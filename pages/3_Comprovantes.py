import sys
from pathlib import Path
import streamlit as st

# === Import shim ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import db

st.set_page_config(page_title="Comprovantes", page_icon="🧾", layout="wide")
st.title("🧾 Comprovantes")

rows = db.query("""
SELECT id, descricao, valor, status, arquivo_path, created_at
FROM movimentos
WHERE deleted_at IS NULL
  AND arquivo_path IS NOT NULL
ORDER BY created_at DESC
LIMIT 200
""", ())

if not rows:
    st.info("Nenhum comprovante enviado até agora.")
else:
    for r in rows:
        with st.expander(f"{r['descricao']} — R$ {r['valor']:,.2f} — {r['status']}"):
            if r.get("arquivo_path"):
                st.markdown(f"[📂 Baixar comprovante]({r['arquivo_path']})")
            else:
                st.warning("Sem arquivo vinculado.")
