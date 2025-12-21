"""Streamlit App: Gestão de Tarefas Infantis"""
import streamlit as st
import os
from db import init_db
from services import (create_user, list_users, update_user_email, create_task, list_tasks, validate_task,
                      get_conversion, set_conversion, create_debit, get_report, seed_sample_data, save_user_photo)
from email_utils import send_email

import logging
import sys
import traceback

# Logging setup
LOG_DIR = os.environ.get('GESTAO_LOGS', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)]
)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def is_role(user, role):
    return role in (user.roles or "").split(',')


def main():
    st.set_page_config(page_title="Gestão Infantil", layout="wide")
    init_db()
    seed_sample_data()

    st.title("Gestão de Tarefas Infantis")

    users = list_users()
    user_map = {u.id: u for u in users}

    current_user_id = st.sidebar.selectbox("Usuário atual", options=[u.id for u in users], format_func=lambda id: user_map[id].name)
    current_user = user_map[current_user_id]

    page = st.sidebar.radio("Página", ['Dashboard','Tarefas','Validar Tarefas','Conversões','Usuários','Débitos','Relatórios','E-mails'])

    if page == 'Dashboard':
        st.header("Resumo")
        report = get_report()

        st.subheader('Crianças — Saldo')
        children_report = [r for r in report if 'child' in (r['user'].roles or '')]
        if children_report:
            header_cols = st.columns([1,2,1,1,1,1,1])
            header_cols[0].markdown('**Foto**')
            header_cols[1].markdown('**Nome**')
            header_cols[2].markdown('**Pontos Validados**')
            header_cols[3].markdown('**Pontos Debitados**')
            header_cols[4].markdown('**Saldo (pontos)**')
            header_cols[5].markdown('**Saldo (R$)**')
            header_cols[6].markdown('**Saldo (horas)**')

            for r in children_report:
                cols_row = st.columns([1,2,1,1,1,1,1])
                u = r['user']
                if u.photo and os.path.exists(u.photo):
                    cols_row[0].image(u.photo, width=60)
                else:
                    cols_row[0].write('—')
                cols_row[1].write(u.name)
                cols_row[2].write(r['points'])
                cols_row[3].write(r['deducted'])
                cols_row[4].write(r['balance_points'])
                cols_row[5].write(r['money'])
                cols_row[6].write(r['hours'])
        else:
            st.info('Nenhuma criança encontrada.')

        st.subheader("Incluir Tarefa")
        with st.form('new_task'):
            name = st.text_input('Nome da tarefa')
            points = st.number_input('Pontos', min_value=1, value=1)
            conv_type = st.selectbox('Conversão', ['money', 'hours'])
            child = st.selectbox('Para criança', options=[u.id for u in users if 'child' in (u.roles or '')], format_func=lambda id: user_map[id].name)
            # escolher validador (pais)
            validators = [u.id for u in users if 'validator' in (u.roles or '')]
            validator = st.selectbox('Validador', options=validators, format_func=lambda id: user_map[id].name)
            submitted_by = current_user_id
            submitted = st.form_submit_button('Registrar tarefa')
            if submitted:
                task = create_task(name, int(points), conv_type, child, submitted_by, validator)
                # Notificações por e-mail: validar e enviar
                to_candidates = [user_map[submitted_by].email, user_map[validator].email]
                tos = [e for e in to_candidates if e and '@' in e]
                if tos:
                    ok, msg = send_email(tos, f"Nova tarefa registrada: {name}", f"Tarefa: {name}\nPontos: {points}\nPara: {user_map[child].name}")
                    if ok:
                        st.success('Tarefa registrada e e-mails enviados.')
                    else:
                        st.warning(f'Tarefa registrada, mas envio de e-mail falhou: {msg}')
                else:
                    st.info('Tarefa registrada. Nenhum e-mail válido configurado para notificação.')
        st.header('Todas as tarefas')
        tasks = list_tasks()
        for t in tasks:
            st.write(f"{t.id} - {t.name} | {t.points} pts | Para: {t.child_id} | Validada: {t.validated}")

    elif page == 'Validar Tarefas':
        st.header('Tarefas pendentes')
        if not is_role(current_user, 'validator'):
            st.warning('Você não tem permissão para validar tarefas.')
        else:
            tasks = list_tasks(validated=False)
            for t in tasks:
                st.write(f"ID {t.id} - {t.name} | {t.points} pts | Para: {t.child_id}")
                if st.button(f'Validar {t.id}', key=f'val_{t.id}'):
                    validate_task(t.id, current_user_id)
                    # notificar solicitante (usa get_report importado no topo; evitar import local que causa UnboundLocalError)
                    send_email([t.submitted_by.email or ''], f"Tarefa validada: {t.name}", f"Sua tarefa {t.name} foi validada.")
                    st.success('Tarefa validada e notificação enviada (ou simulada).')

    elif page == 'Conversões':
        st.header('Fatores de Conversão')
        conv = get_conversion()
        money = st.number_input('R$ por ponto', value=float(conv.money_per_point), step=0.01)
        hours = st.number_input('Horas por ponto', value=float(conv.hours_per_point), step=0.01)
        if st.button('Salvar conversões'):
            set_conversion(float(money), float(hours))
            st.success('Conversões atualizadas.')

    elif page == 'Usuários':
        st.header('Cadastro de integrantes')
        with st.form('new_user'):
            name = st.text_input('Nome')
            email = st.text_input('E-mail')
            roles = st.multiselect('Papeis', options=['child','parent','validator'], default=['child'])
            photo_file = st.file_uploader('Foto (png/jpg)', type=['png','jpg','jpeg'])
            submitted = st.form_submit_button('Criar usuário')
            if submitted:
                new_user = create_user(name=name, email=email, roles=','.join(roles))
                if photo_file is not None:
                    # salvar foto
                    save_user_photo(new_user.id, photo_file.read(), photo_file.name)
                st.success('Usuário criado.')
        st.subheader('Lista de usuários')
        for u in list_users():
            cols_main = st.columns([1,4])
            if u.photo and os.path.exists(u.photo):
                cols_main[0].image(u.photo, width=100)
            else:
                cols_main[0].write('Sem foto')
            cols_main[1].write(f"{u.id} - {u.name} | {u.email} | {u.roles}")
            cols = st.columns([1,2])
            new_email = cols[1].text_input(f'Editar email {u.id}', value=u.email or '', key=f'email_{u.id}')
            if cols[0].button('Salvar e-mail', key=f'save_email_{u.id}'):
                update_user_email(u.id, new_email)
                st.success('E-mail atualizado.')

            # Upload de nova foto
            photo_edit = st.file_uploader(f'Enviar nova foto para {u.name}', type=['png','jpg','jpeg'], key=f'photo_{u.id}')
            if photo_edit is not None and st.button(f'Salvar foto {u.id}', key=f'save_photo_{u.id}'):
                save_user_photo(u.id, photo_edit.read(), photo_edit.name)
                st.success('Foto atualizada.')

    elif page == 'Débitos':
        st.header('Realizar débito')
        # Permissão unificada: validators também podem realizar débitos (antes existia 'debiter')
        if not is_role(current_user, 'validator') and not is_role(current_user, 'parent'):
            st.warning('Você não tem permissão para realizar débitos.')
        else:
            users_children = [u for u in users if 'child' in (u.roles or '')]
            target = st.selectbox('Criança', options=[u.id for u in users_children], format_func=lambda id: user_map[id].name)
            amount_money = st.number_input('Valor (R$)', min_value=0.0, step=0.5)
            amount_hours = st.number_input('Horas', min_value=0.0, step=0.1)
            reason = st.text_input('Motivo')
            if st.button('Confirmar débito'):
                conv = get_conversion()
                # converter para pontos equivalentes
                points_from_money = int(amount_money / conv.money_per_point) if amount_money else 0
                points_from_hours = int(amount_hours / conv.hours_per_point) if amount_hours else 0
                points = points_from_money + points_from_hours
                if points <= 0:
                    st.warning('Valor/hora inválidos (resulta em 0 pontos).')
                else:
                    create_debit(user_id=target, points=points, money=amount_money or None, hours=amount_hours or None, reason=reason, performed_by_id=current_user_id)
                    st.success('Débito realizado e registrado.')

    elif page == 'Relatórios':
        st.header('Relatórios financeiros e de horas')
        report = get_report()
        st.table([{
            'Nome': r['user'].name,
            'Saldo pontos': r['balance_points'],
            'Saldo R$': r['money'],
            'Saldo horas': r['hours']
        } for r in report])

    elif page == 'E-mails':
        st.header('Configurar e-mails dos responsáveis')
        st.write('Edite os e-mails dos responsáveis para receber notificações.')
        for u in list_users():
            if 'parent' in (u.roles or '') or 'validator' in (u.roles or ''):
                cols = st.columns([2,1])
                email = cols[0].text_input(f'E-mail {u.name}', value=u.email or '', key=f'email_edit_{u.id}')
                if cols[1].button('Salvar', key=f'save_em_{u.id}'):
                    update_user_email(u.id, email)
                    st.success('E-mail atualizado.')

        st.markdown('---')
        st.subheader('Configurar / Testar SMTP')
        import email_utils as eu
        smtp_configured = False
        try:
            smtp_configured = bool(getattr(st, 'secrets', None) and st.secrets.get('smtp'))
        except Exception:
            smtp_configured = False

        st.write('Status SMTP: ', '✅ Configurado' if smtp_configured else '⚠️ Não configurado')
        if smtp_configured:
            if st.button('Testar conexão SMTP'):
                ok, msg = eu.test_smtp_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

            # Enviar e-mail de teste
            test_to = st.text_input('Enviar e-mail de teste para', value='')
            if st.button('Enviar e-mail de teste'):
                if not test_to:
                    st.warning('Informe um e-mail de destino válido.')
                else:
                    ok, msg = eu.send_email(test_to, 'Teste de e-mail - Gestão Infantil', 'Esta é uma mensagem de teste.')
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.info('Configure `st.secrets["smtp"]` para habilitar envio real de e-mails. veja README para instruções.')


if __name__ == '__main__':
    try:
        logging.info("Starting Gestão Infantil app")
        main()
    except Exception:
        logging.exception("Unhandled exception running app")
        import sys, traceback
        traceback.print_exc(file=sys.stderr)
        raise
