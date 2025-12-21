"""configure_secrets.py

Script interativo para criar `.streamlit/secrets.toml` localmente de forma segura.
Ele solicita os dados de SMTP (senha via getpass) e grava o arquivo em `.streamlit/secrets.toml` com permissão 600 (quando suportado).
Também tenta uma conexão de teste ao servidor SMTP usando as credenciais fornecidas.

Uso: python configure_secrets.py
"""
import getpass
import os
from pathlib import Path
import smtplib

SECRETS_PATH = Path('.streamlit') / 'secrets.toml'


def prompt(prompt_text, default=None):
    if default:
        v = input(f"{prompt_text} [{default}]: ")
        return v.strip() or default
    else:
        return input(f"{prompt_text}: ").strip()


def yesno(prompt_text, default=True):
    d = 'Y/n' if default else 'y/N'
    v = input(f"{prompt_text} ({d}): ").strip().lower()
    if v == '':
        return default
    return v in ('y','yes')


def test_smtp(cfg):
    try:
        use_ssl = cfg.get('use_ssl', False)
        port = int(cfg.get('port', 465 if use_ssl else 587))
        server_addr = cfg['server']
        if use_ssl:
            s = smtplib.SMTP_SSL(server_addr, port, timeout=10)
        else:
            s = smtplib.SMTP(server_addr, port, timeout=10)
            s.starttls()
        user = cfg.get('user')
        pwd = cfg.get('password')
        if user and pwd:
            s.login(user, pwd)
        s.quit()
        return True, 'Conexão SMTP bem-sucedida.'
    except Exception as e:
        return False, f'Falha no teste SMTP: {e}'


def main():
    print('Configurar secrets SMTP (arquivo local: .streamlit/secrets.toml)')
    print('Observação: o arquivo NÃO deverá ser comitado. Ele já está listado no .gitignore')

    server = prompt('SMTP server (ex: smtp.gmail.com)')
    port = prompt('Porta (587 para STARTTLS, 465 para SSL)', '587')
    user = prompt('Usuário (login / e-mail)')
    password = getpass.getpass('Senha (não será exibida): ')
    sender = prompt('From (remetente) - deixar em branco para usar o usuário', user) or user
    use_ssl = yesno('Usar SSL/TLS direto (SMTPS, porta 465)?', False)

    cfg = {
        'server': server,
        'port': port,
        'user': user,
        'password': password,
        'from': sender,
        'use_ssl': 'true' if use_ssl else 'false'
    }

    # Garantir diretório
    d = SECRETS_PATH.parent
    d.mkdir(parents=True, exist_ok=True)

    # Gravar toml simples
    lines = ['[smtp]']
    lines.append(f'server = "{cfg['server']}"')
    lines.append(f'port = {cfg['port']}')
    lines.append(f'user = "{cfg['user']}"')
    lines.append(f'password = "{cfg['password']}"')
    lines.append(f'from = "{cfg['from']}"')
    lines.append(f'use_ssl = {cfg['use_ssl']}')

    content = '\n'.join(lines) + '\n'

    SECRETS_PATH.write_text(content, encoding='utf-8')

    # Tentar restringir permissões (Unix); no Windows pode não ter efeito
    try:
        os.chmod(SECRETS_PATH, 0o600)
    except Exception:
        pass

    print(f'Arquivo gravado em: {SECRETS_PATH.resolve()} (não commit)')

    print('Executando teste de conexão SMTP...')
    ok, msg = test_smtp({'server': server, 'port': port, 'user': user, 'password': password, 'use_ssl': use_ssl})
    if ok:
        print('OK:', msg)
    else:
        print('ERRO:', msg)
        print('Verifique host/porta/usuário/senha e tente novamente.')

    print('Concluído.')


if __name__ == '__main__':
    main()
