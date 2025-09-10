# main.py — arquivo de entrada mínimo
import streamlit as st

st.set_page_config(page_title="Fluxo de Caixa Pro", page_icon="💼", layout="wide")

# se a página existir, redireciona
try:
    st.switch_page("pages/1_Dashboard.py")
except Exception:
    st.title("Fluxo de Caixa Pro")
    st.error("Não encontrei pages/1_Dashboard.py. Verifique o nome/ordem na pasta pages/.")
