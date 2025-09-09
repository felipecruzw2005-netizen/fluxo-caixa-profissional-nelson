
import streamlit as st
import pandas as pd
from lib import db, ui, permissions as perms, audit, reporting, storage
from io import BytesIO

TEMPLATE_COLS = ["data","descricao","categoria","tipo","valor","forma_pagamento","status","cliente","vencimento","responsavel_email"]

def load_users():
    return {u["email"]: u for u in db.query("SELECT id,name,email FROM users")}

def df_from_db():
    rows = db.query("SELECT m.id, m.data, m.descricao, m.categoria, m.tipo, m.valor, m.forma_pagamento, m.status, c.nome as cliente, m.vencimento, m.responsavel_user_id, m.responsavel_nome FROM movimentos m LEFT JOIN clientes c ON c.id=m.cliente_id ORDER BY date(m.data) DESC")
    return pd.DataFrame(rows)

def page():
    ui.header("assets/logo.png", "Planilha (edição tipo Excel)", "Edite e importe em massa")
    users = load_users()
    emails = list(users.keys())
    st.write("### Baixar template")
    template = pd.DataFrame(columns=TEMPLATE_COLS)
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        template.to_excel(w, index=False, sheet_name="Template")
    st.download_button("⬇️ Baixar Template Excel", data=b.getvalue(), file_name="template_fluxo.xlsx", use_container_width=True)

    st.write("### Importar planilha")
    up = st.file_uploader("Envie um Excel (aba única) seguindo o template", type=["xlsx","csv"])
    if up is not None:
        if up.name.lower().endswith(".csv"):
            df_imp = pd.read_csv(up)
        else:
            df_imp = pd.read_excel(up)
        # Normaliza colunas
        df_imp.columns = [c.strip().lower() for c in df_imp.columns]
        missing = [c for c in TEMPLATE_COLS if c not in df_imp.columns]
        if missing:
            st.error(f"Colunas ausentes: {missing}")
        else:
            st.success("Planilha válida. Revise/edite antes de salvar.")
            df_edit = st.data_editor(df_imp, use_container_width=True, num_rows="dynamic")
            if st.button("💾 Gravar na base", type="primary"):
                ok, fail = 0, 0
                for _, r in df_edit.iterrows():
                    # cliente
                    cliente_id = None
                    if pd.notna(r.get("cliente")) and str(r.get("cliente")).strip():
                        rows = db.query("SELECT id FROM clientes WHERE nome=?", (str(r["cliente"]).strip(),))
                        cliente_id = rows[0]["id"] if rows else db.execute("INSERT INTO clientes (nome) VALUES (?)",(str(r["cliente"]).strip(),))
                    # responsavel
                    resp_email = str(r.get("responsavel_email") or "").strip().lower()
                    resp_user = users.get(resp_email)
                    resp_id = resp_user["id"] if resp_user else None
                    resp_nome = resp_user["name"] if resp_user else (resp_email if resp_email else None)
                    try:
                        db.execute("""INSERT INTO movimentos (data, descricao, categoria, forma_pagamento, tipo, valor, cliente_id, status, vencimento, responsavel_user_id, responsavel_nome, created_by)
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                   (str(r.get("data")), str(r.get("descricao")), str(r.get("categoria")), str(r.get("forma_pagamento")), str(r.get("tipo")), float(r.get("valor")), cliente_id, str(r.get("status")), str(r.get("vencimento") or ""), resp_id, resp_nome, st.session_state.user["id"]))
                        ok += 1
                    except Exception as e:
                        fail += 1
                audit.log(st.session_state.user["id"], "bulk_import", "movimentos", None, {"ok": ok, "fail": fail})
                st.success(f"Importação concluída. Inseridos: {ok} | Falhas: {fail}")

    st.write("### Editar como planilha os lançamentos existentes")
    df = df_from_db()
    if df.empty:
        st.info("Sem dados para editar.")
        return
    # Campo de edição do responsável por linha
    df["responsavel_email"] = ""
    # Pre-fill se houver id
    user_map_by_id = {v["id"]: k for k,v in users.items()}
    df.loc[df["responsavel_user_id"].notna(), "responsavel_email"] = df.loc[df["responsavel_user_id"].notna(),"responsavel_user_id"].map(user_map_by_id)
    edited = st.data_editor(df, use_container_width=True, num_rows="dynamic", disabled=["id"])
    if st.button("💾 Salvar alterações em massa", type="primary"):
        count = 0
        for _, r in edited.iterrows():
            resp_email = str(r.get("responsavel_email") or "").strip().lower()
            resp_user = users.get(resp_email)
            resp_id = resp_user["id"] if resp_user else None
            resp_nome = resp_user["name"] if resp_user else (resp_email if resp_email else None)
            before = db.query("SELECT * FROM movimentos WHERE id=?", (int(r["id"]),))
            if not before: 
                continue
            db.execute("UPDATE movimentos SET data=?, descricao=?, categoria=?, tipo=?, valor=?, forma_pagamento=?, status=?, vencimento=?, responsavel_user_id=?, responsavel_nome=? WHERE id=?",
                       (str(r.get("data")), str(r.get("descricao")), str(r.get("categoria")), str(r.get("tipo")), float(r.get("valor")), str(r.get("forma_pagamento")), str(r.get("status")), str(r.get("vencimento") or ""), resp_id, resp_nome, int(r["id"])))
            db.execute("INSERT INTO movement_history (movimento_id, before_json, changed_by, action) VALUES (?,?,?,?)",
                       (int(r["id"]), json.dumps(before[0]), st.session_state.user["id"], "update"))
            count += 1
        audit.log(st.session_state.user["id"], "bulk_update", "movimentos", None, {"count": count})
        st.success(f"Atualizados: {count}")
