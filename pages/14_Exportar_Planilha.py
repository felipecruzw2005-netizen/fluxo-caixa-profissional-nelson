import streamlit as st
import pandas as pd
from io import BytesIO
from lib import db, ui

st.set_page_config(page_title="Exportar Planilha", page_icon="📤", layout="wide")

ui.header("assets/logo.png", "Exportar Planilha", "Excel fiel ao que está no sistema")

rows = db.query("""
SELECT m.*, c.nome as cliente
FROM movimentos m
LEFT JOIN clientes c ON c.id=m.cliente_id
WHERE m.deleted_at IS NULL
ORDER BY COALESCE(NULLIF(m.data,''), m.created_at) DESC
""", ())

if not rows:
    st.info("Sem dados para exportar.")
    st.stop()

df = pd.DataFrame(rows)
st.dataframe(df.head(50), use_container_width=True, hide_index=True)

out = BytesIO()
with pd.ExcelWriter(out, engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="Planilha")

st.download_button("⬇️ Exportar Excel", data=out.getvalue(), file_name="planilha_fluxo.xlsx", use_container_width=True, type="primary")
