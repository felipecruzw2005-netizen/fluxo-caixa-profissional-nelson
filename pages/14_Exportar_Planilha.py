
import streamlit as st
import pandas as pd
from lib import db, ui

def page():
    ui.header("assets/logo.png", "Exportar Planilha", "Excel fiel ao que está no sistema")
    df = pd.DataFrame(db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id WHERE m.deleted_at IS NULL ORDER BY date(m.data) DESC"))
    if df.empty:
        st.info("Sem dados.")
        return
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)
    import io
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Planilha")
    st.download_button("⬇️ Exportar Excel", data=out.getvalue(), file_name="planilha_fluxo.xlsx", use_container_width=True)
