
import streamlit as st
import pandas as pd
def filtros_sidebar(df: pd.DataFrame):
    st.sidebar.subheader("Filtros")
    date_col = pd.to_datetime(df["data"])
    min_d, max_d = date_col.min(), date_col.max()
    start, end = st.sidebar.date_input("Período", [min_d.date() if pd.notna(min_d) else None, end if (end:=max_d.date()) else None])
    status = st.sidebar.multiselect("Status", sorted([s for s in df["status"].dropna().unique()]))
    forma = st.sidebar.multiselect("Forma de pagamento", sorted([s for s in df["forma_pagamento"].dropna().unique()]))
    tipo = st.sidebar.multiselect("Tipo", ["entrada","saida"])
    cliente = st.sidebar.text_input("Cliente (contém)")
    min_val, max_val = st.sidebar.slider("Valor", float(df["valor"].min() if len(df) else 0), float(df["valor"].max() if len(df) else 1000), value=(float(df["valor"].min() if len(df) else 0), float(df["valor"].max() if len(df) else 1000)))
    q = st.sidebar.text_input("Busca")
    return {
        "periodo": (start, end),
        "status": set(status),
        "forma": set(forma),
        "tipo": set(tipo),
        "cliente": cliente.strip(),
        "valor_range": (min_val, max_val),
        "q": q.strip().lower()
    }

def aplicar_filtros(df: pd.DataFrame, f):
    if len(df)==0: return df
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"]).dt.date
    s,e = f["periodo"]
    if s and e:
        df = df[(df["data"]>=s) & (df["data"]<=e)]
    if f["status"]:
        df = df[df["status"].isin(f["status"])]
    if f["forma"]:
        df = df[df["forma_pagamento"].isin(f["forma"])]
    if f["tipo"]:
        df = df[df["tipo"].isin(f["tipo"])]
    if f["cliente"]:
        df = df[df.get("cliente","").astype(str).str.contains(f["cliente"], case=False, na=False)]
    vmin, vmax = f["valor_range"]
    df = df[(df["valor"]>=vmin) & (df["valor"]<=vmax)]
    if f["q"]:
        mask = False
        for col in ["descricao","categoria","forma_pagamento","status","tipo"]:
            if col in df.columns:
                mask = mask | df[col].astype(str).str.lower().str.contains(f["q"], na=False)
        df = df[mask]
    return df
