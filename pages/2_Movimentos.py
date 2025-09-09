import streamlit as st
from lib import db, ui, permissions as perms, storage

st.set_page_config(page_title="Movimentos", page_icon="💸", layout="wide")

with st.sidebar:
    if not perms.can(st.session_state.user, "can_create_movements"):
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

# Consulta base
sql = "SELECT * FROM movimentos WHERE deleted_at IS NULL"
params = []

if data_ini:
    sql += " AND date(data) >= ?"
    params.append(str(data_ini))
if data_fim:
    sql += " AND date(data) <= ?"
    params.append(str(data_fim))
if tipo != "Todos":
    sql += " AND tipo = ?"
    params.append(tipo)

sql += " ORDER BY date(data) DESC"

rows = db.query(sql, tuple(params))

# Exibição em tabela
st.dataframe(rows, use_container_width=True)

# Botão para adicionar novo movimento (se permitido)
if perms.can(st.session_state.user, "can_create_movements"):
    with st.expander("➕ Adicionar movimento", expanded=False):
        with st.form("novo_mov"):
            data = st.date_input("Data")
            descricao = st.text_input("Descrição")
            categoria = st.text_input("Categoria")
            valor = st.number_input("Valor", step=0.01)
            tipo = st.selectbox("Tipo", ["entrada", "saida"])
            status = st.selectbox("Status", ["pendente", "confirmado", "pago"])
            arquivo = st.file_uploader("Comprovante", type=["png", "jpg", "jpeg", "pdf"])

            submitted = st.form_submit_button("Salvar")
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
                        tipo,
                        valor,
                        status,
                        path,
                        st.session_state.user["id"],
                    ),
                )
                st.success("Movimento adicionado com sucesso!")
                st.experimental_rerun()
