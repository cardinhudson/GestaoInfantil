"""Serviços (CRUD) e lógica do domínio."""
from db import get_session, init_db
from models import User, Task, Conversion, Debit
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


def ensure_conversion_exists(db: Session):
    conv = db.query(Conversion).first()
    if not conv:
        conv = Conversion(money_per_point=0.5, hours_per_point=0.1)
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode()).hexdigest()


def create_user(name: str, email: str = None, roles: str = "child", password: str = None) -> User:
    db = get_session()
    usr = User(name=name, email=email, roles=roles, password_hash=hash_password(password) if password else None)
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


def update_user_password(user_id: int, new_password: str):
    """Atualiza a senha (armazenando hash) para o usuário informado."""
    db = get_session()
    usr = db.query(User).get(user_id)
    if not usr:
        db.close()
        return None
    usr.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(usr)
    db.close()
    try:
        logger.info(f"Senha atualizada para user_id={user_id}")
    except Exception:
        pass
    return usr


def get_user_by_email(email: str):
    db = get_session()
    usr = db.query(User).filter(func.lower(User.email) == (email or '').lower()).first()
    db.close()
    return usr


def delete_user(user_id: int):
    """Remove usuário e registros relacionados (tarefas e débitos) do banco.
    Retorna True se usuário existia e foi removido, False caso contrário.
    """
    db = get_session()
    try:
        # Remover tarefas relacionadas (child, submitted_by, validator)
        db.query(Task).filter(
            (Task.child_id == user_id) | (Task.submitted_by_id == user_id) | (Task.validator_id == user_id)
        ).delete(synchronize_session=False)

        # Remover débitos relacionados (user alvo ou quem executou)
        db.query(Debit).filter((Debit.user_id == user_id) | (Debit.performed_by_id == user_id)).delete(synchronize_session=False)

        usr = db.query(User).get(user_id)
        if not usr:
            db.close()
            return False
        db.delete(usr)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def authenticate_user(email: str, password: str):
    usr = get_user_by_email(email)
    if not usr or not usr.password_hash:
        return None
    if usr.password_hash == hash_password(password):
        return usr
    return None


def create_task(name: str, amount: float, conversion_type: str, child_id: int, submitted_by_id: int, validator_id: int = None):
    db = get_session()
    task = Task(name=name, points=float(amount), conversion_type=conversion_type, child_id=child_id,
                submitted_by_id=submitted_by_id, validator_id=validator_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    try:
        logger.info(f"Tarefa criada: id={task.id} nome={task.name} child={child_id} valor={task.points} tipo={conversion_type}")
    except Exception:
        pass
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
        try:
            logger.info(f"Tarefa validada: id={task.id} por={validator_id}")
        except Exception:
            pass
        # Notificação por e-mail desabilitada por configuração (evitar falhas em deploys sem SMTP).
        logger.debug("Envio de e-mail desabilitado: notificação de validação não será enviada.")
    db.close()
    return task


def get_conversion():
    # Conversões deixam de ser usadas diretamente; mantido para compatibilidade futura
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


def list_debits(user_id: int = None):
    db = get_session()
    q = db.query(Debit)
    if user_id is not None:
        q = q.filter(Debit.user_id == user_id)
    res = q.order_by(Debit.created_at.desc()).all()
    db.close()
    return res


def get_report():
    """Saldo por usuário (dinheiro e horas) usando tasks validadas e débitos registrados."""
    db = get_session()

    # Tarefas validadas: dinheiro
    money_q = db.query(Task.child_id, func.sum(Task.points).label('money')).filter(
        Task.validated == True, Task.conversion_type == 'money').group_by(Task.child_id).subquery()
    # Tarefas validadas: horas
    hours_q = db.query(Task.child_id, func.sum(Task.points).label('hours')).filter(
        Task.validated == True, Task.conversion_type == 'hours').group_by(Task.child_id).subquery()

    # Débitos
    debit_money_q = db.query(Debit.user_id, func.sum(Debit.money_amount).label('deb_money')).group_by(Debit.user_id).subquery()
    debit_hours_q = db.query(Debit.user_id, func.sum(Debit.hours_amount).label('deb_hours')).group_by(Debit.user_id).subquery()

    users = db.query(User).all()
    report = []
    for u in users:
        money_earn = db.query(money_q.c.money).filter(money_q.c.child_id == u.id).scalar() or 0.0
        hours_earn = db.query(hours_q.c.hours).filter(hours_q.c.child_id == u.id).scalar() or 0.0
        money_deb = db.query(debit_money_q.c.deb_money).filter(debit_money_q.c.user_id == u.id).scalar() or 0.0
        hours_deb = db.query(debit_hours_q.c.deb_hours).filter(debit_hours_q.c.user_id == u.id).scalar() or 0.0
        balance_money = round((money_earn - (money_deb or 0)), 2)
        balance_hours = round((hours_earn - (hours_deb or 0)), 2)
        report.append({
            'user': u,
            'money': float(balance_money),
            'hours': float(balance_hours),
            'earned_money': float(money_earn),
            'earned_hours': float(hours_earn),
            'debited_money': float(money_deb or 0),
            'debited_hours': float(hours_deb or 0),
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
        # Seed minimal: dois children e um validador (senha padrão 123)
        db.add_all([
            User(name='Validador', email='admin@example.com', roles='validator', password_hash=hash_password('123')),
            User(name='Joao', email='joao@example.com', roles='child', password_hash=hash_password('123')),
            User(name='Ana', email='ana@example.com', roles='child', password_hash=hash_password('123')),
        ])
        db.commit()
    # Garantir que usuários existentes tenham senha padrão (somente em ambientes de desenvolvimento)
    users_no_pwd = db.query(User).filter((User.password_hash == None) | (User.password_hash == '')).all()
    for u in users_no_pwd:
        u.password_hash = hash_password('123')
    if users_no_pwd:
        db.commit()

    ensure_conversion_exists(db)
    ensure_uploads_dir()
    db.close()

    # Garantir que exista um administrador com e-mail conhecido para desenvolvimento
    try:
        if not get_user_by_email('admin@example.com'):
            create_user(name='Administrador', email='admin@example.com', roles='validator', password='123')
    except Exception:
        pass
