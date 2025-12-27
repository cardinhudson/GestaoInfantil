"""Script de teste para verificar se está conseguindo ler dados do Supabase"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Configuração de logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Teste 1: Verificar variáveis de ambiente
print("=" * 60)
print("TESTE 1: Variáveis de Ambiente")
print("=" * 60)
gestao_db = os.environ.get("GESTAO_DB")
database_url = os.environ.get("DATABASE_URL")
print(f"GESTAO_DB: {gestao_db[:50] + '...' if gestao_db else 'NÃO DEFINIDO'}")
print(f"DATABASE_URL: {database_url[:50] + '...' if database_url else 'NÃO DEFINIDO'}")

# Teste 2: Tentar conexão ao banco
print("\n" + "=" * 60)
print("TESTE 2: Conectando ao banco de dados")
print("=" * 60)
try:
    from db import get_connection, DB_TARGET, DB_KIND
    print(f"DB_KIND: {DB_KIND}")
    print(f"DB_TARGET: {DB_TARGET[:50] + '...' if DB_TARGET else 'NÃO DEFINIDO'}")
    
    conn = get_connection()
    print(f"✅ Conexão estabelecida: {type(conn)}")
    
    # Teste 3: Listar usuários
    print("\n" + "=" * 60)
    print("TESTE 3: Lendo usuários do banco")
    print("=" * 60)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM users")
    row = cur.fetchone()
    count = list(row.values())[0] if isinstance(row, dict) else row[0]
    print(f"Total de usuários no banco: {count}")
    
    if count > 0:
        cur.execute("SELECT id, name, email, roles FROM users ORDER BY id LIMIT 10")
        rows = cur.fetchall()
        print(f"\nPrimeiros usuários:")
        for row in rows:
            if isinstance(row, dict):
                print(f"  ID {row['id']}: {row['name']} ({row['email']}) - {row['roles']}")
            else:
                print(f"  {row}")
    else:
        print("⚠️ Nenhum usuário encontrado no banco!")
    
    cur.close()
    conn.close()
    print("✅ Leitura concluída com sucesso!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

# Teste 4: Tentar via services
print("\n" + "=" * 60)
print("TESTE 4: Lendo via módulo services")
print("=" * 60)
try:
    from services import list_users
    users = list_users()
    print(f"Total de usuários retornados por list_users(): {len(users)}")
    if users:
        for user in users[:5]:
            print(f"  ID {user.id}: {user.name} ({user.email}) - {user.roles}")
    else:
        print("⚠️ list_users() retornou lista vazia!")
except Exception as e:
    print(f"❌ ERRO ao chamar list_users(): {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Teste finalizado")
print("=" * 60)
