
import streamlit as st
from passlib.hash import bcrypt
from . import db
from . import permissions as perms
from datetime import datetime, timedelta
import uuid

def ensure_admin():
    users = db.query("SELECT * FROM users")
    if not users:
        pwd = bcrypt.hash("admin")
        admin_id = db.execute("INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,?)",
                   ("Admin","admin@example.com",pwd,"admin"))
        db.execute("INSERT OR REPLACE INTO permissions (user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients) VALUES (?,?,?,?,?,?,?)",
                   (admin_id,1,1,1,1,1,1))

def login_form():
    st.sidebar.subheader("Acesso")
    email = st.sidebar.text_input("Email")
    pwd = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar", use_container_width=True):
        rows = db.query("SELECT * FROM users WHERE email=?", (email,))
        if rows and bcrypt.verify(pwd, rows[0]["password_hash"]):
            st.session_state.user = {"id": rows[0]["id"], "name": rows[0]["name"], "role": rows[0]["role"]}
            st.sidebar.success("Bem-vindo, " + rows[0]["name"])
        else:
            st.sidebar.error("Credenciais inválidas")

def require_auth():
    if "user" not in st.session_state:
        st.session_state.user = None
    if st.session_state.user is None:
        login_form()
        st.stop()

def forgot_password_ui():
    st.sidebar.markdown("—")
    with st.sidebar.expander("Esqueci a senha"):
        email = st.text_input("Email de cadastro", key="fp_email")
        if st.button("Gerar token"):
            u = db.query("SELECT * FROM users WHERE email=?", (email,))
            if not u:
                st.warning("Email não encontrado.")
            else:
                import uuid, datetime
                token = uuid.uuid4().hex
                exp = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
                db.execute("INSERT INTO password_resets (user_id, token, expires_at) VALUES (?,?,?)", (u[0]["id"], token, exp))
                st.success("Token gerado! Guarde com segurança.")
                st.code(token)

                # Envia por e-mail se houver SMTP configurado em st.secrets["smtp"]
                try:
                    smtp = st.secrets.get("smtp", {})
                    if smtp and smtp.get("host"):
                        import smtplib
                        from email.message import EmailMessage
                        msg = EmailMessage()
                        msg["Subject"] = "Token de Redefinição de Senha"
                        msg["From"] = smtp.get("from", smtp.get("user"))
                        msg["To"] = email
                        msg.set_content(f"Seu token: {token}\nVálido até: {exp}")
                        with smtplib.SMTP_SSL(smtp["host"], smtp.get("port", 465)) as s:
                            s.login(smtp["user"], smtp["password"])
                            s.send_message(msg)
                        st.info("Token enviado por e-mail.")
                except Exception as e:
                    st.caption("Não foi possível enviar por e-mail; exibindo token aqui.")

        st.markdown("---")
        st.caption("Já tem o token?")
        email2 = st.text_input("Email", key="rp_email")
        token2 = st.text_input("Token")
        newpwd = st.text_input("Nova senha", type="password")
        if st.button("Redefinir senha"):
            u = db.query("SELECT * FROM users WHERE email=?", (email2,))
            if not u:
                st.error("Email inválido.")
            else:
                import datetime
                rows = db.query("SELECT * FROM password_resets WHERE user_id=? AND token=?", (u[0]["id"], token2))
                if not rows:
                    st.error("Token inválido.")
                else:
                    exp = rows[0]["expires_at"]
                    if datetime.datetime.fromisoformat(exp) < datetime.datetime.utcnow():
                        st.error("Token expirado.")
                    else:
                        db.execute("UPDATE users SET password_hash=? WHERE id=?", (bcrypt.hash(newpwd), u[0]["id"]))
                        st.success("Senha atualizada. Faça login.")
