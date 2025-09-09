
import streamlit as st
import pandas as pd
from lib import db, ui

def load_df():
    rows = db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id ORDER BY date(m.data) ASC")
    return pd.DataFrame(rows)

def page():
    ui.header("assets/logo.png", "Fluxo de Caixa", "Visão geral e indicadores")
    df = load_df()
    if df.empty:
        st.info("Nenhum movimento cadastrado ainda.")
        return
    entradas = float(df[df["tipo"]=="entrada"]["valor"].sum())
    saidas = float(df[df["tipo"]=="saida"]["valor"].sum())
    saldo = entradas - saidas
    ui.metric_cards({
        "Entradas": (f"R$ {entradas:,.2f}", "+", "#10B981"),
        "Saídas": (f"R$ {saidas:,.2f}", "-", "#EF4444"),
        "Saldo": (f"R$ {saldo:,.2f}", "", "#7C3AED")
    })
    df["data"] = pd.to_datetime(df["data"])
    monthly = df.groupby(df["data"].dt.to_period("M")).agg(receitas=("valor", lambda s: s[df.loc[s.index, "tipo"]=="entrada"].sum()),
                                                           despesas=("valor", lambda s: s[df.loc[s.index, "tipo"]=="saida"].sum())).reset_index()
    monthly["data"] = monthly["data"].astype(str)
    ui.line_chart(monthly, x="data", y=["receitas","despesas"], title="Evolução mensal")
    st.subheader("Últimos lançamentos")
    st.dataframe(df.sort_values("data", ascending=False).head(20)[["data","descricao","categoria","tipo","valor","status"]], use_container_width=True, hide_index=True)
