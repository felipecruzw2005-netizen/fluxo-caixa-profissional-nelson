import streamlit as st, pandas as pd
from lib import db, ui

st.set_page_config(page_title="Planilha", page_icon="📑", layout="wide")
ui.header("assets/logo.png", "Planilha (edição)", "Edite como Excel e salve no banco")

rows = db.query(
    """
    SELECT id, data, descricao, categoria, forma_pagamento, tipo, valor, status, vencimento,
           centro_custo, placa, observacao,
           to_char(created_at, 'YYYY-MM-DD') AS created_at_iso
    FROM movimentos
    WHERE deleted_at IS NULL
    ORDER BY COALESCE(NULLIF(data,''), to_char(created_at, 'YYYY-MM-DD')) DESC
    LIMIT 500
    """,
    (),
)

df = pd.DataFrame(rows)
if df.empty:
    st.info("Sem dados.")
    st.stop()

edited = st.data_editor(df, use_container_width=True, num_rows="dynamic")
if st.button("💾 Salvar alterações", type="primary"):
    # aplica diffs simples (id obrigatório)
    for _, r in edited.iterrows():
        db.execute("""UPDATE movimentos SET data=?, descricao=?, categoria=?, forma_pagamento=?, tipo=?, valor=?, status=?, vencimento=?, centro_custo=?, placa=?, observacao=? WHERE id=?""",
                   (str(r["data"] or ""), str(r["descricao"] or ""), str(r["categoria"] or ""), str(r["forma_pagamento"] or ""),
                    str(r["tipo"] or "saida"), float(r["valor"] or 0), str(r["status"] or "pendente"), str(r["vencimento"] or ""),
                    str(r["centro_custo"] or ""), str(r["placa"] or ""), str(r["observacao"] or ""), int(r["id"])))
    st.success("Planilha salva.")
    st.experimental_rerun()
