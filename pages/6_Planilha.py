import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# === Import shim ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import db

st.set_page_config(page_title="Planilha", page_icon="📊", layout="wide")
st.title("📊 Planilha")

rows = db.query("""
SELECT id, data, descricao, categoria, forma_pagamento, tipo, valor, status,
       vencimento, centro_custo, placa, observacao, responsavel_nome
FROM movimentos
WHERE deleted_at IS NULL
ORDER BY COALESCE(NULLIF(data,''), to_char(created_at,'YYYY-MM-DD')) DESC
LIMIT 500
""", ())

df = pd.DataFrame(rows)

if df.empty:
    st.info("Nenhum movimento cadastrado ainda.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "📥 Exportar para Excel",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="planilha_fluxo.csv",
        mime="text/csv",
    )
