"""
Script de upgrade do SQLite - IDEMPOTENTE
Pode ser executado múltiplas vezes sem causar erros.
"""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import _resolve_sqlite_path, DB_TARGET
import os

# Força uso do arquivo local se DB_TARGET não for SQLite
if not DB_TARGET or DB_TARGET.startswith('postgres'):
    target = 'gestaoinfantil.db'
else:
    target = DB_TARGET
sqlite_path = _resolve_sqlite_path(target)
print(f"Usando banco: {sqlite_path}")

conn = sqlite3.connect(sqlite_path)
c = conn.cursor()

def table_exists(table_name):
    """Verifica se uma tabela existe no banco."""
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return c.fetchone() is not None

print('Desabilitando foreign_keys temporariamente...')
c.execute('PRAGMA foreign_keys=OFF')

# Renomeia tabela users para users_old apenas se users existe e users_old não existe
if table_exists('users') and not table_exists('users_old'):
    print('Renomeando tabela users antiga...')
    c.execute('ALTER TABLE users RENAME TO users_old')

# Cria tabela users apenas se não existir
if not table_exists('users'):
    print('Criando nova tabela users com UNIQUE e CHECK...')
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        roles TEXT NOT NULL DEFAULT 'child' CHECK (roles IN ('child', 'validator', 'admin')),
        password_hash TEXT,
        photo TEXT
    )''')

# Migra dados apenas se users_old existir
if table_exists('users_old'):
    print('Migrando dados...')
    c.execute('INSERT OR IGNORE INTO users (id, name, email, roles, password_hash, photo) SELECT id, name, email, roles, password_hash, photo FROM users_old')

print('Recriando índices...')
c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)')

# Remove tabela users_old apenas se existir
if table_exists('users_old'):
    print('Removendo tabela antiga...')
    c.execute('DROP TABLE users_old')

print('Reabilitando foreign_keys...')
c.execute('PRAGMA foreign_keys=ON')

print('Criando índices extras...')
c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_child_id ON tasks (child_id)')
c.execute('CREATE INDEX IF NOT EXISTS idx_debits_user_id ON debits (user_id)')

conn.commit()

print('Estrutura final:')
for row in c.execute('PRAGMA table_info(users)'):
    print(row)
for row in c.execute('PRAGMA index_list(users)'):
    print(row)

conn.close()
print('Upgrade seguro aplicado ao SQLite com sucesso!')
