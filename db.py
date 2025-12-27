"""Database helpers supporting SQLite (local) and Postgres (cloud persistence).

If GESTAO_DB / DATABASE_URL starts with postgres, we connect to Postgres using
psycopg2. Otherwise we default to a local SQLite file. Both backends expose the
same get_connection() API and init_db() creates the required tables.
"""
import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)



def _get_db_target_from_env() -> Optional[str]:
    # Força uso do Postgres/Supabase. Não permite fallback para SQLite.
    target = os.environ.get("GESTAO_DB") or os.environ.get("DATABASE_URL")
    if target:
        logger.info(f"DB target found in environment variables")
        return target
    try:
        import streamlit as _st  # type: ignore
        secrets = getattr(_st, "secrets", None)
        if secrets is not None:
            # Streamlit Cloud: secrets é um objeto SecretsMapping, não dict
            try:
                if "GESTAO_DB" in secrets:
                    logger.info("DB target found in st.secrets (GESTAO_DB)")
                    return secrets["GESTAO_DB"]
                if "DATABASE_URL" in secrets:
                    logger.info("DB target found in st.secrets (DATABASE_URL)")
                    return secrets["DATABASE_URL"]
            except Exception as e:
                logger.warning(f"Erro ao ler secrets: {e}")
    except Exception as e:
        logger.warning(f"Não foi possível importar/ler st.secrets: {e}")
    # Se não encontrar, retorna None (tratado depois)
    logger.error("Nenhuma configuração de banco encontrada!")
    return None


def _resolve_sqlite_path(target: Optional[str]) -> Path:
    name = target or "gestaoinfantil.db"
    if name.startswith("sqlite://"):
        name = name.replace("sqlite://", "", 1).lstrip("/")
    path = Path(name)
    if not path.is_absolute():
        path = Path(os.getcwd()).joinpath(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()


# Variáveis globais - inicializadas de forma lazy
_DB_TARGET = None
_DB_KIND = None
_DB_PATH = None
_initialized = False


def _ensure_initialized():
    global _DB_TARGET, _DB_KIND, _DB_PATH, _initialized
    if _initialized:
        return
    _DB_TARGET = _get_db_target_from_env()
    if not _DB_TARGET:
        # Mostra erro amigável no Streamlit se possível
        try:
            import streamlit as st
            st.error("❌ **Erro de Configuração do Banco de Dados**")
            st.warning("""
            Nenhuma configuração de banco Postgres/Supabase encontrada!
            
            **Configure GESTAO_DB nas Secrets do Streamlit Cloud:**
            1. Vá em Manage App → Settings → Secrets
            2. Adicione: `GESTAO_DB = "postgresql://usuario:senha@host:porta/database"`
            3. Salve e reinicie o app
            """)
            st.stop()
        except Exception:
            pass
        raise RuntimeError("[ERRO] Configure GESTAO_DB ou DATABASE_URL nas secrets/ambiente.")
    if not _DB_TARGET.startswith("postgres"):
        raise RuntimeError("[ERRO] O sistema exige banco Postgres/Supabase. String de conexão inválida.")
    _DB_KIND = "pg"
    _DB_PATH = None
    _initialized = True
    logger.info("Using Postgres database via GESTAO_DB/DATABASE_URL")


# Propriedades para acesso às variáveis (compatibilidade)
@property
def DB_TARGET():
    _ensure_initialized()
    return _DB_TARGET


@property
def DB_KIND():
    _ensure_initialized()
    return _DB_KIND


# Para compatibilidade com código existente que importa DB_TARGET e DB_KIND
def _get_db_target():
    _ensure_initialized()
    return _DB_TARGET


def _get_db_kind():
    _ensure_initialized()
    return _DB_KIND


# Alias para compatibilidade
DB_TARGET = None  # Será inicializado na primeira chamada a get_connection()
DB_KIND = "pg"  # Assume Postgres por padrão
DB_PATH = None


def get_connection():
    _ensure_initialized()
    # Apenas Postgres/Supabase
    try:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(_DB_TARGET, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    except Exception:
        logger.info("psycopg2 not available, trying pg8000 fallback")
        try:
            import pg8000
            from urllib.parse import urlparse
            parsed = urlparse(_DB_TARGET)
            user = parsed.username
            password = parsed.password
            host = parsed.hostname or "localhost"
            port = int(parsed.port) if parsed.port else 5432
            dbname = parsed.path.lstrip("/") or "postgres"
            raw_conn = pg8000.connect(user=user, host=host, port=port, database=dbname, password=password)
            return raw_conn
        except Exception:
            raise RuntimeError("Postgres driver not installed. Install psycopg2-binary ou pg8000.")

def init_db():
    _ensure_initialized()
    conn = get_connection()
    try:
        if _DB_KIND == "sqlite":
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    roles TEXT NOT NULL DEFAULT 'child',
                    password_hash TEXT,
                    photo TEXT
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    points REAL NOT NULL,
                    conversion_type TEXT NOT NULL,
                    child_id INTEGER NOT NULL,
                    submitted_by_id INTEGER,
                    validator_id INTEGER,
                    validated INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    validated_at TEXT,
                    FOREIGN KEY(child_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(submitted_by_id) REFERENCES users(id),
                    FOREIGN KEY(validator_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS conversions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    money_per_point REAL NOT NULL DEFAULT 0.5,
                    hours_per_point REAL NOT NULL DEFAULT 0.1
                );

                CREATE TABLE IF NOT EXISTS debits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    points_deducted INTEGER NOT NULL DEFAULT 0,
                    money_amount REAL,
                    hours_amount REAL,
                    reason TEXT,
                    performed_by_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(performed_by_id) REFERENCES users(id)
                );
                """
            )
        else:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    roles TEXT NOT NULL DEFAULT 'child',
                    password_hash TEXT,
                    photo TEXT
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    points DOUBLE PRECISION NOT NULL,
                    conversion_type TEXT NOT NULL,
                    child_id INTEGER NOT NULL,
                    submitted_by_id INTEGER,
                    validator_id INTEGER,
                    validated BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    validated_at TIMESTAMP WITH TIME ZONE,
                    CONSTRAINT fk_child FOREIGN KEY(child_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_submitted FOREIGN KEY(submitted_by_id) REFERENCES users(id),
                    CONSTRAINT fk_validator FOREIGN KEY(validator_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS conversions (
                    id SERIAL PRIMARY KEY,
                    money_per_point DOUBLE PRECISION NOT NULL DEFAULT 0.5,
                    hours_per_point DOUBLE PRECISION NOT NULL DEFAULT 0.1
                );

                CREATE TABLE IF NOT EXISTS debits (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    points_deducted INTEGER NOT NULL DEFAULT 0,
                    money_amount DOUBLE PRECISION,
                    hours_amount DOUBLE PRECISION,
                    reason TEXT,
                    performed_by_id INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_performed FOREIGN KEY(performed_by_id) REFERENCES users(id)
                );
                """
            )
            cur.close()
        conn.commit()
    finally:
        conn.close()
