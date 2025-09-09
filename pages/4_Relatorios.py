
import streamlit as st
import pandas as pd
from lib import db, ui, filters, reporting, storage

def page():
    ui.header("assets/logo.png", "Relatórios", "Exportações com marca")
    rows = db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id ORDER BY date(m.data) ASC")
    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Sem dados para relatório.")
        return
    f = filters.filtros_sidebar(df)
    df_f = filters.aplicar_filtros(df, f)
    entradas = float(df_f[df_f["tipo"]=="entrada"]["valor"].sum())
    saidas = float(df_f[df_f["tipo"]=="saida"]["valor"].sum())
    saldo = entradas - saidas
    resumo = {"Entradas": f"R$ {entradas:,.2f}", "Saídas": f"R$ {saidas:,.2f}", "Saldo": f"R$ {saldo:,.2f}"}
    st.write("Pré-visualização")
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    st.caption("Inclui colunas: vencimento e responsável.")
    # Generate exports on the fly
    logo_bytes = storage.read_bytes("assets/logo.png")
    excel_bytes = reporting.to_excel(df_f, resumo)
    pdf_bytes = reporting.to_pdf(df_f, resumo, logo_bytes)
    st.session_state.exports = {"excel": excel_bytes, "pdf": pdf_bytes}
    st.download_button("⬇️ Exportar Excel", data=excel_bytes, file_name="relatorio_fluxo.xlsx", use_container_width=True)
    st.download_button("⬇️ Exportar PDF", data=pdf_bytes, file_name="relatorio_fluxo.pdf", use_container_width=True)
