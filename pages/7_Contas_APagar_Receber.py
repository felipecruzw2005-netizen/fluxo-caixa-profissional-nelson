
import streamlit as st
import pandas as pd
from datetime import date, datetime
from lib import db, ui, permissions as perms, audit

def load_df():
    rows = db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id ORDER BY date(coalesce(m.vencimento, m.data)) ASC")
    return pd.DataFrame(rows)

def badge_status(venc):
    if not venc:
        return "—"
    try:
        d = datetime.fromisoformat(venc).date()
    except:
        try:
            d = pd.to_datetime(venc).date()
        except:
            return "—"
    hoje = date.today()
    if d < hoje:
        return "🟥 Atrasado"
    elif (d - hoje).days <= 3:
        return "🟧 Vence em breve"
    else:
        return "🟩 OK"

def page():
    ui.header("assets/logo.png", "Contas a Pagar & Receber", "Quem paga o quê e quando")
    df = load_df()
    if df.empty:
        st.info("Nada por aqui ainda.")
        return
    col1, col2, col3, col4 = st.columns(4)
    tipo = col1.selectbox("Tipo", ["todos","entrada","saida"])
    resp = col2.text_input("Responsável (email/nome contém)")
    status = col3.selectbox("Status", ["todos","confirmado","pendente","estornado"])
    so_atrasados = col4.checkbox("Somente atrasados")
    df["badge"] = df["vencimento"].apply(badge_status)
    if tipo != "todos":
        df = df[df["tipo"]==tipo]
    if status != "todos":
        df = df[df["status"]==status]
    if resp.strip():
        r = resp.strip().lower()
        df = df[(df.get("responsavel_nome","").str.lower().str.contains(r, na=False)) | (df.get("responsavel_user_id").astype(str)==r)]
    if so_atrasados:
        df = df[df["badge"]=="🟥 Atrasado"]
    st.dataframe(df[["id","data","vencimento","descricao","tipo","valor","cliente","responsavel_nome","badge","status"]], use_container_width=True, hide_index=True)
