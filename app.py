import streamlit as st
from lib import db, ui, permissions as perms

st.set_page_config(page_title="Fluxo de Caixa Pro", page_icon="💼", layout="wide")

# 1) Bootstrap: cria tabelas na 1ª execução (Postgres/SQLite)
db.bootstrap()

# 2) Fallback de sessão (independe do auth.ensure_session)
def _ensure_admin_user():
    rows = db.query("SELECT id, name, email, role FROM users WHERE email = ?", ("admin@example.com",))
    if not rows:
        # cria admin padrão
        from passlib.hash import pbkdf2_sha256
        pwd = pbkdf2_sha256.hash("admin")
        # Postgres/SQLite ambos aceitam esse insert via nosso db.execute (placeholders "?" serão normalizados)
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin@example.com", pwd, "admin"),
        )
        rows = db.query("SELECT id, name, email, role FROM users WHERE email = ?", ("admin@example.com",))
    return rows[0]

def _safe_ensure_session():
    # Tenta usar auth.ensure_session se existir; senão, cria sessão com admin padrão
    try:
        from lib import auth
        if hasattr(auth, "ensure_session"):
            auth.ensure_session()
            if "user" not in st.session_state or not st.session_state.user:
                # como fallback, injeta admin
                st.session_state.user = _ensure_admin_user()
        else:
            st.session_state.user = _ensure_admin_user()
    except Exception:
        st.session_state.user = _ensure_admin_user()

_safe_ensure_session()

# 3) Header e instruções
ui.header("assets/logo.png", "Fluxo de Caixa Pro", "Dashboard financeiro enxuto")
st.markdown("""
Use o menu lateral para acessar:

- **Movimentos** (lançamentos e edição)
- **Comprovantes** (upload e galeria)
- **Projeção de Caixa** (30/60/90 dias)
- **Relatório por Centro de Custo**
- **Importar Planilha (Mapear)**
- **Exportar Planilha**
""")

# 4) (Opcional) mostra quem está logado e permissões básicas
u = st.session_state.get("user")
if u:
    st.caption(f"Logado como: **{u.get('name','?')}** · {u.get('email','?')} · role: {u.get('role','user')}")
