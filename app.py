
import streamlit as st
from lib import auth, ui, permissions as perms, db
from importlib import import_module

st.set_page_config(page_title="Fluxo de Caixa Pro", page_icon="💸", layout="wide", initial_sidebar_state="expanded")

# Bootstrap
from lib import db as _db
_db.bootstrap()
auth.ensure_admin()

PAGES = {
    "Dashboard": "pages.1_Dashboard",
    "Movimentos": "pages.2_Movimentos",
    "Comprovantes": "pages.3_Comprovantes",
    "Relatórios": "pages.4_Relatorios",
    "Usuários (Opcional)": "pages.5_Usuarios",
    "Planilha": "pages.6_Planilha",
    "Contas a Pagar & Receber": "pages.7_Contas_APagar_Receber",
    "Notificações": "pages.8_Notificacoes",
    "Templates de E-mail": "pages.9_Templates_Email",
    "Assistente de Template (WYSIWYG)": "pages.B_WYSIWYG",
    "Configurações": "pages.A_Config",
    "Exportar Planilha": "pages.14_Exportar_Planilha",
    "Importar Planilha (Mapear)": "pages.13_Importar_Mapear",
    "Relatório por Centro de Custo": "pages.12_Centro_Custo",
    "Projeção de Caixa": "pages.11_Projecao",
    "Lixeira (Restaurar)": "pages.10_Lixeira"
}

with st.sidebar:
    st.image("assets/logo.png", width=120)
    st.title("Fluxo Pro")
    auth.login_form()
auth.forgot_password_ui()

if "user" not in st.session_state or st.session_state.user is None:
    st.stop()


allowed_pages = []
u = st.session_state.user
if perms.can(u, "can_view_reports"):
    allowed_pages.append("Relatórios")
if perms.can(u, "can_edit_movements"):
    allowed_pages.append("Movimentos")
# Todos podem ver Dashboard e Comprovantes
allowed_pages.extend([p for p in ["Dashboard","Comprovantes"] if p not in allowed_pages])
# Admin-only page:
if perms.can(u, "can_manage_users"):
    allowed_pages.append("Usuários (Opcional)")
page_name = st.sidebar.radio("Navegar", allowed_pages, label_visibility="collapsed", index=0)

module = import_module(PAGES[page_name])
module.page()
