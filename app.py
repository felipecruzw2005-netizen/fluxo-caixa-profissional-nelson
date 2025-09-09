import streamlit as st
from lib import db, ui

st.set_page_config(page_title="Fluxo de Caixa Pro", page_icon="💼", layout="wide")
db.bootstrap()

ui.header("assets/logo.png", "Fluxo de Caixa Pro", "Sistema financeiro enxuto")
st.markdown("""
Use o menu lateral para acessar:
- **Dashboard**
- **Movimentos**
- **Comprovantes**
- **Relatórios**
- **Usuários**
- **Planilha**
- **Contas a Pagar e Receber**
- **Importar Planilha**
- **Exportar Planilha**
""")
