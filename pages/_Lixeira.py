
import streamlit as st
import pandas as pd
from lib import db, ui, audit

def page():
    ui.header("assets/logo.png", "Lixeira (Restaurar itens)", "Soft-delete com restauração")
    rows = db.query("SELECT * FROM movimentos WHERE deleted_at IS NOT NULL ORDER BY datetime(deleted_at) DESC")
    if not rows:
        st.info("Lixeira vazia.")
        return
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    ids = st.multiselect("Selecione IDs para restaurar", df["id"].tolist())
    if st.button("Restaurar selecionados", type="primary"):
        for i in ids:
            db.execute("UPDATE movimentos SET deleted_at=NULL WHERE id=?", (int(i),))
            audit.log(st.session_state.user["id"], "restore", "movimentos", int(i), {})
        st.success(f"Restaurados: {len(ids)}")
