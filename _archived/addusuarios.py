import streamlit as st
from passlib.hash import pbkdf2_sha256
from lib import db

st.set_page_config(page_title="Criar usuários iniciais", page_icon="👥")

st.title("👥 Criar usuários iniciais")

usuarios = [
    ("Nelson", "nelson.viracondo@gmail.com"),
    ("Luciana", "lucianadib.adm@gmail.com"),
    ("Augusto", "augusto.napol1@gmail.com"),
]

senha = "Napoli"
senha_hash = pbkdf2_sha256.hash(senha)

for nome, email in usuarios:
    row = db.query("SELECT id FROM users WHERE email = ?", (email,))
    if row:
        st.info(f"Usuário {email} já existe (id {row[0]['id']})")
    else:
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            (nome, email, senha_hash, "admin"),
        )
        st.success(f"Usuário {email} criado como ADMIN com sucesso!")
