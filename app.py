"""Streamlit App: Gestão de Tarefas Infantis"""
import streamlit as st
import os
import time
import subprocess
from db import init_db
from services import (create_user, list_users, update_user_email, create_task, list_tasks, validate_task,
                      get_conversion, set_conversion, create_debit, get_report, seed_sample_data, save_user_photo,
                      authenticate_user, get_user_by_email, update_user_password, list_debits, delete_user, delete_task, delete_debit)
# Envio de e-mail desabilitado por padrão para evitar falhas em ambientes sem SMTP

import logging
import sys
import traceback
import pandas as pd
import plotly.express as px


def safe_rerun():
    """Tenta usar st.experimental_rerun() quando disponível; caso contrário usa st.stop().
    Isso evita AttributeError em versões do Streamlit que não expõem experimental_rerun.
    """
    try:
        fn = getattr(st, 'experimental_rerun', None)
        if callable(fn):
            fn()
            return
    except Exception:
        pass
    try:
        # st.stop() interrompe a execução do script atual e força refresh
        st.stop()
    except Exception:
        # último recurso: raise para que Streamlit mostre erro
        raise


def _open_browser():
    """Tenta abrir o navegador no localhost:8501 após um delay."""
    import time
    import webbrowser
    import subprocess
    import os
    time.sleep(2)  # Aguarda o servidor iniciar
    url = 'http://localhost:8501'
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['cmd', '/c', 'start', url], check=False, shell=False)
        else:
            webbrowser.open(url)
        logging.info(f'Navegador aberto automaticamente em {url}')
    except Exception as e:
        logging.debug(f'Falha ao abrir navegador: {e}')


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

# Registrar exceções não tratadas em arquivo para facilitar debug em deploys
def _log_uncaught_exceptions(exctype, value, tb):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, 'startup_error.log'), 'a', encoding='utf-8') as fh:
            fh.write('\n=== Uncaught exception ===\n')
            traceback.print_exception(exctype, value, tb, file=fh)
    except Exception:
        # Não devemos falhar o processo ao tentar logar a exceção
        pass

sys.excepthook = _log_uncaught_exceptions

# Marca de importação para ajudar a diagnosticar se o arquivo é carregado corretamente
try:
    logging.info('app.py imported — starting module initialization')
except Exception:
    pass

# Evita múltiplos disparos de abertura de navegador em reruns do Streamlit
_AUTO_BROWSER_STARTED = False


def photo_or_placeholder(user, width=60):
    path = getattr(user, 'photo', None)
    if path and os.path.exists(path):
        return path
    return None


def is_role(user, role):
    return role in (user.roles or "").split(',')


def _open_local_browser(*args, **kwargs):
    pass


def main():
    st.set_page_config(page_title="Gestão Infantil", layout="wide")

    # ...existing code...

    try:
        init_db()
    except Exception:
        logging.exception("Falha ao inicializar o DB")
    try:
        seed_sample_data()
    except Exception:
        logging.exception("Falha ao rodar seed_sample_data")

    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    st.sidebar.title("Autenticação")

    # Login form
    if not st.session_state.user_id:
        st.title("Gestão Infantil - Login")
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                user = authenticate_user(email, password)
                if user:
                    st.session_state.user_id = user.id
                    safe_rerun()
                else:
                    st.error("Credenciais inválidas")
        st.info("Use as credenciais de exemplo: admin@example.com / 123")
        return

    # Carregar usuário logado
    users = list_users()
    user_map = {u.id: u for u in users}
    current_user = user_map.get(st.session_state.user_id)
    if not current_user:
        st.session_state.user_id = None
        safe_rerun()
        return

    is_validator = 'validator' in (current_user.roles or '')
    is_child = 'child' in (current_user.roles or '')

    with st.sidebar:
        # Mostrar foto do usuário logado (se disponível)
        try:
            photo_path = photo_or_placeholder(current_user)
            if photo_path:
                st.image(photo_path, width=80)
            else:
                st.write('Sem foto')
        except Exception:
            # não falhar a renderização da sidebar por causa da imagem
            pass
        st.markdown(f"**Logado como:** {current_user.name} ({current_user.roles})")
        if st.button("Sair"):
            st.session_state.user_id = None
            safe_rerun()
        # Disponibilizar páginas conforme o papel: validators veem tudo; children veem Tarefas e Débitos (apenas para si)
        if is_validator:
            pages = ['Dashboard','Tarefas','Validar','Débitos','Usuários']
        elif is_child:
            pages = ['Dashboard','Tarefas','Débitos']
        else:
            pages = ['Dashboard']
        page = st.radio("Página", pages)

    # Cabeçalho: mostrar foto e nome do usuário logado antes de tudo (acima do título)
    try:
        hdr_col1, hdr_col2 = st.columns([1, 8])
        if getattr(current_user, 'photo', None) and os.path.exists(current_user.photo):
            hdr_col1.image(current_user.photo, width=64)
        else:
            hdr_col1.write('')
        hdr_col2.markdown(f"**{current_user.name}**")
    except Exception:
        pass

    st.title("Gestão de Tarefas Infantis")

    report = get_report()
    children_report = [r for r in report if 'child' in (r['user'].roles or '')]

    def render_balance_charts(children_report):
        if not children_report:
            st.info('Nenhuma criança cadastrada.')
            return

        names = [r['user'].name for r in children_report]
        photos = [photo_or_placeholder(r['user']) for r in children_report]
        money_values = [r['money'] for r in children_report]
        hour_values = [r['hours'] for r in children_report]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Saldo em dinheiro (R$)')
            fig_money = px.bar(x=names, y=money_values, labels={'x':'Criança','y':'Saldo (R$)'})
            # Aplicar degradê em tons de azul e exibir rótulos com valores formatados
            fig_money.update_traces(
                marker=dict(color=money_values, colorscale='Blues', showscale=False),
                text=[f"R$ {v:.2f}" for v in money_values],
                textposition='auto',
                hovertemplate='%{x}: R$ %{y:.2f}'
            )
            fig_money.update_layout(margin=dict(l=10,r=10,b=40,t=10))
            st.plotly_chart(fig_money, use_container_width=True)
        with col2:
            st.subheader('Saldo em horas')
            fig_hours = px.bar(x=names, y=hour_values, labels={'x':'Criança','y':'Horas'})
            # Usar degradê azul também para horas e rótulos com unidade
            fig_hours.update_traces(
                marker=dict(color=hour_values, colorscale='Blues', showscale=False),
                text=[f"{v:.2f} h" for v in hour_values],
                textposition='auto',
                hovertemplate='%{x}: %{y:.2f} h'
            )
            fig_hours.update_layout(margin=dict(l=10,r=10,b=40,t=10))
            st.plotly_chart(fig_hours, use_container_width=True)

        # (Fotos abaixo dos gráficos removidas por solicitação)

    def render_tables(children_report):
        st.markdown('---')
        st.subheader('Tabela de Dinheiro')
        header = st.columns([1,2,2,2,2])
        header[0].markdown('**Foto**')
        header[1].markdown('**Nome**')
        header[2].markdown('**Realizado (R$)**')
        header[3].markdown('**Debitado (R$)**')
        header[4].markdown('**Saldo (R$)**')
        for r in children_report:
            u = r['user']
            row = st.columns([1,2,2,2,2])
            if photo_or_placeholder(u):
                row[0].image(photo_or_placeholder(u), width=60)
            else:
                row[0].write('—')
            row[1].write(u.name)
            row[2].write(f"R$ {r['earned_money']:.2f}")
            row[3].write(f"R$ {r['debited_money']:.2f}")
            row[4].write(f"R$ {r['money']:.2f}")

        st.subheader('Tabela de Horas')
        header = st.columns([1,2,2,2,2])
        header[0].markdown('**Foto**')
        header[1].markdown('**Nome**')
        header[2].markdown('**Realizado (h)**')
        header[3].markdown('**Debitado (h)**')
        header[4].markdown('**Saldo (h)**')
        for r in children_report:
            u = r['user']
            row = st.columns([1,2,2,2,2])
            if photo_or_placeholder(u):
                row[0].image(photo_or_placeholder(u), width=60)
            else:
                row[0].write('—')
            row[1].write(u.name)
            row[2].write(f"{r['earned_hours']:.2f} h")
            row[3].write(f"{r['debited_hours']:.2f} h")
            row[4].write(f"{r['hours']:.2f} h")

    def render_child_card(r):
        u = r['user']
        money = r['money']
        hours = r['hours']
        col_photo, col_money, col_hours = st.columns([1,2,2])
        if u.photo and os.path.exists(u.photo):
            col_photo.image(u.photo, width=90)
        else:
            col_photo.write('Sem foto')
        col_money.metric("Saldo em R$", f"R$ {money:.2f}")
        col_hours.metric("Saldo em horas", f"{hours:.2f} h")
        col_chart1, col_chart2 = st.columns(2)
        col_chart1.bar_chart(pd.DataFrame({'R$':[money]}, index=['Saldo']))
        col_chart2.bar_chart(pd.DataFrame({'Horas':[hours]}, index=['Saldo']))

    if page == 'Dashboard':
        st.subheader('Saldos por criança')
        if not children_report:
            st.info('Nenhuma criança cadastrada.')
        else:
            render_balance_charts(children_report)
            render_tables(children_report)

    elif page == 'Tarefas':
        if not (is_validator or is_child):
            st.warning('Apenas validadores ou crianças podem cadastrar tarefas.')
        else:
            # filtro por criança (por padrão, child vê seu próprio nome)
            users_children = [u for u in users if 'child' in (u.roles or '')]
            options = [None] + [u.id for u in users_children]
            def fmt(uid):
                if uid is None:
                    return 'Todos'
                return user_map[uid].name
            default = current_user.id if is_child and not is_validator else None
            filter_target = st.selectbox('Filtrar por criança', options=options, format_func=fmt, index=options.index(default) if default in options else 0)

            st.subheader('Cadastrar tarefa')
            with st.form('new_task_form'):
                name = st.text_input('Nome da tarefa')
                amount = st.number_input('Valor', min_value=0.0, step=0.5)
                conv_type = st.selectbox('Tipo', ['money','hours'], format_func=lambda x: 'Dinheiro (R$)' if x=='money' else 'Horas de videogame')
                # Se for child, somente cadastrar para si; se for validator, escolher criança alvo
                if is_child and not is_validator:
                    child = current_user.id
                    st.write(f'Para criança: {current_user.name}')
                else:
                    child = st.selectbox('Para criança', options=[u.id for u in users if 'child' in (u.roles or '')], format_func=lambda id: user_map[id].name)
                # Quando criado por child, deixar validator None (pendente). Quando criado por validator, registrar submitted_by como validator.
                submitted_by = current_user.id
                validator = None if is_child and not is_validator else current_user.id
                submitted = st.form_submit_button('Registrar tarefa')
                if submitted:
                    try:
                        create_task(name, amount, conv_type, child, submitted_by, validator)
                        st.success('Tarefa registrada; aguarde validação.')
                    except Exception as exc:
                        logging.exception('Erro ao criar tarefa')
                        st.error(f'Falha ao registrar tarefa: {exc}')

            st.subheader('Tarefas registradas')
            tasks_all = list_tasks()
            if filter_target is not None:
                tasks_all = [t for t in tasks_all if t.child_id == filter_target]
            for t in tasks_all:
                assignee = user_map[t.child_id].name if t.child_id in user_map else t.child_id
                status = '✅ Validada' if t.validated else '⏳ Pendente'
                cols = st.columns([6,2])
                cols[0].write(f"{t.id} - {t.name} | {t.points} ({'R$' if t.conversion_type=='money' else 'h'}) | Para: {assignee} | {status}")
                if is_validator:
                    if cols[1].button('Excluir', key=f'del_task_{t.id}'):
                        ok = delete_task(t.id)
                        if ok:
                            st.success('Tarefa excluída com sucesso.')
                            st.stop()
                        else:
                            st.error('Falha ao excluir tarefa.')

    elif page == 'Validar':
        if not is_validator:
            st.warning('Apenas validadores podem validar tarefas.')
        else:
            st.subheader('Tarefas pendentes')
            pending = list_tasks(validated=False)
            if not pending:
                st.info('Nenhuma tarefa pendente.')
            for t in pending:
                assignee = user_map[t.child_id].name if t.child_id in user_map else t.child_id
                col1, col2 = st.columns([3,1])
                col1.write(f"{t.name} | {t.points} ({'R$' if t.conversion_type=='money' else 'h'}) | Para: {assignee}")
                if col2.button('Validar', key=f'val_{t.id}'):
                    try:
                        validate_task(t.id, current_user.id)
                        st.success('Tarefa validada.')
                        safe_rerun()
                    except Exception as exc:
                        logging.exception('Erro ao validar tarefa')
                        st.error(f'Falha ao validar tarefa: {exc}')

    elif page == 'Débitos':
        if not (is_validator or is_child):
            st.warning('Apenas validadores ou crianças podem registrar débitos.')
        else:
            st.subheader('Registrar débito')
            users_children = [u for u in users if 'child' in (u.roles or '')]
            # filtro para visualização/seleção: children list + Todos
            options = [None] + [u.id for u in users_children]
            def fmt_deb(uid):
                if uid is None:
                    return 'Todos'
                return user_map[uid].name
            default_deb = current_user.id if is_child and not is_validator else None
            view_filter = st.selectbox('Filtrar débitos por criança', options=options, format_func=fmt_deb, index=options.index(default_deb) if default_deb in options else 0)

            # Form para registrar débito (se child: só para si; se validator: pode escolher)
            if is_child and not is_validator:
                target = current_user.id
                st.write(f'Débito será registrado para: {current_user.name}')
            else:
                target = st.selectbox('Criança (alvo do débito)', options=[u.id for u in users_children], format_func=lambda id: user_map[id].name)
            amount_money = st.number_input('Valor (R$)', min_value=0.0, step=0.5, key='deb_money')
            amount_hours = st.number_input('Horas', min_value=0.0, step=0.1, key='deb_hours')
            reason = st.text_input('Motivo', key='deb_reason')
            if st.button('Confirmar débito'):
                try:
                    create_debit(user_id=target, points=0, money=amount_money or None, hours=amount_hours or None, reason=reason, performed_by_id=current_user.id)
                    st.success('Débito registrado.')
                except Exception as exc:
                    logging.exception('Falha ao registrar débito')
                    st.error(f'Erro ao registrar débito: {exc}')

            # Mostrar débitos conforme filtro
            st.markdown('---')
            st.subheader('Débitos registrados')
            debs = list_debits(user_id=view_filter)
            if not debs:
                st.info('Nenhum débito encontrado para o filtro selecionado.')
            else:
                for d in debs:
                    who = user_map[d.user_id].name if d.user_id in user_map else d.user_id
                    by = user_map[d.performed_by_id].name if d.performed_by_id in user_map else d.performed_by_id
                    parts = []
                    if d.money_amount:
                        parts.append(f"R$ {d.money_amount:.2f}")
                    if d.hours_amount:
                        parts.append(f"{d.hours_amount:.2f} h")
                    pts = ', '.join(parts) if parts else '—'
                    cols = st.columns([8,2])
                    cols[0].write(f"{d.id} | Para: {who} | Valor: {pts} | Por: {by} | Motivo: {d.reason or '-'} | {d.created_at}")
                    if is_validator:
                        if cols[1].button('Excluir', key=f'del_deb_{d.id}'):
                            ok = delete_debit(d.id)
                            if ok:
                                st.success('Débito excluído com sucesso.')
                                st.stop()
                            else:
                                st.error('Falha ao excluir débito.')

    elif page == 'Usuários':
        if not is_validator:
            st.warning('Apenas validadores podem gerenciar usuários.')
        else:
            st.subheader('Criar usuário')
            with st.form('new_user'):
                name = st.text_input('Nome')
                email = st.text_input('E-mail')
                role = st.selectbox('Papel', ['child','validator'], format_func=lambda x: 'Child' if x=='child' else 'Validador')
                password = st.text_input('Senha', type='password')
                photo_file = st.file_uploader('Foto (png/jpg)', type=['png','jpg','jpeg'])
                submitted = st.form_submit_button('Criar usuário')
                if submitted:
                    try:
                        new_user = create_user(name=name, email=email, roles=role, password=password)
                        if photo_file is not None:
                            try:
                                save_user_photo(new_user.id, photo_file.read(), photo_file.name)
                            except Exception as e:
                                st.warning(f'⚠️ Usuário criado, mas erro ao fazer upload da foto: {str(e)}')
                        st.success('Usuário criado.')
                        st.stop()  # Mostra feedback e só recarrega na próxima ação do usuário
                    except Exception as e:
                        st.error(f'❌ Erro ao criar usuário: {str(e)}')

            st.subheader('Lista de usuários')
            for u in list_users():
                cols_main = st.columns([1,4,1])
                if u.photo and os.path.exists(u.photo):
                    cols_main[0].image(u.photo, width=80)
                else:
                    cols_main[0].write('Sem foto')
                cols_main[1].write(f"{u.name} | {u.email or 'sem e-mail'} | {u.roles}")
                # Ações: editar e excluir (com confirmação)
                with cols_main[2]:
                    with st.expander('Ações'):
                        if st.button('Editar usuário', key=f'edit_user_btn_{u.id}'):
                            st.session_state[f'edit_user_{u.id}'] = not st.session_state.get(f'edit_user_{u.id}', False)
                        if st.session_state.get(f'edit_user_{u.id}', False):
                            with st.form(f'edit_user_form_{u.id}'):
                                new_name = st.text_input('Nome', value=u.name, key=f'edit_name_{u.id}')
                                new_email = st.text_input('E-mail', value=u.email or '', key=f'edit_email_{u.id}')
                                new_role = st.selectbox('Papel', ['child','validator'], index=0 if u.roles=='child' else 1, format_func=lambda x: 'Child' if x=='child' else 'Validador', key=f'edit_role_{u.id}')
                                new_pwd = st.text_input('Nova senha (deixe em branco para manter)', type='password', key=f'edit_pwd_{u.id}')
                                submitted_edit = st.form_submit_button('Salvar alterações')
                                if submitted_edit:
                                    from services import update_user_full
                                    update_user_full(u.id, new_name, new_email, new_role, new_pwd if new_pwd else None)
                                    st.success('Usuário atualizado.')
                                    st.session_state[f'edit_user_{u.id}'] = False
                                    st.stop()
                        # Ações antigas
                        new_email = st.text_input(f'Editar email {u.id}', value=u.email or '', key=f'email_{u.id}')
                        if st.button('Salvar e-mail', key=f'save_email_{u.id}'):
                            update_user_email(u.id, new_email)
                            st.success('E-mail atualizado.')
                            st.stop()

                        # Trocar senha
                        st.markdown('---')
                        new_pwd = st.text_input(f'Nova senha para {u.name} (deixe em branco para manter)', type='password', key=f'pwd_{u.id}')
                        if new_pwd and st.button('Alterar senha', key=f'chg_pwd_{u.id}'):
                            try:
                                update_user_password(u.id, new_pwd)
                                st.success('Senha atualizada com sucesso.')
                                st.stop()
                            except Exception as exc:
                                logging.exception('Falha ao atualizar senha do usuário')
                                st.error(f'Erro ao atualizar senha: {exc}')

                        st.markdown('---')
                        st.write('Excluir usuário (irrevogável)')
                        confirm = st.checkbox('Confirmar exclusão', key=f'confirm_{u.id}')
                        if confirm and st.button('Excluir usuário', key=f'delete_{u.id}'):
                            # remover foto do disco se existir
                            try:
                                if u.photo and os.path.exists(u.photo):
                                    os.remove(u.photo)
                            except Exception:
                                logging.exception('Falha ao remover foto do usuário')
                            ok = delete_user(u.id)
                            if ok:
                                st.success('Usuário excluído com sucesso.')
                                # Se o usuário excluído for o que está logado, encerrar sessão e forçar rerun.
                                try:
                                    if st.session_state.get('user_id') == u.id:
                                        st.session_state.user_id = None
                                        st.stop()
                                    else:
                                        st.stop()
                                except Exception:
                                    st.stop()
                            else:
                                st.error('Falha ao excluir usuário.')


if __name__ == '__main__':
    try:
        logging.info("Starting Gestão Infantil app")
        main()
    except Exception:
        logging.exception("Unhandled exception running app")
        traceback.print_exc(file=sys.stderr)
        raise
