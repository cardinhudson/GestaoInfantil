
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from db import _resolve_sqlite_path, DB_TARGET

# Use o caminho do banco local
import os
# Força uso do arquivo local se DB_TARGET não for SQLite
target = DB_TARGET
if not target or target.startswith('postgres'):
    target = 'gestaoinfantil.db'
sqlite_path = _resolve_sqlite_path(target)
print(f"Usando banco: {sqlite_path}")

conn = sqlite3.connect(sqlite_path)
c = conn.cursor()

# Índice e UNIQUE para email
c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)")

# Índice para child_id em tasks
c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_child_id ON tasks (child_id)")

# Índice para user_id em debits
c.execute("CREATE INDEX IF NOT EXISTS idx_debits_user_id ON debits (user_id)")

# Constraint CHECK para roles válidos (apenas para novas linhas)
c.execute("PRAGMA foreign_keys = ON")
c.execute("CREATE TABLE IF NOT EXISTS users_tmp AS SELECT * FROM users")
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    roles TEXT NOT NULL DEFAULT 'child' CHECK (roles IN ('child', 'validator', 'admin')),
    password_hash TEXT,
    photo TEXT
)''')
c.execute("INSERT OR IGNORE INTO users SELECT * FROM users_tmp")
c.execute("DROP TABLE users_tmp")

conn.commit()

# Mostrar estrutura
for row in c.execute("PRAGMA table_info(users)"):
    print(row)
for row in c.execute("PRAGMA index_list(users)"):
    print(row)

conn.close()
print("Melhorias aplicadas ao SQLite com sucesso!")
