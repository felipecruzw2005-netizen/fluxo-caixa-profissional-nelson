import streamlit as st, pandas as pd
from passlib.hash import pbkdf2_sha256
from lib import db, ui

st.set_page_config(page_title="Usuários", page_icon="👥", layout="wide")
ui.header("assets/logo.png", "Usuários", "Gerenciamento simples")

with st.expander("Adicionar usuário"):
    name = st.text_input("Nome")
    email = st.text_input("E-mail")
    pwd = st.text_input("Senha", type="password")
    role = st.selectbox("Papel", ["user","admin"])
    if st.button("Criar", type="primary"):
        if not (name and email and pwd):
            st.error("Preencha nome, e-mail e senha.")
        else:
            db.execute("INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)",
                       (name, email, pbkdf2_sha256.hash(pwd), role))
            st.success("Usuário criado.")
            st.experimental_rerun()

rows = db.query("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC", ())
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
