"""Serviços (CRUD) e lógica do domínio."""
from db import get_session, init_db
from models import User, Task, Conversion, Debit
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime


def ensure_conversion_exists(db: Session):
    conv = db.query(Conversion).first()
    if not conv:
        conv = Conversion(money_per_point=0.5, hours_per_point=0.1)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def create_user(name: str, email: str = None, roles: str = "child") -> User:
    db = get_session()
    usr = User(name=name, email=email, roles=roles)
    db.add(usr)
    db.commit()
    db.refresh(usr)
    db.close()
    return usr


def list_users():
    db = get_session()
    users = db.query(User).all()
    db.close()
    return users


def update_user_email(user_id: int, new_email: str):
    db = get_session()
    usr = db.query(User).get(user_id)
    if usr:
        usr.email = new_email
        db.commit()
        db.refresh(usr)
    db.close()
    return usr


def create_task(name: str, points: int, conversion_type: str, child_id: int, submitted_by_id: int, validator_id: int = None):
    db = get_session()
    task = Task(name=name, points=points, conversion_type=conversion_type, child_id=child_id,
                submitted_by_id=submitted_by_id, validator_id=validator_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    db.close()
    return task


def list_tasks(validated: bool = None):
    db = get_session()
    q = db.query(Task)
    if validated is not None:
        q = q.filter(Task.validated == validated)
    tasks = q.all()
    db.close()
    return tasks


def validate_task(task_id: int, validator_id: int):
    db = get_session()
    task = db.query(Task).get(task_id)
    if task and not task.validated:
        task.validated = True
        task.validator_id = validator_id
        task.validated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    db.close()
    return task


def get_conversion():
    db = get_session()
    conv = ensure_conversion_exists(db)
    db.close()
    return conv


def set_conversion(money_per_point: float, hours_per_point: float):
    db = get_session()
    conv = ensure_conversion_exists(db)
    conv.money_per_point = money_per_point
    conv.hours_per_point = hours_per_point
    db.commit()
    db.refresh(conv)
    db.close()
    return conv


def create_debit(user_id: int, points: int, money: float = None, hours: float = None, reason: str = None, performed_by_id: int = None):
    db = get_session()
    debit = Debit(user_id=user_id, points_deducted=points, money_amount=money, hours_amount=hours, reason=reason, performed_by_id=performed_by_id)
    db.add(debit)
    db.commit()
    db.refresh(debit)
    db.close()
    return debit


def get_report():
    db = get_session()
    conv = ensure_conversion_exists(db)

    # Pontos validados por criança
    subq = db.query(Task.child_id, func.sum(Task.points).label('points')).filter(Task.validated == True).group_by(Task.child_id).subquery()

    # Débitos por usuário (points)
    debq = db.query(Debit.user_id, func.sum(Debit.points_deducted).label('points_deducted')).group_by(Debit.user_id).subquery()

    users = db.query(User).all()

    report = []
    for u in users:
        pts = db.query(subq.c.points).filter(subq.c.child_id == u.id).scalar() or 0
        ded = db.query(debq.c.points_deducted).filter(debq.c.user_id == u.id).scalar() or 0
        balance_points = pts - ded
        money = balance_points * conv.money_per_point
        hours = balance_points * conv.hours_per_point
        report.append({
            'user': u,
            'points': int(pts),
            'deducted': int(ded),
            'balance_points': int(balance_points),
            'money': round(money, 2),
            'hours': round(hours, 2)
        })

    db.close()
    return report


import os
import time

UPLOADS_DIR = os.environ.get('GESTAO_UPLOADS', 'uploads')


def ensure_uploads_dir():
    path = os.path.join(UPLOADS_DIR, 'users')
    os.makedirs(path, exist_ok=True)
    return path


def _safe_filename(name: str) -> str:
    # simples sanitização para nomes de arquivos
    return ''.join(c for c in name if c.isalnum() or c in (' ','.','_','-')).replace(' ','_')


def save_user_photo(user_id: int, file_bytes: bytes, original_filename: str) -> str:
    """Salva o arquivo em uploads/users e atualiza o campo `photo` do usuário.
    Retorna o caminho relativo salvo.
    """
    ensure_uploads_dir()
    ts = int(time.time())
    ext = os.path.splitext(original_filename)[1].lower() or '.jpg'
    fname = f"user_{user_id}_{ts}{ext}"
    fname = _safe_filename(fname)
    path = os.path.join(UPLOADS_DIR, 'users', fname)

    with open(path, 'wb') as f:
        f.write(file_bytes)

    db = get_session()
    usr = db.query(User).get(user_id)
    if usr:
        usr.photo = path
        db.commit()
        db.refresh(usr)
    db.close()
    return path


def seed_sample_data():
    db = get_session()
    if db.query(User).count() == 0:
        # Exemplo: 2 pais, 2 crianças, 1 tia com permissão
        db.add_all([
            User(name='Mãe', email='mae@example.com', roles='parent,validator'),
            User(name='Pai', email='pai@example.com', roles='parent,validator'),
            User(name='João', email='joao@example.com', roles='child'),
            User(name='Ana', email='ana@example.com', roles='child'),
            User(name='Tia', email='tia@example.com', roles='validator')
        ])
        db.commit()
    ensure_conversion_exists(db)
    ensure_uploads_dir()
    db.close()
