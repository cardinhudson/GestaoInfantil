"""
Script para corrigir foreign keys quebradas no banco SQLite.
As tabelas tasks e debits estão com FK apontando para users_old em vez de users.
"""
import sqlite3
import os

db_path = 'gestaoinfantil.db'
print(f"Corrigindo banco: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Desabilitar foreign keys temporariamente
c.execute('PRAGMA foreign_keys=OFF')

print("\n=== CORRIGINDO TABELA TASKS ===")

# Verificar estrutura atual
print("Estrutura atual de tasks:")
for row in c.execute("PRAGMA table_info(tasks)"):
    print(f"  {row}")

# Backup dos dados
print("Fazendo backup dos dados...")
c.execute("SELECT * FROM tasks")
tasks_data = c.fetchall()
print(f"  {len(tasks_data)} tarefas encontradas")

# Obter colunas
c.execute("PRAGMA table_info(tasks)")
tasks_columns = [row[1] for row in c.fetchall()]
print(f"  Colunas: {tasks_columns}")

# Renomear tabela antiga
print("Renomeando tasks para tasks_backup...")
c.execute("ALTER TABLE tasks RENAME TO tasks_backup")

# Criar nova tabela com FK correta
print("Criando nova tabela tasks...")
c.execute('''CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    points INTEGER NOT NULL,
    conversion_type VARCHAR NOT NULL,
    child_id INTEGER NOT NULL,
    submitted_by_id INTEGER NOT NULL,
    validator_id INTEGER,
    validated BOOLEAN,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    validated_at DATETIME,
    FOREIGN KEY (child_id) REFERENCES users(id),
    FOREIGN KEY (submitted_by_id) REFERENCES users(id),
    FOREIGN KEY (validator_id) REFERENCES users(id)
)''')

# Restaurar dados
print("Restaurando dados...")
if tasks_data:
    placeholders = ','.join(['?' for _ in tasks_columns])
    cols = ','.join(tasks_columns)
    c.executemany(f"INSERT INTO tasks ({cols}) VALUES ({placeholders})", tasks_data)
print(f"  {len(tasks_data)} tarefas restauradas")

# Remover backup
print("Removendo backup...")
c.execute("DROP TABLE tasks_backup")

print("\n=== CORRIGINDO TABELA DEBITS ===")

# Verificar estrutura atual
print("Estrutura atual de debits:")
for row in c.execute("PRAGMA table_info(debits)"):
    print(f"  {row}")

# Backup dos dados
print("Fazendo backup dos dados...")
c.execute("SELECT * FROM debits")
debits_data = c.fetchall()
print(f"  {len(debits_data)} débitos encontrados")

# Obter colunas
c.execute("PRAGMA table_info(debits)")
debits_columns = [row[1] for row in c.fetchall()]
print(f"  Colunas: {debits_columns}")

# Renomear tabela antiga
print("Renomeando debits para debits_backup...")
c.execute("ALTER TABLE debits RENAME TO debits_backup")

# Criar nova tabela com FK correta
print("Criando nova tabela debits...")
c.execute('''CREATE TABLE debits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    points_deducted INTEGER NOT NULL,
    money_amount FLOAT,
    hours_amount FLOAT,
    reason TEXT,
    performed_by_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (performed_by_id) REFERENCES users(id)
)''')

# Restaurar dados
print("Restaurando dados...")
if debits_data:
    placeholders = ','.join(['?' for _ in debits_columns])
    cols = ','.join(debits_columns)
    c.executemany(f"INSERT INTO debits ({cols}) VALUES ({placeholders})", debits_data)
print(f"  {len(debits_data)} débitos restaurados")

# Remover backup
print("Removendo backup...")
c.execute("DROP TABLE debits_backup")

# Remover tabela users_tmp se existir
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_tmp'")
if c.fetchone():
    print("\nRemovendo tabela users_tmp...")
    c.execute("DROP TABLE users_tmp")

# Recriar índices
print("\n=== RECRIANDO ÍNDICES ===")
c.execute('CREATE INDEX IF NOT EXISTS idx_tasks_child_id ON tasks (child_id)')
c.execute('CREATE INDEX IF NOT EXISTS idx_debits_user_id ON debits (user_id)')

# Reabilitar foreign keys
c.execute('PRAGMA foreign_keys=ON')

conn.commit()

print("\n=== VERIFICANDO CORREÇÃO ===")

print("Foreign keys de tasks:")
for row in c.execute("PRAGMA foreign_key_list(tasks)"):
    print(f"  {row}")

print("Foreign keys de debits:")
for row in c.execute("PRAGMA foreign_key_list(debits)"):
    print(f"  {row}")

# Verificar integridade
print("\nVerificando integridade...")
c.execute("PRAGMA integrity_check")
result = c.fetchone()[0]
print(f"  Resultado: {result}")

conn.close()
print("\n✅ Correção concluída com sucesso!")
