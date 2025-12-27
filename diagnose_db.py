"""Script para diagnosticar e corrigir problemas no banco SQLite."""
import sqlite3
import os

db_path = 'gestaoinfantil.db'
print(f"Analisando banco: {db_path}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("\n=== TABELAS ===")
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(f"  - {row[0]}")

print("\n=== TRIGGERS ===")
triggers = list(c.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'"))
if triggers:
    for name, sql in triggers:
        print(f"  - {name}")
        if 'users_old' in (sql or ''):
            print(f"    ⚠️ ENCONTRADO: referência a users_old!")
            print(f"    SQL: {sql}")
else:
    print("  Nenhum trigger encontrado")

print("\n=== VIEWS ===")
views = list(c.execute("SELECT name, sql FROM sqlite_master WHERE type='view'"))
if views:
    for name, sql in views:
        print(f"  - {name}")
        if 'users_old' in (sql or ''):
            print(f"    ⚠️ ENCONTRADO: referência a users_old!")
else:
    print("  Nenhuma view encontrada")

print("\n=== ÍNDICES ===")
for row in c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name"):
    name, tbl = row
    if 'users_old' in (name or '') or 'users_old' in (tbl or ''):
        print(f"  ⚠️ {name} (tabela: {tbl}) - REFERÊNCIA A users_old!")
    else:
        print(f"  - {name} (tabela: {tbl})")

print("\n=== FOREIGN KEYS (tasks) ===")
for row in c.execute("PRAGMA foreign_key_list(tasks)"):
    print(f"  {row}")

print("\n=== PROCURANDO 'users_old' EM TODO O SCHEMA ===")
all_objects = list(c.execute("SELECT name, type, sql FROM sqlite_master WHERE sql IS NOT NULL"))
found = False
for name, obj_type, sql in all_objects:
    if 'users_old' in sql:
        print(f"  ⚠️ {obj_type} '{name}' contém 'users_old'")
        print(f"     SQL: {sql[:200]}...")
        found = True

if not found:
    print("  Nenhuma referência a users_old encontrada no schema")

# Verificar se users_old existe
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_old'")
if c.fetchone():
    print("\n⚠️ TABELA users_old AINDA EXISTE! Removendo...")
    c.execute("DROP TABLE IF EXISTS users_old")
    conn.commit()
    print("✅ Tabela users_old removida")
else:
    print("\n✅ Tabela users_old não existe (correto)")

conn.close()
print("\nDiagnóstico concluído!")
