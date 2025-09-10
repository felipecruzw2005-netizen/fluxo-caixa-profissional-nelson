import streamlit as st
import pandas as pd
from lib import db, ui, permissions as perms, storage

st.set_page_config(page_title="Movimentos", page_icon="💸", layout="wide")

# ---------- Sessão segura (não depende do auth.ensure_session) ----------
def _ensure_user():
    u = st.session_state.get("user")
    if u:
        return u
    # tenta usar auth.ensure_session se existir
    try:
        from lib import auth
        if hasattr(auth, "ensure_session"):
            auth.ensure_session()
            u = st.session_state.get("user")
            if u:
                return u
    except Exception:
        pass
    # fallback: garante admin padrão
    rows = db.query("SELECT id, name, email, role FROM users WHERE email = ?", ("admin@example.com",))
    if not rows:
        from passlib.hash import pbkdf2_sha256
        pwd = pbkdf2_sha256.hash("admin")
        db.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
            ("Administrador", "admin@example.com", pwd, "admin"),
        )
        rows = db.query("SELECT id, name, email, role FROM users WHERE email = ?", ("admin@example.com",))
    st.session_state.user = rows[0]
    return st.session_state.user

u = _ensure_user()
# -----------------------------------------------------------------------

with st.sidebar:
    if not perms.can(u, "can_create_movements"):
        st.warning("Você não tem permissão para criar movimentos.")

st.title("📊 Movimentos")

# Filtros
with st.expander("Filtros", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input("Data inicial", value=None)
    with col2:
        data_fim = st.date_input("Data final", value=None)
    with col3:
        tipo = st.selectbox("Tipo", ["Todos", "entrada", "saida"])

# Consulta base (compatível com Postgres/SQLite)
sql = """
SELECT id, data, descricao, categoria, centro_custo, placa, observacao,
       forma_pagamento, tipo, valor, cliente_id, status, arquivo_path,
       vencimento, responsavel_user_id, responsavel_nome, created_by,
       to_char(created_at, 'YYYY-MM-DD') AS created_at_iso
FROM movimentos
WHERE deleted_at IS NULL
"""
params = []

if data_ini:
    sql += " AND COALESCE(NULLIF(data,''), to_char(created_at,'YYYY-MM-DD')) >= ?"
    params.append(str(data_ini))
if data_fim:
    sql += " AND COALESCE(NULLIF(data,''), to_char(created_at,'YYYY-MM-DD')) <= ?"
    params.append(str(data_fim))
if tipo != "Todos":
    sql += " AND tipo = ?"
    params.append(tipo)

sql += " ORDER BY COALESCE(NULLIF(data,''), to_char(created_at,'YYYY-MM-DD')) DESC"

rows = db.query(sql, tuple(params))
df = pd.DataFrame(rows)

# Exibição em tabela
st.dataframe(df, use_container_width=True)

# Botão para adicionar novo movimento (se permitido)
if perms.can(u, "can_create_movements"):
    with st.expander("➕ Adicionar movimento", expanded=False):
        with st.form("novo_mov"):
            data = st.date_input("Data")
            descricao = st.text_input("Descrição")
            categoria = st.text_input("Categoria")
            valor = st.number_input("Valor", step=0.01)
            tipo_sel = st.selectbox("Tipo", ["entrada", "saida"])
            status = st.selectbox("Status", ["pendente", "confirmado", "pago"])
            arquivo = st.file_uploader("Comprovante", type=["png", "jpg", "jpeg", "pdf"])

            submitted = st.form_submit_button("Salvar", type="primary")
            if submitted:
                path = None
                if arquivo:
                    path = storage.save_upload(arquivo)

                db.execute(
                    "INSERT INTO movimentos (data, descricao, categoria, tipo, valor, status, arquivo_path, created_by) VALUES (?,?,?,?,?,?,?,?)",
                    (
                        str(data),
                        descricao,
                        categoria,
                        tipo_sel,
                        float(valor or 0),
                        status,
                        path,
                        u["id"],
                    ),
                )
                st.success("Movimento adicionado com sucesso!")
                st.experimental_rerun()
