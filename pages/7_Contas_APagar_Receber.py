import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# === Import shim ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import db

st.set_page_config(page_title="Contas a Pagar e Receber", page_icon="✅❌", layout="wide")
st.title("✅❌ Contas a Pagar e Receber")

rows = db.query("""
SELECT id, descricao, valor, status, vencimento, responsavel_nome
FROM movimentos
WHERE deleted_at IS NULL
  AND (status = 'pendente' OR status = 'confirmado')
ORDER BY COALESCE(NULLIF(vencimento,''), to_char(created_at,'YYYY-MM-DD')) ASC
LIMIT 200
""", ())

df = pd.DataFrame(rows)

if df.empty:
    st.info("Nenhuma conta pendente no momento.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)
