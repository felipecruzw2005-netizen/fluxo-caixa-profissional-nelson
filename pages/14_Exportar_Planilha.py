import streamlit as st
import pandas as pd
from io import BytesIO
from lib import db

st.set_page_config(page_title="Exportar Planilha", page_icon="📤", layout="wide")

st.title("📤 Exportar Planilha")
st.caption("Gera um Excel com exatamente o que está no banco.")

rows = db.query(
    """
    SELECT m.id, m.data, m.descricao, m.categoria, m.forma_pagamento, m.tipo, m.valor, m.status, m.vencimento,
           m.centro_custo, m.placa, m.observacao, c.nome AS cliente,
           to_char(m.created_at, 'YYYY-MM-DD') AS created_at_iso
    FROM movimentos m
    LEFT JOIN clientes c ON c.id = m.cliente_id
    WHERE m.deleted_at IS NULL
    ORDER BY COALESCE(NULLIF(m.data,''), to_char(m.created_at,'YYYY-MM-DD')) DESC
    """,
    (),
)

df = pd.DataFrame(rows)
if df.empty:
    st.info("Sem dados para exportar.")
else:
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Planilha")
    st.download_button("⬇️ Exportar Excel", data=out.getvalue(), file_name="planilha_fluxo.xlsx", use_container_width=True, type="primary")
