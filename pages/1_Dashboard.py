import streamlit as st
import pandas as pd
from lib import db

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")

# Consulta simples: soma entradas/saídas
rows = db.query(
    "SELECT tipo, status, COALESCE(valor,0) AS valor FROM movimentos WHERE deleted_at IS NULL",
    (),
)
df = pd.DataFrame(rows)

# Calcula totais
total_ent = float(df[df["tipo"] == "entrada"]["valor"].sum()) if not df.empty else 0.0
total_sai = float(df[df["tipo"] == "saida"]["valor"].sum()) if not df.empty else 0.0
saldo = total_ent - total_sai

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Entradas", f"R$ {total_ent:,.2f}")
c2.metric("Saídas", f"R$ {total_sai:,.2f}")
c3.metric("Saldo", f"R$ {saldo:,.2f}")

st.divider()

# Tabela resumo por tipo/status
if df.empty:
    st.info("Sem dados no momento.")
else:
    resumo = df.groupby(["tipo", "status"])["valor"].sum().reset_index()
    st.dataframe(resumo, use_container_width=True, hide_index=True)
