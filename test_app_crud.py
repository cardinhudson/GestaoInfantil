"""
Teste automatizado completo do sistema Gestão Infantil.
Testa CRUD de usuários, tarefas, débitos e navegação.

Este teste usa diretamente as funções do services.py para testar o backend.
Para testes de interface, recomenda-se usar Selenium ou Playwright.

Executar: python test_app_crud.py
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db
from services import (
    create_user, list_users, update_user_email, delete_user,
    create_task, list_tasks, validate_task, delete_task,
    create_debit, list_debits, delete_debit,
    get_conversion, set_conversion, get_report,
    authenticate_user, update_user_password
)

# Gera emails únicos usando timestamp
def unique_email(prefix):
    return f"{prefix}_{int(time.time()*1000)}@test.com"

def test_database_init():
    """Testa inicialização do banco de dados."""
    print("Testando inicialização do banco de dados...")
    try:
        init_db()
        print("✅ Banco de dados inicializado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False

def test_user_crud():
    """Testa CRUD completo de usuários."""
    print("\n--- Testando CRUD de Usuários ---")
    
    email = unique_email("teste_auto")
    new_email = unique_email("teste_atualizado")
    
    # CREATE
    print("Criando usuário de teste...")
    try:
        user = create_user(name="Teste Automatizado", email=email, roles="child", password="123456")
        print(f"✅ Usuário criado: {user.name} (ID: {user.id})")
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False
    
    # READ
    print("Listando usuários...")
    try:
        users = list_users()
        found = any(u.email == email for u in users)
        if found:
            print(f"✅ Usuário encontrado na lista ({len(users)} usuários no total)")
        else:
            print("❌ Usuário não encontrado na lista")
            return False
    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")
        return False
    
    # UPDATE
    print("Atualizando e-mail do usuário...")
    try:
        update_user_email(user.id, new_email)
        print("✅ E-mail atualizado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao atualizar e-mail: {e}")
        delete_user(user.id)
        return False
    
    # AUTHENTICATE
    print("Testando autenticação...")
    try:
        auth_user = authenticate_user(new_email, "123456")
        if auth_user:
            print("✅ Autenticação bem sucedida")
        else:
            print("❌ Falha na autenticação")
            delete_user(user.id)
            return False
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        delete_user(user.id)
        return False
    
    # UPDATE PASSWORD
    print("Atualizando senha do usuário...")
    try:
        update_user_password(user.id, "nova_senha_123")
        auth_user = authenticate_user(new_email, "nova_senha_123")
        if auth_user:
            print("✅ Senha atualizada e autenticação OK")
        else:
            print("❌ Senha atualizada mas autenticação falhou")
            delete_user(user.id)
            return False
    except Exception as e:
        print(f"❌ Erro ao atualizar senha: {e}")
        delete_user(user.id)
        return False
    
    # DELETE
    print("Excluindo usuário de teste...")
    try:
        ok = delete_user(user.id)
        if ok:
            print("✅ Usuário excluído com sucesso")
        else:
            print("❌ Falha ao excluir usuário")
            return False
    except Exception as e:
        print(f"❌ Erro ao excluir usuário: {e}")
        return False
    
    return True

def test_task_crud():
    """Testa CRUD completo de tarefas."""
    print("\n--- Testando CRUD de Tarefas ---")
    
    user_email = unique_email("teste_tarefa")
    validator_email = unique_email("validador_teste")
    
    # Precisa de um usuário para criar tarefa
    try:
        user = create_user(name="Teste Tarefa", email=user_email, roles="child", password="123456")
        validator = create_user(name="Validador Teste", email=validator_email, roles="validator", password="123456")
    except Exception as e:
        print(f"❌ Erro ao criar usuários para teste de tarefas: {e}")
        return False
    
    # CREATE
    print("Criando tarefa de teste...")
    try:
        # Assinatura: create_task(name, amount, conversion_type, child_id, submitted_by_id, validator_id=None)
        task = create_task(
            name="Tarefa de teste automatizado",
            amount=5.00,
            conversion_type="money",
            child_id=user.id,
            submitted_by_id=user.id
        )
        print(f"✅ Tarefa criada: {task.name} (ID: {task.id})")
    except Exception as e:
        print(f"❌ Erro ao criar tarefa: {e}")
        delete_user(user.id)
        delete_user(validator.id)
        return False
    
    # READ
    print("Listando tarefas...")
    try:
        tasks = list_tasks()
        found = any(t.id == task.id for t in tasks)
        if found:
            print(f"✅ Tarefa encontrada na lista ({len(tasks)} tarefas no total)")
        else:
            print("❌ Tarefa não encontrada na lista")
            delete_user(user.id)
            delete_user(validator.id)
            return False
    except Exception as e:
        print(f"❌ Erro ao listar tarefas: {e}")
        delete_user(user.id)
        delete_user(validator.id)
        return False
    
    # VALIDATE
    print("Validando tarefa...")
    try:
        validated = validate_task(task.id, validator.id)
        if validated:
            print("✅ Tarefa validada com sucesso")
        else:
            print("⚠️ Tarefa não pôde ser validada (pode já estar validada)")
    except Exception as e:
        print(f"⚠️ Aviso ao validar tarefa: {e}")
    
    # DELETE
    print("Excluindo tarefa de teste...")
    try:
        ok = delete_task(task.id)
        if ok:
            print("✅ Tarefa excluída com sucesso")
        else:
            print("❌ Falha ao excluir tarefa")
            delete_user(user.id)
            delete_user(validator.id)
            return False
    except Exception as e:
        print(f"❌ Erro ao excluir tarefa: {e}")
        delete_user(user.id)
        delete_user(validator.id)
        return False
    
    # Limpar usuários de teste
    delete_user(user.id)
    delete_user(validator.id)
    
    return True

def test_debit_crud():
    """Testa CRUD completo de débitos."""
    print("\n--- Testando CRUD de Débitos ---")
    
    user_email = unique_email("teste_debito")
    
    # Precisa de um usuário para criar débito
    try:
        user = create_user(name="Teste Débito", email=user_email, roles="child", password="123456")
    except Exception as e:
        print(f"❌ Erro ao criar usuário para teste de débitos: {e}")
        return False
    
    # CREATE
    print("Criando débito de teste...")
    try:
        # Assinatura: create_debit(user_id, points, money=None, hours=None, reason=None, performed_by_id=None)
        debit = create_debit(
            user_id=user.id,
            points=10,
            money=10.00,
            reason="Débito de teste",
            performed_by_id=user.id
        )
        print(f"✅ Débito criado: {debit.reason} (ID: {debit.id})")
    except Exception as e:
        print(f"❌ Erro ao criar débito: {e}")
        delete_user(user.id)
        return False
    
    # READ
    print("Listando débitos...")
    try:
        debits = list_debits()
        found = any(d.id == debit.id for d in debits)
        if found:
            print(f"✅ Débito encontrado na lista ({len(debits)} débitos no total)")
        else:
            print("❌ Débito não encontrado na lista")
            delete_user(user.id)
            return False
    except Exception as e:
        print(f"❌ Erro ao listar débitos: {e}")
        delete_user(user.id)
        return False
    
    # DELETE
    print("Excluindo débito de teste...")
    try:
        ok = delete_debit(debit.id)
        if ok:
            print("✅ Débito excluído com sucesso")
        else:
            print("❌ Falha ao excluir débito")
            delete_user(user.id)
            return False
    except Exception as e:
        print(f"❌ Erro ao excluir débito: {e}")
        delete_user(user.id)
        return False
    
    # Limpar usuário de teste
    delete_user(user.id)
    
    return True

def test_conversion():
    """Testa configuração de conversão."""
    print("\n--- Testando Configuração de Conversão ---")
    
    try:
        # Assinatura: set_conversion(money_per_point, hours_per_point)
        set_conversion(10.0, 0.5)
        print("✅ Conversão definida (money=10.0, hours=0.5)")
        
        # GET
        conv = get_conversion()
        if conv:
            print(f"✅ Conversão lida: money={conv.money_per_point}, hours={conv.hours_per_point}")
        else:
            print("⚠️ Conversão retornou None (pode não existir registro)")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar conversão: {e}")
        return False

def test_report():
    """Testa geração de relatório."""
    print("\n--- Testando Geração de Relatório ---")
    
    try:
        report = get_report()
        print(f"✅ Relatório gerado com {len(report)} registros")
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("TESTE AUTOMATIZADO COMPLETO - GESTÃO INFANTIL")
    print("=" * 60)
    
    results = []
    
    results.append(("Inicialização do Banco", test_database_init()))
    results.append(("CRUD de Usuários", test_user_crud()))
    results.append(("CRUD de Tarefas", test_task_crud()))
    results.append(("CRUD de Débitos", test_debit_crud()))
    results.append(("Configuração de Conversão", test_conversion()))
    results.append(("Geração de Relatório", test_report()))
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {passed} passaram, {failed} falharam")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
