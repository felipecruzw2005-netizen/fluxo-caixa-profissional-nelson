import streamlit as st
from lib import db, auth, ui

st.set_page_config(page_title="Fluxo de Caixa Pro", page_icon="💼", layout="wide")

# Bootstrap (cria tabelas na 1ª execução)
db.bootstrap()

# Autenticação simples (ajuste conforme seu auth)
auth.ensure_session()

ui.header("assets/logo.png", "Fluxo de Caixa Pro", "Dashboard financeiro enxuto")
st.markdown("""
Bem-vindo! Use o menu lateral para acessar:
- **Movimentos** (lançamentos e edição)
- **Comprovantes** (upload e galeria)
- **Projeção de Caixa** (30/60/90)
- **Relatório por Centro de Custo**
- **Importar Planilha (Mapear)**
- **Exportar Planilha**
""")
