
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from lib import db, ui

def proxima_data(vencimento:str|None, freq:str|None):
    # freq ex.: "07/mês" -> próximo dia 07
    hoje = date.today()
    if vencimento:
        try:
            d = pd.to_datetime(vencimento).date()
            if d >= hoje:
                return d
        except:
            pass
    if freq and "/mês" in str(freq):
        dia = int(str(freq).split("/")[0])
        ano, mes = hoje.year, hoje.month
        cand = date(ano, mes, min(dia, 28))
        if cand < hoje:
            # próximo mês
            mes = 12 if mes==12 else mes+1
            ano = ano+1 if mes==1 else ano
            cand = date(ano, mes, min(dia, 28))
        return cand
    return None

def page():
    ui.header("assets/logo.png", "Projeção de Caixa", "30/60/90 dias")
    horizon = st.selectbox("Horizonte", [30,60,90], index=0)
    rows = db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id WHERE coalesce(status,'pendente') IN ('pendente') AND (deleted_at IS NULL)")
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Sem itens pendentes.")
        return
    # tenta inferir frequência a partir de observacao/categoria
    df["freq"] = df["observacao"].fillna("")
    df["prox_data"] = df.apply(lambda r: proxima_data(r.get("vencimento"), r.get("freq")), axis=1)
    df = df.dropna(subset=["prox_data"])
    df["dias"] = (df["prox_data"] - date.today()).apply(lambda d: d.days)
    df = df[df["dias"] <= horizon]
    if df.empty:
        st.info("Sem projeções no período.")
        return
    st.dataframe(df[["id","descricao","valor","tipo","prox_data","cliente","centro_custo","freq"]], use_container_width=True, hide_index=True)
    # resumo
    entradas = float(df[df["tipo"]=="entrada"]["valor"].sum())
    saidas = float(df[df["tipo"]=="saida"]["valor"].sum())
    saldo = entradas - saidas
    st.success(f"Previsto até {horizon}d — Entradas: R$ {entradas:,.2f} | Saídas: R$ {saidas:,.2f} | Saldo: R$ {saldo:,.2f}")
