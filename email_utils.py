"""Utilitários para envio de e-mail e logs.

- Usa `st.secrets['smtp']` quando disponível. Campos esperados:
  server, port, user, password, from, use_ssl (opcional)

Funções:
- send_email(to_addresses, subject, body) -> (success: bool, message: str)
- test_smtp_connection() -> (success: bool, message: str)
"""
import smtplib
from email.message import EmailMessage
import logging
import re

logger = logging.getLogger("email_utils")

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


def _normalize_addresses(addrs):
    if not addrs:
        return []
    if isinstance(addrs, str):
        addrs = [addrs]
    return [a.strip() for a in addrs if a and isinstance(a, str) and EMAIL_REGEX.match(a.strip())]


def _get_smtp_config():
    try:
        import streamlit as st
        smtp = st.secrets.get('smtp', None) if hasattr(st, 'secrets') else None
    except Exception:
        smtp = None
    return smtp


def send_email(to_addresses, subject, body):
    """Envia e-mail via SMTP quando configurado via `st.secrets['smtp']`.
    Retorna (True, msg) se enviado, ou (False, erro_msg) se falhar ou config ausente.
    """
    smtp = _get_smtp_config()
    to_list = _normalize_addresses(to_addresses)
    if not to_list:
        msg = "Nenhum destinatário válido fornecido."
        logger.warning(msg)
        return False, msg

    if not smtp:
        # Simulação / ambiente de desenvolvimento
        logger.info(f"Simulated email -> To: {to_list} | Subject: {subject} | Body: {body}")
        return False, "SMTP não configurado; e-mail simulado (veja logs)."

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = smtp.get('from') or smtp.get('user')
        msg['To'] = ', '.join(to_list)
        msg.set_content(body)

        use_ssl = bool(smtp.get('use_ssl', False))
        port = int(smtp.get('port', 465 if use_ssl else 587))
        server_addr = smtp.get('server')

        if use_ssl:
            server = smtplib.SMTP_SSL(server_addr, port, timeout=10)
        else:
            server = smtplib.SMTP(server_addr, port, timeout=10)
            server.starttls()

        user = smtp.get('user')
        pwd = smtp.get('password')
        if user and pwd:
            server.login(user, pwd)

        server.send_message(msg)
        server.quit()
        logger.info(f"E-mail enviado para {to_list}: {subject}")
        return True, "E-mail enviado com sucesso."
    except Exception as exc:
        logger.exception("Erro ao enviar e-mail")
        return False, f"Erro ao enviar e-mail: {exc}"


def test_smtp_connection():
    """Tenta conectar ao servidor SMTP configurado e faz login se credenciais estiverem presentes."""
    smtp = _get_smtp_config()
    if not smtp:
        return False, "SMTP não configurado em `st.secrets['smtp']`."
    try:
        use_ssl = bool(smtp.get('use_ssl', False))
        port = int(smtp.get('port', 465 if use_ssl else 587))
        server_addr = smtp.get('server')
        if use_ssl:
            server = smtplib.SMTP_SSL(server_addr, port, timeout=10)
        else:
            server = smtplib.SMTP(server_addr, port, timeout=10)
            server.starttls()
        user = smtp.get('user')
        pwd = smtp.get('password')
        if user and pwd:
            server.login(user, pwd)
        server.quit()
        return True, "Conexão SMTP bem-sucedida."
    except Exception as exc:
        logger.exception("Teste SMTP falhou")
        return False, f"Falha ao conectar/login SMTP: {exc}"

