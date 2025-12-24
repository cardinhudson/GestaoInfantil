"""db.py
Configuração do SQLite + SQLAlchemy e função para inicializar o DB.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

DB_FILENAME = os.environ.get("GESTAO_DB", "gestaoinfantil.db")
DB_URL = f"sqlite:///{DB_FILENAME}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Logger para depuração de persistência
logger = logging.getLogger(__name__)
try:
    logger.info(f"DB_URL={DB_URL} DB_FILENAME_ABS={os.path.abspath(DB_FILENAME)}")
except Exception:
    pass


from sqlalchemy import text

def init_db():
    """Cria as tabelas se não existirem e aplica migrações simples."""
    from models import User, Task, Conversion, Debit  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # migração simples: adicionar coluna `photo` em users se não existir
    ensure_user_photo_column()
    ensure_user_password_column()


def ensure_user_photo_column():
    """Verifica se a coluna `photo` existe na tabela `users` e a cria se ausente.
    Isso evita erros quando o schema foi atualizado sem migrações formais.
    """
    try:
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(users);"))
            cols = [row["name"] for row in res.mappings()]
            if "photo" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN photo TEXT;"))
    except Exception:
        # Não falhar a inicialização apenas por causa da migração; log opcional
        pass


def ensure_user_password_column():
    """Adiciona coluna password_hash se ausente."""
    try:
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(users);"))
            cols = [row[1] for row in res.fetchall()]
            if "password_hash" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash TEXT;"))
    except Exception:
        pass


def get_session():
    logger.debug(f"Abrindo sessão DB para {DB_URL}")
    return SessionLocal()
