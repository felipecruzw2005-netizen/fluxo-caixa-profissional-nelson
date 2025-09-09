
import streamlit as st
from passlib.hash import bcrypt
from lib import db, ui, auth, permissions as perms

def page():
    ui.header("assets/logo.png", "Usuários (Opcional)", "Cadastro e permissões simples")
    if st.session_state.user["role"] != "admin":
        st.warning("Apenas administradores podem gerenciar usuários.")
        return
    with st.expander("➕ Novo usuário"):
        name = st.text_input("Nome")
        email = st.text_input("Email")
        pwd = st.text_input("Senha", type="password")
        role = st.selectbox("Papel", ["user","admin"])
        if st.button("Criar"):
            db.execute("INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)", (name,email,bcrypt.hash(pwd),role))
            st.success("Usuário criado.")
    rows = db.query("SELECT id,name,email,role,created_at FROM users")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Permissões")
    rows = db.query("SELECT id,name,email FROM users")
    for r in rows:
        with st.container(border=True):
            st.markdown(f"**{r['name']}** — {r['email']}")
            p = perms.get_perms(r["id"])
            c1,c2,c3,c4,c5 = st.columns(5)
            a = c1.checkbox("Ver relatórios", value=bool(p["can_view_reports"]), key=f"vr{r['id']}")
            b0 = c2.checkbox("Criar movimentos", value=bool(p["can_create_movements"]), key=f"cm{r['id']}")
            b = c3.checkbox("Editar movimentos", value=bool(p["can_edit_movements"]), key=f"em{r['id']}")
            b2 = c4.checkbox("Apagar movimentos", value=bool(p["can_delete_movements"]), key=f"dm{r['id']}")
            d = c5.checkbox("Gerenciar usuários", value=bool(p["can_manage_users"]), key=f"gu{r['id']}")
            if st.button("Salvar", key=f"save{r['id']}"):
                db.execute("INSERT OR REPLACE INTO permissions (user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients) VALUES (?,?,?,?,?,?,?)",
                           (r["id"], int(a), int(b0), int(b), int(b2), int(d), 1))
                st.success("Permissões atualizadas.")
