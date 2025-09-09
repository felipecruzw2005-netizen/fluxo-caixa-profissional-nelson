import streamlit as st, pandas as pd, datetime as dt
from lib import db, ui

st.set_page_config(page_title="Contas a Pagar e Receber", page_icon="🧮", layout="wide")
ui.header("assets/logo.png", "Contas a Pagar e Receber", "Pendências e recebimentos")

hoje = dt.date.today().isoformat()

tabs = st.tabs(["💸 A Pagar","💰 A Receber"])

# A Pagar
with tabs[0]:
    rows = db.query("""SELECT id, descricao, valor, vencimento, status FROM movimentos 
                       WHERE deleted_at IS NULL AND tipo='saida' AND COALESCE(status,'pendente') IN ('pendente') 
                       ORDER BY COALESCE(NULLIF(vencimento,''), '9999-12-31') ASC""", ())
    df = pd.DataFrame(rows)
    if df.empty: st.info("Nada a pagar."); 
    else: st.dataframe(df, use_container_width=True, hide_index=True)

# A Receber
with tabs[1]:
    rows = db.query("""SELECT id, descricao, valor, vencimento, status FROM movimentos 
                       WHERE deleted_at IS NULL AND tipo='entrada' AND COALESCE(status,'pendente') IN ('pendente') 
                       ORDER BY COALESCE(NULLIF(vencimento,''), '9999-12-31') ASC""", ())
    df = pd.DataFrame(rows)
    if df.empty: st.info("Nada a receber."); 
    else: st.dataframe(df, use_container_width=True, hide_index=True)
