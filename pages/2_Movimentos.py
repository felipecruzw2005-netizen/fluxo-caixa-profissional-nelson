
import streamlit as st
import pandas as pd
from lib import db, ui, filters, storage, permissions as perms, audit
from datetime import date

def form_novo():
    with st.expander("➕ Novo lançamento", expanded=False):
        
    if not perms.can(st.session_state.user, "can_create_movements"):
        st.warning("Você não possui permissão para criar lançamentos.")
        return

        c1,c2,c3 = st.columns(3)
        data = c1.date_input("Data", value=date.today())
        descricao = c2.text_input("Descrição")
        categoria = c3.text_input("Categoria")
        c4,c5,c6 = st.columns(3)
        tipo = c4.selectbox("Tipo", ["entrada","saida"])
        valor = c5.number_input("Valor (R$)", min_value=0.0, step=50.0, format="%.2f")
        forma = c6.selectbox("Forma de pagamento", ["pix","cartao","boleto","dinheiro","transferencia","outros"])
        c7,c8 = st.columns(2)
        status = c7.selectbox("Status", ["pendente","confirmado","pago","estornado"])
        cliente_nome = c8.text_input("Cliente (opcional)")
        c9,c10 = st.columns(2)
        vencimento = c9.date_input("Vencimento (opcional)")
        responsavel_email = c10.text_input("Quem paga (email do usuário) (opcional)")

        c11,c12,c13 = st.columns(3)
        centro_custo = c11.text_input("Centro de Custo (opcional)")
        placa = c12.text_input("Placa / Código (opcional)")
        observacao = c13.text_input("Observação (opcional)")
    
        up = st.file_uploader("Comprovante (opcional)", type=["png","jpg","jpeg","pdf"])
        if up is not None:
            st.caption("Pré-visualização:")
            if up.type.startswith("image/"):
                st.image(up, width=260)
            else:
                st.info("PDF anexado.")
        if st.button("Salvar", type="primary", use_container_width=True):
            cliente_id = None
            if cliente_nome:
                rows = db.query("SELECT id FROM clientes WHERE nome=?", (cliente_nome,))
                cliente_id = rows[0]["id"] if rows else db.execute("INSERT INTO clientes (nome) VALUES (?)",(cliente_nome,))
            arquivo_path = storage.save_upload(up) if up else None
            # resolve responsavel
            resp = db.query("SELECT id,name FROM users WHERE email=?", (responsavel_email.strip().lower(),)) if responsavel_email.strip() else []
            resp_id = resp[0]["id"] if resp else None
            resp_nome = resp[0]["name"] if resp else (responsavel_email.strip() or None)
            db.execute("""INSERT INTO movimentos (data, descricao, categoria, forma_pagamento, tipo, valor, cliente_id, status, arquivo_path, vencimento, responsavel_user_id, responsavel_nome, centro_custo, placa, observacao, created_by)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (str(data), descricao, categoria, forma, tipo, float(valor), cliente_id, status, arquivo_path, str(vencimento) if vencimento else None, resp_id, resp_nome, st.session_state.user["id"]))
            st.success("Lançamento criado.")

def page():
    ui.header("assets/logo.png", "Movimentos", "Cadastre, filtre e exporte")
    form_novo()
    rows = db.query("SELECT m.*, c.nome as cliente FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id ORDER BY date(m.data) DESC")
    df = pd.DataFrame(rows)
    f = filters.filtros_sidebar(df if not df.empty else pd.DataFrame([{"data":"2024-01-01","valor":0}]))
    df_f = filters.aplicar_filtros(df, f) if not df.empty else df
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    st.download_button("Exportar Excel", data=st.session_state.exports["excel"], file_name="relatorio.xlsx")
    st.download_button("Exportar PDF", data=st.session_state.exports["pdf"], file_name="relatorio.pdf")

    st.subheader("Gerenciar lançamentos")
    if df_f is not None and len(df_f)>0:
        for _, r in df_f.head(200).iterrows():
            with st.expander(f"[{r['id']}] {r['data']} — {r['descricao']} (R$ {r['valor']:.2f})", expanded=False):
                c1,c2,c3 = st.columns(3)
                if perms.can(st.session_state.user, "can_edit_movements"):
                    new_desc = c1.text_input("Descrição", value=str(r["descricao"]), key=f"ed_desc{r['id']}")
                    new_val = c2.number_input("Valor", value=float(r["valor"]), step=50.0, format="%.2f", key=f"ed_val{r['id']}")
                    new_status = c3.selectbox("Status", ["confirmado","pendente","estornado"], index=["confirmado","pendente","estornado"].index(r["status"]), key=f"ed_stat{r['id']}")
                    if st.button("Salvar alterações", key=f"save_{r['id']}"):
                        before = db.query("SELECT * FROM movimentos WHERE id=?", (int(r["id"]),))
                        db.execute("INSERT INTO movement_history (movimento_id, before_json, changed_by, action) VALUES (?,?,?,?)",
                                   (int(r["id"]), json.dumps(before[0]), st.session_state.user["id"], "update"))
                        db.execute("UPDATE movimentos SET descricao=?, valor=?, status=? WHERE id=?",
                                   (new_desc, float(new_val), new_status, int(r["id"])))
                        audit.log(st.session_state.user["id"], "update", "movimentos", int(r["id"]), {"fields":["descricao","valor","status"]})
                        st.success("Atualizado.")
                if perms.can(st.session_state.user, "can_delete_movements"):
                    if st.button("Excluir", key=f"del_{r['id']}"):
                        before = db.query("SELECT * FROM movimentos WHERE id=?", (int(r["id"]),))
                        db.execute("INSERT INTO movement_history (movimento_id, before_json, changed_by, action) VALUES (?,?,?,?)",
                                   (int(r["id"]), json.dumps(before[0]), st.session_state.user["id"], "delete"))
                        db.execute("UPDATE movimentos SET deleted_at=CURRENT_TIMESTAMP WHERE id=?", (int(r["id"]),))
                        audit.log(st.session_state.user["id"], "delete", "movimentos", int(r["id"]), {})
                        st.warning("Excluído.")
