
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

print('Desabilitando foreign_keys temporariamente...')
c.execute('PRAGMA foreign_keys=OFF')

print('Renomeando tabela users antiga...')
c.execute('ALTER TABLE users RENAME TO users_old')

print('Criando nova tabela users com UNIQUE e CHECK...')
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    roles TEXT NOT NULL DEFAULT 'child' CHECK (roles IN ('child', 'validator', 'admin')),
    password_hash TEXT,
    photo TEXT
)''')

print('Migrando dados...')
c.execute('INSERT OR IGNORE INTO users (id, name, email, roles, password_hash, photo) SELECT id, name, email, roles, password_hash, photo FROM users_old')

print('Recriando índices...')
c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)')

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
