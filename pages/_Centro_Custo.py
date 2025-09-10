
import streamlit as st
import pandas as pd
from lib import db, ui, reporting

def page():
    ui.header("assets/logo.png", "Relatório por Centro de Custo", "Consolidação e export")
    rows = db.query("SELECT * FROM movimentos WHERE deleted_at IS NULL")
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Sem dados.")
        return
    df["centro_custo"] = df["centro_custo"].fillna("—")
    grp = df.groupby(["centro_custo","tipo"])["valor"].sum().reset_index()
    tabela = grp.pivot(index="centro_custo", columns="tipo", values="valor").fillna(0.0)
    tabela["saldo"] = tabela.get("entrada",0.0) - tabela.get("saida",0.0)
    st.dataframe(tabela, use_container_width=True)
    # export excel
    import io
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        tabela.to_excel(w, sheet_name="Centro de Custo")
        df.to_excel(w, index=False, sheet_name="Detalhado")
    st.download_button("⬇️ Exportar Excel", data=out.getvalue(), file_name="relatorio_centro_custo.xlsx", use_container_width=True)
