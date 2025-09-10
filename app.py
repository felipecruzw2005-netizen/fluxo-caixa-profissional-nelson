# app.py (raiz) — Dashboard + esconde "Home" do menu multipage
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# === Import shim: garante acesso a lib/ ===
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import db  # agora funciona em qualquer ambiente

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# === Hack visual: esconde o primeiro item do menu multipage ("Home"/app) ===
# Funciona nas builds atuais do Streamlit Cloud. Se mudarem o DOM no futuro, me avisa que te mando o seletor novo.
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul li:first-child { display: none !important; }
</style>
""", unsafe_allow_html=True)

# === Sidebar: adiciona um link manual pro Dashboard (já que escondemos o "Home") ===
with st.sidebar:
    st.page_link("app.py", label="📊 Dashboard")  # volta sempre pra este arquivo
    st.markdown("---")

st.title("📊 Dashboard")

rows = db.query(
    "SELECT tipo, status, COALESCE(valor,0) AS valor FROM movimentos WHERE deleted_at IS NULL",
    (),
)
df = pd.DataFrame(rows)

total_ent = float(df[df["tipo"] == "entrada"]["valor"].sum()) if not df.empty else 0.0
total_sai = float(df[df["tipo"] == "saida"]["valor"].sum()) if not df.empty else 0.0
saldo = total_ent - total_sai

c1, c2, c3 = st.columns(3)
c1.metric("Entradas", f"R$ {total_ent:,.2f}")
c2.metric("Saídas", f"R$ {total_sai:,.2f}")
c3.metric("Saldo", f"R$ {saldo:,.2f}")

st.divider()

if df.empty:
    st.info("Sem dados no momento.")
else:
    resumo = df.groupby(["tipo", "status"])["valor"].sum().reset_index()
    st.dataframe(resumo, use_container_width=True, hide_index=True)
