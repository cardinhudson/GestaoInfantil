
from typing import Optional
import requests

# Configurações do Supabase Storage

# Configurações do Supabase Storage
SUPABASE_URL = "https://qusavydxnnctnrqfwoua.supabase.co"
SUPABASE_BUCKET = "user-photos"
# Use a service_role para upload seguro (NUNCA exponha no frontend)
SUPABASE_KEY = "HudsonCardin1211"

def upload_photo_supabase(user_id: int, file_bytes: bytes, original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1].lower() or ".jpg"
    fname = _safe_filename(f"user_{user_id}_{int(time.time())}{ext}")
    path = f"users/{fname}"
    # Upload do arquivo
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{path}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/octet-stream"
    }
    headers["x-upsert"] = "true"
    try:
        resp = requests.put(url, headers=headers, data=file_bytes)
        if not resp.ok:
            print(f"[Supabase Upload] Erro HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    except Exception as e:
        print(f"[Supabase Upload] Falha ao enviar foto: {e}")
        print(f"URL: {url}")
        print(f"Headers: {{'Authorization': 'Bearer ...', 'Content-Type': 'application/octet-stream', 'x-upsert': 'true'}}")
        print(f"Tamanho do arquivo: {len(file_bytes)} bytes")
        raise
    # Gera URL pública
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"
    return public_url
def get_user_by_id(user_id: int) -> "Optional[User]":
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            cur.close()
        else:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            cur.close()
        return _row_to_user(row)
    finally:
        conn.close()
def update_user_full(user_id: int, name: str, email: str, roles: str, password: str = None) -> "Optional[User]":
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            if password:
                cur.execute("UPDATE users SET name = %s, email = %s, roles = %s, password_hash = %s WHERE id = %s",
                            (name, email, roles, hash_password(password), user_id))
            else:
                cur.execute("UPDATE users SET name = %s, email = %s, roles = %s WHERE id = %s",
                            (name, email, roles, user_id))
            conn.commit()
            cur.close()
        else:
            cur = conn.cursor()
            if password:
                cur.execute("UPDATE users SET name = ?, email = ?, roles = ?, password_hash = ? WHERE id = ?",
                            (name, email, roles, hash_password(password), user_id))
            else:
                cur.execute("UPDATE users SET name = ?, email = ?, roles = ? WHERE id = ?",
                            (name, email, roles, user_id))
            conn.commit()
            cur.close()
        # Retorna o usuário atualizado
        return get_user_by_id(user_id)
    finally:
        conn.close()
def delete_debit(debit_id: int) -> bool:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("DELETE FROM debits WHERE id = %s", (debit_id,))
            deleted = cur.rowcount > 0
            cur.close()
            conn.commit()
            return deleted
        else:
            cursor = conn.execute("DELETE FROM debits WHERE id = ?", (debit_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()
def delete_task(task_id: int) -> bool:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            deleted = cur.rowcount > 0
            cur.close()
            conn.commit()
            return deleted
        else:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
    finally:
        conn.close()
"""Serviços (CRUD) e lógica do domínio utilizando sqlite3 explicitamente."""
import hashlib
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from models import User

from db import DB_KIND, get_connection
from models import Conversion, Debit, Task, User

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode()).hexdigest()


def _row_to_user(row) -> Optional[User]:
    if not row:
        return None
    return User(
        id=row["id"],
        name=row["name"],
        email=row["email"],
        roles=row["roles"],
        password_hash=row["password_hash"],
        photo=row["photo"],
    )


def _row_to_task(row) -> Optional[Task]:
    if not row:
        return None
    return Task(
        id=row["id"],
        name=row["name"],
        points=float(row["points"]),
        conversion_type=row["conversion_type"],
        child_id=row["child_id"],
        submitted_by_id=row["submitted_by_id"],
        validator_id=row["validator_id"],
        validated=bool(row["validated"]),
        created_at=row["created_at"],
        validated_at=row["validated_at"],
    )


def _row_to_debit(row) -> Optional[Debit]:
    if not row:
        return None
    return Debit(
        id=row["id"],
        user_id=row["user_id"],
        points_deducted=row["points_deducted"],
        money_amount=row["money_amount"],
        hours_amount=row["hours_amount"],
        reason=row["reason"],
        performed_by_id=row["performed_by_id"],
        created_at=row["created_at"],
    )


def _row_to_conversion(row) -> Optional[Conversion]:
    if not row:
        return None
    return Conversion(
        id=row["id"],
        money_per_point=float(row["money_per_point"]),
        hours_per_point=float(row["hours_per_point"]),
    )


def create_user(name: str, email: str = None, roles: str = "child", password: str = None) -> User:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (name, email, roles, password_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, email, roles, hash_password(password) if password else None),
            )
            row_id = cur.fetchone()
            user_id = row_id.get("id") if isinstance(row_id, dict) else row_id[0]
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            fetched = cur.fetchone()
            cur.close()
            conn.commit()
            return _row_to_user(fetched)
        cursor = conn.execute(
            "INSERT INTO users (name, email, roles, password_hash) VALUES (?, ?, ?, ?)",
            (name, email, roles, hash_password(password) if password else None),
        )
        conn.commit()
        user_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def list_users() -> List[User]:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("SELECT * FROM users ORDER BY id")
            rows = cur.fetchall()
            cur.close()
        else:
            rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [_row_to_user(row) for row in rows]
    finally:
        conn.close()


def update_user_email(user_id: int, new_email: str) -> Optional[User]:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, user_id))
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.commit()
            return _row_to_user(row)
        conn.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def update_user_password(user_id: int, new_password: str) -> Optional[User]:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(new_password), user_id))
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            cur.close()
            conn.commit()
            if row:
                logger.info("Senha atualizada para user_id=%s", user_id)
            return _row_to_user(row)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            logger.info("Senha atualizada para user_id=%s", user_id)
        return _row_to_user(row)
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[User]:
    if not email:
        return None
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            row = cur.fetchone()
            cur.close()
            return _row_to_user(row)
        row = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
        return _row_to_user(row)
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM tasks WHERE child_id = %s OR submitted_by_id = %s OR validator_id = %s",
                (user_id, user_id, user_id),
            )
            cur.execute(
                "DELETE FROM debits WHERE user_id = %s OR performed_by_id = %s",
                (user_id, user_id),
            )
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            deleted = cur.rowcount > 0
            cur.close()
            conn.commit()
            return deleted
        conn.execute(
            "DELETE FROM tasks WHERE child_id = ? OR submitted_by_id = ? OR validator_id = ?",
            (user_id, user_id, user_id),
        )
        conn.execute(
            "DELETE FROM debits WHERE user_id = ? OR performed_by_id = ?",
            (user_id, user_id),
        )
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[User]:
    usr = get_user_by_email(email)
    if not usr or not usr.password_hash:
        return None
    if usr.password_hash == hash_password(password):
        return usr
    return None


def create_task(name: str, amount: float, conversion_type: str, child_id: int, submitted_by_id: int, validator_id: int = None) -> Task:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tasks (name, points, conversion_type, child_id, submitted_by_id, validator_id, validated)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (name, float(amount), conversion_type, child_id, submitted_by_id, validator_id, False),
            )
            row_id = cur.fetchone()
            task_id = row_id.get("id") if isinstance(row_id, dict) else row_id[0]
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            cur.close()
        else:
            cursor = conn.execute(
                """
                INSERT INTO tasks (name, points, conversion_type, child_id, submitted_by_id, validator_id, validated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, float(amount), conversion_type, child_id, submitted_by_id, validator_id, 0),
            )
            conn.commit()
            task_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = _row_to_task(row)
        if task:
            logger.info(
                "Tarefa criada id=%s nome=%s child=%s valor=%s tipo=%s",
                task.id,
                task.name,
                child_id,
                task.points,
                conversion_type,
            )
        if DB_KIND == "pg":
            conn.commit()
        return task
    finally:
        conn.close()


def list_tasks(validated: bool = None) -> List[Task]:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            if validated is None:
                cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            else:
                cur.execute("SELECT * FROM tasks WHERE validated = %s ORDER BY created_at DESC", (validated,))
            rows = cur.fetchall()
            cur.close()
        else:
            if validated is None:
                rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE validated = ? ORDER BY created_at DESC",
                    (1 if validated else 0,),
                ).fetchall()
        return [_row_to_task(row) for row in rows]
    finally:
        conn.close()


def validate_task(task_id: int, validator_id: int) -> Optional[Task]:
    conn = get_connection()
    try:
        now = datetime.utcnow()
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                "UPDATE tasks SET validated = TRUE, validator_id = %s, validated_at = %s WHERE id = %s",
                (validator_id, now, task_id),
            )
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            cur.close()
        else:
            conn.execute(
                "UPDATE tasks SET validated = 1, validator_id = ?, validated_at = ? WHERE id = ?",
                (validator_id, now.isoformat(), task_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = _row_to_task(row)
        if task:
            logger.info("Tarefa validada id=%s por=%s", task.id, validator_id)
        if DB_KIND == "pg":
            conn.commit()
        return task
    finally:
        conn.close()


def ensure_conversion_exists(conn) -> Conversion:
    if DB_KIND == "pg":
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversions LIMIT 1")
        row = cur.fetchone()
        if row:
            cur.close()
            return _row_to_conversion(row)
        cur.execute("INSERT INTO conversions (money_per_point, hours_per_point) VALUES (%s, %s) RETURNING id", (0.5, 0.1))
        conn.commit()
        cur.execute("SELECT * FROM conversions LIMIT 1")
        row = cur.fetchone()
        cur.close()
        return _row_to_conversion(row)
    row = conn.execute("SELECT * FROM conversions LIMIT 1").fetchone()
    if row:
        return _row_to_conversion(row)
    conn.execute("INSERT INTO conversions (money_per_point, hours_per_point) VALUES (?, ?)", (0.5, 0.1))
    conn.commit()
    row = conn.execute("SELECT * FROM conversions LIMIT 1").fetchone()
    return _row_to_conversion(row)


def get_conversion() -> Conversion:
    conn = get_connection()
    try:
        return ensure_conversion_exists(conn)
    finally:
        conn.close()


def set_conversion(money_per_point: float, hours_per_point: float) -> Conversion:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("SELECT id FROM conversions LIMIT 1")
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE conversions SET money_per_point = %s, hours_per_point = %s WHERE id = %s",
                    (money_per_point, hours_per_point, row["id"]),
                )
            else:
                cur.execute(
                    "INSERT INTO conversions (money_per_point, hours_per_point) VALUES (%s, %s)",
                    (money_per_point, hours_per_point),
                )
            cur.close()
            conn.commit()
            return ensure_conversion_exists(conn)
        row = conn.execute("SELECT id FROM conversions LIMIT 1").fetchone()
        if row:
            conn.execute(
                "UPDATE conversions SET money_per_point = ?, hours_per_point = ? WHERE id = ?",
                (money_per_point, hours_per_point, row["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO conversions (money_per_point, hours_per_point) VALUES (?, ?)",
                (money_per_point, hours_per_point),
            )
        conn.commit()
        return ensure_conversion_exists(conn)
    finally:
        conn.close()


def create_debit(
    user_id: int,
    points: int,
    money: float = None,
    hours: float = None,
    reason: str = None,
    performed_by_id: int = None,
) -> Debit:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO debits (user_id, points_deducted, money_amount, hours_amount, reason, performed_by_id)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                """,
                (user_id, points or 0, money, hours, reason, performed_by_id),
            )
            row_id = cur.fetchone()
            debit_id = row_id.get("id") if isinstance(row_id, dict) else row_id[0]
            cur.execute("SELECT * FROM debits WHERE id = %s", (debit_id,))
            row = cur.fetchone()
            cur.close()
            conn.commit()
            return _row_to_debit(row)
        cursor = conn.execute(
            """
            INSERT INTO debits (user_id, points_deducted, money_amount, hours_amount, reason, performed_by_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, points or 0, money, hours, reason, performed_by_id),
        )
        conn.commit()
        debit_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM debits WHERE id = ?", (debit_id,)).fetchone()
        return _row_to_debit(row)
    finally:
        conn.close()


def list_debits(user_id: int = None) -> List[Debit]:
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            if user_id is None:
                cur.execute("SELECT * FROM debits ORDER BY created_at DESC")
            else:
                cur.execute("SELECT * FROM debits WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            rows = cur.fetchall()
            cur.close()
        else:
            if user_id is None:
                rows = conn.execute("SELECT * FROM debits ORDER BY created_at DESC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM debits WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
        return [_row_to_debit(row) for row in rows]
    finally:
        conn.close()


def get_report() -> List[Dict[str, float]]:
    conn = get_connection()
    try:
        users = list_users()
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute(
                "SELECT child_id, SUM(points) AS total FROM tasks WHERE validated = TRUE AND conversion_type = 'money' GROUP BY child_id"
            )
            money_rows = cur.fetchall()
            cur.execute(
                "SELECT child_id, SUM(points) AS total FROM tasks WHERE validated = TRUE AND conversion_type = 'hours' GROUP BY child_id"
            )
            hours_rows = cur.fetchall()
            cur.execute("SELECT user_id, SUM(money_amount) AS total FROM debits GROUP BY user_id")
            deb_money_rows = cur.fetchall()
            cur.execute("SELECT user_id, SUM(hours_amount) AS total FROM debits GROUP BY user_id")
            deb_hours_rows = cur.fetchall()
            cur.close()
        else:
            money_rows = conn.execute(
                "SELECT child_id, SUM(points) AS total FROM tasks WHERE validated = 1 AND conversion_type = 'money' GROUP BY child_id"
            ).fetchall()
            hours_rows = conn.execute(
                "SELECT child_id, SUM(points) AS total FROM tasks WHERE validated = 1 AND conversion_type = 'hours' GROUP BY child_id"
            ).fetchall()
            deb_money_rows = conn.execute(
                "SELECT user_id, SUM(money_amount) AS total FROM debits GROUP BY user_id"
            ).fetchall()
            deb_hours_rows = conn.execute(
                "SELECT user_id, SUM(hours_amount) AS total FROM debits GROUP BY user_id"
            ).fetchall()

        money_map = {row["child_id"]: float(row["total"] or 0) for row in money_rows}
        hours_map = {row["child_id"]: float(row["total"] or 0) for row in hours_rows}
        deb_money_map = {row["user_id"]: float(row["total"] or 0) for row in deb_money_rows}
        deb_hours_map = {row["user_id"]: float(row["total"] or 0) for row in deb_hours_rows}

        report = []
        for user in users:
            earned_money = money_map.get(user.id, 0.0)
            earned_hours = hours_map.get(user.id, 0.0)
            deb_money = deb_money_map.get(user.id, 0.0)
            deb_hours = deb_hours_map.get(user.id, 0.0)
            report.append(
                {
                    "user": user,
                    "money": round(earned_money - deb_money, 2),
                    "hours": round(earned_hours - deb_hours, 2),
                    "earned_money": earned_money,
                    "earned_hours": earned_hours,
                    "debited_money": deb_money,
                    "debited_hours": deb_hours,
                }
            )
        return report
    finally:
        conn.close()


UPLOADS_DIR = os.environ.get("GESTAO_UPLOADS", "uploads")


def ensure_uploads_dir():
    path = os.path.join(UPLOADS_DIR, "users")
    os.makedirs(path, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).replace(" ", "_")


def save_user_photo(user_id: int, file_bytes: bytes, original_filename: str) -> str:
    # Salva no Supabase Storage e obtém URL pública
    url = upload_photo_supabase(user_id, file_bytes, original_filename)
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("UPDATE users SET photo = %s WHERE id = %s", (url, user_id))
            conn.commit()
            cur.close()
        else:
            cur = conn.cursor()
            cur.execute("UPDATE users SET photo = ? WHERE id = ?", (url, user_id))
            conn.commit()
            cur.close()
    finally:
        conn.close()
    return url


def seed_sample_data():
    conn = get_connection()
    try:
        if DB_KIND == "pg":
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) FROM users")
            row = cur.fetchone()
            count = list(row.values())[0] if isinstance(row, dict) else row[0]
            if count == 0:
                logger.info("Inserindo usuários de exemplo")
                cur.executemany(
                    "INSERT INTO users (name, email, roles, password_hash) VALUES (%s, %s, %s, %s)",
                    [
                        ("Validador", "admin@example.com", "validator", hash_password("123")),
                        ("Joao", "joao@example.com", "child", hash_password("123")),
                        ("Ana", "ana@example.com", "child", hash_password("123")),
                    ],
                )
            cur.execute("SELECT id FROM users WHERE password_hash IS NULL OR password_hash = ''")
            users_no_pwd = cur.fetchall()
            for row in users_no_pwd:
                user_id = row.get("id") if isinstance(row, dict) else row[0]
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (hash_password("123"), user_id),
                )
            cur.close()
            conn.commit()
            ensure_conversion_exists(conn)
        else:
            count = conn.execute("SELECT COUNT(1) FROM users").fetchone()[0]
            if count == 0:
                logger.info("Inserindo usuários de exemplo")
                conn.executemany(
                    "INSERT INTO users (name, email, roles, password_hash) VALUES (?, ?, ?, ?)",
                    [
                        ("Validador", "admin@example.com", "validator", hash_password("123")),
                        ("Joao", "joao@example.com", "child", hash_password("123")),
                        ("Ana", "ana@example.com", "child", hash_password("123")),
                    ],
                )
            conn.commit()

            users_no_pwd = conn.execute(
                "SELECT id FROM users WHERE password_hash IS NULL OR password_hash = ''"
            ).fetchall()
            for row in users_no_pwd:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password("123"), row["id"]),
                )
            if users_no_pwd:
                conn.commit()

            ensure_conversion_exists(conn)
    finally:
        conn.close()

    ensure_uploads_dir()

    try:
        if not get_user_by_email("admin@example.com"):
            create_user(name="Administrador", email="admin@example.com", roles="validator", password="123")
    except Exception:
        pass
