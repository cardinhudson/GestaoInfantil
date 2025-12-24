#!/usr/bin/env python3
"""Teste de conexão ao DB usado pelo app.

Uso:
  - Defina a variável de ambiente `GESTAO_DB` ou crie `.streamlit/secrets.toml` com GESTAO_DB.
  - Rode: `python scripts/test_db_connection.py`

O script tentará conectar ao Postgres (se a URL começa com "postgres") ou
abrirá o arquivo SQLite local e verificará se as tabelas existem.
"""
import os
import sys
import sqlite3
import traceback


def test_sqlite(path: str):
    print(f"Testando SQLite em: {path}")
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tabelas existentes:", tables)
        return True
    finally:
        conn.close()


def test_postgres(dsn: str):
    try:
        import psycopg2
        import psycopg2.extras
    except Exception as e:
        print("psycopg2 não está instalado. Instale com: pip install psycopg2-binary")
        raise
    print("Testando Postgres com DSN (ocultando credenciais na saída)")
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur = conn.cursor()
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
        rows = cur.fetchall()
        tables = [r['tablename'] for r in rows]
        print("Tabelas públicas:", tables)
        cur.close()
        return True
    finally:
        conn.close()


def main():
    target = os.environ.get('GESTAO_DB')
    if not target:
        # tentar secrets do Streamlit localmente
        try:
            import tomllib
            p = os.path.join('.streamlit', 'secrets.toml')
            if os.path.exists(p):
                with open(p, 'rb') as fh:
                    data = tomllib.load(fh)
                    target = data.get('GESTAO_DB') or data.get('database', {}).get('GESTAO_DB')
        except Exception:
            # fallback para Python <3.11 sem tomllib
            try:
                import toml
                p = os.path.join('.streamlit', 'secrets.toml')
                if os.path.exists(p):
                    data = toml.load(p)
                    target = data.get('GESTAO_DB') or data.get('database', {}).get('GESTAO_DB')
            except Exception:
                pass

    if not target:
        print('Nenhuma variável GESTAO_DB encontrada. Usando SQLite local padrão.')
        sqlite_path = os.path.abspath(os.environ.get('GESTAO_DB', 'gestaoinfantil.db'))
        try:
            ok = test_sqlite(sqlite_path)
            print('Conexão SQLite OK' if ok else 'Falha SQLite')
            sys.exit(0 if ok else 2)
        except Exception:
            traceback.print_exc()
            sys.exit(3)

    if target.startswith('postgres'):
        try:
            ok = test_postgres(target)
            print('Conexão Postgres OK' if ok else 'Falha Postgres')
            sys.exit(0 if ok else 4)
        except Exception:
            traceback.print_exc()
            sys.exit(5)

    # tratar como caminho sqlite
    try:
        sqlite_path = target.replace('sqlite:///', '') if target.startswith('sqlite:///') else target
        ok = test_sqlite(sqlite_path)
        print('Conexão SQLite OK' if ok else 'Falha SQLite')
        sys.exit(0 if ok else 6)
    except Exception:
        traceback.print_exc()
        sys.exit(7)


if __name__ == '__main__':
    main()
