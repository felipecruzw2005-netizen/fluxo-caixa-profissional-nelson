import streamlit as st, pandas as pd, io
from lib import db, ui

st.set_page_config(page_title="Relatórios", page_icon="📈", layout="wide")
ui.header("assets/logo.png", "Relatórios", "Consolidações e exportações")

rows = db.query("""SELECT m.*, c.nome AS cliente FROM movimentos m
                   LEFT JOIN clientes c ON c.id=m.cliente_id
                   WHERE m.deleted_at IS NULL""", ())
df = pd.DataFrame(rows)

if df.empty:
    st.info("Sem dados.")
    st.stop()

aba = st.selectbox("Tipo de relatório", ["Por Cliente","Por Categoria","Por Centro de Custo","Detalhado"])
if aba == "Detalhado":
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    key = {"Por Cliente":"cliente", "Por Categoria":"categoria", "Por Centro de Custo":"centro_custo"}[aba]
    df[key] = df[key].fillna("—")
    g = df.groupby([key,"tipo"])["valor"].sum().reset_index()
    piv = g.pivot(index=key, columns="tipo", values="valor").fillna(0.0)
    piv["saldo"] = piv.get("entrada",0.0) - piv.get("saida",0.0)
    st.dataframe(piv, use_container_width=True)

buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    df.to_excel(w, index=False, sheet_name="Detalhado")
st.download_button("⬇️ Exportar Excel (Detalhado)", data=buf.getvalue(), file_name="relatorio.xlsx", use_container_width=True)
