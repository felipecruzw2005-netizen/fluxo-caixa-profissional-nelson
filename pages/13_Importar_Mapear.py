
import streamlit as st
import pandas as pd
from lib import db, ui, audit
from io import BytesIO
from datetime import date

FIELDS = ["data","descricao","categoria","tipo","valor","forma_pagamento","status","cliente","vencimento","responsavel_email","centro_custo","placa","observacao"]
EXTRA_FIELDS = ["freq_col"]  # coluna onde pode vir padrões tipo "07/mês"

COLIDX_PREFIX = "__COLIDX_"  # para mapear por índice quando não há cabeçalho

def save_mapping(name, mapping):
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (f"mapping:{name}", pd.Series(mapping).to_json()))

def load_mapping(name):
    rows = db.query("SELECT value FROM settings WHERE key=?", (f"mapping:{name}",))
    if rows:
        try:
            return pd.read_json(BytesIO(rows[0]["value"].encode())).to_dict()
        except Exception:
            pass
    return {}

def col_choices(df):
    cols = list(df.columns)
    # também permitir escolher por índice
    idx = [f"{COLIDX_PREFIX}{i+1}" for i in range(len(cols))]
    labels = [f"(coluna {i+1})" for i in range(len(cols))]
    # retornar pares (label->value)
    choices = list(cols) + labels
    return choices, cols, idx, labels

def get_cell(row, mapping_value, cols):
    # mapping_value pode ser nome da coluna, rótulo '(coluna N)' ou __COLIDX_N
    if mapping_value is None or mapping_value == "(ignorar)":
        return None
    if mapping_value in cols:
        return row[mapping_value]
    if mapping_value.startswith(COLIDX_PREFIX):
        i = int(mapping_value.replace(COLIDX_PREFIX,"")) - 1
        return row.iloc[i] if i < len(row) else None
    if mapping_value.startswith("(coluna "):
        i = int(mapping_value.split()[1].strip(")")) - 1
        return row.iloc[i] if i < len(row) else None
    return row.get(mapping_value)

def parse_valor_brl(x):
    if pd.isna(x): return 0.0
    s = str(x).strip()
    s = s.replace("R$","").replace(" ","")
    # padrão brasileiro: milhar ponto, decimal vírgula
    s = s.replace(".","").replace(",",".")
    try:
        return float(s)
    except:
        # fallback para número direto
        try:
            return float(re.findall(r"[-+]?\d*\.?\d+", str(x).replace(",","."))[0])
        except:
            return None

def validate_row(rec):
    errors = []
    if not rec.get("descricao"):
        errors.append("descricao ausente")
    v = rec.get("valor")
    if v is None:
        errors.append("valor inválido")
    if rec.get("status") and str(rec["status"]).lower() not in ["pendente","confirmado","pago","estornado"]:
        errors.append(f"status inválido: {rec['status']}")
    if rec.get("tipo") and str(rec["tipo"]).lower() not in ["entrada","saida"]:
        errors.append(f"tipo inválido: {rec['tipo']}")
    return errors

def page():
    ui.header("assets/logo.png", "Importar Planilha (mapeamento)", "Suba 1x por mês e depois edite só pelo sistema")
    nome_lote = st.text_input("Nome do lote/mês", value=date.today().strftime("%Y-%m"))
    mapping_name = st.text_input("Nome do mapeamento", value="padrao")
    up = st.file_uploader("Planilha (xlsx/csv)", type=["xlsx","csv"])
    if up is None:
        st.info("Envie a planilha para mapear colunas (ex.: primeira coluna '07/mês', depois descrição, valor em BRL, placa/código, observação).")
        return
    df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
    st.write("Prévia da planilha:")
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)
    st.markdown("### Mapeie as colunas")
    choices, cols, idx_vals, idx_labels = col_choices(df)
    defaults = load_mapping(mapping_name)

    # Botão de preset baseado na foto (1a col: freq '07/mês', 2a: descricao, 3a: valor BRL, 4a: placa, 5a: observacao)
    if st.button("Aplicar preset: Financiamentos (foto)"):
        defaults = {
            "descricao": "(coluna 2)",
            "valor": "(coluna 3)",
            "placa": "(coluna 4)",
            "observacao": "(coluna 5)",
            "freq_col": "(coluna 1)",
            "tipo": "(ignorar)",
            "status": "(ignorar)",
            "categoria": "(ignorar)",
            "centro_custo": "(ignorar)",
            "data": "(ignorar)",
            "forma_pagamento": "(ignorar)",
            "cliente": "(ignorar)",
            "vencimento": "(ignorar)",
            "responsavel_email": "(ignorar)"
        }

    mapping = {}
    for f in FIELDS + EXTRA_FIELDS:
        default_choice = defaults.get(f, "(ignorar)")
        mapping[f] = st.selectbox(f"{f} ↔", ["(ignorar)"] + choices, index=(["(ignorar)"]+choices).index(default_choice) if default_choice in (["(ignorar)"]+choices) else 0)

    if st.button("Salvar mapeamento"):
        # traduz rótulos "(coluna N)" em __COLIDX_N para persistir
        norm = {k: (v if not v.startswith("(coluna ") else f"{COLIDX_PREFIX}{v.split()[1].strip(')')}") for k,v in mapping.items()}
        save_mapping(mapping_name, norm)
        st.success("Mapeamento salvo.")

    if st.button("Importar linhas", type="primary"):
        # carrega mapeamento normalizado
        norm = {k: (v if not v.startswith("(coluna ") else f"{COLIDX_PREFIX}{v.split()[1].strip(')')}") for k,v in mapping.items()}
        ok=0; fail=0
        errors_rows = []
        batch_id = db.execute("INSERT INTO batches (name, period_label, created_by) VALUES (?,?,?)", (mapping_name, nome_lote, st.session_state.user["id"]))
        for i, r in df.iterrows():
            rec = {}
            for f in FIELDS:
                val = get_cell(r, norm.get(f, "(ignorar)"), cols)
                rec[f] = val
            # freq -> observacao + futura projeção
            freq_val = get_cell(r, norm.get("freq_col","(ignorar)"), cols)
            if pd.notna(freq_val) and str(freq_val).strip():
                rec["observacao"] = (str(rec.get("observacao") or "") + " " + str(freq_val)).strip()
            # defaults inteligentes
            if not rec.get("tipo"): rec["tipo"] = "saida"
            if not rec.get("status"): rec["status"] = "pendente"
            if not rec.get("categoria"): rec["categoria"] = "Financiamento" if "financi" in str(rec.get("descricao","")).lower() else None
            if not rec.get("centro_custo"): rec["centro_custo"] = "Veículos" if rec.get("placa") else None
            # parse valor BRL
            v = parse_valor_brl(rec.get("valor"))
            rec["valor"] = v
            errs = validate_row(rec)
            if errs:
                errors_rows.append({"linha": int(i+2), "erro": "; ".join(errs), **{k: rec.get(k) for k in ["descricao","valor","placa","observacao"]}})
                fail += 1
                continue
            # cliente resolve
            cliente_id = None
            if rec.get("cliente"):
                rows = db.query("SELECT id FROM clientes WHERE nome=?", (str(rec["cliente"]).strip(),))
                cliente_id = rows[0]["id"] if rows else db.execute("INSERT INTO clientes (nome) VALUES (?)",(str(rec["cliente"]).strip(),))
            # responsavel resolve
            resp_email = str(rec.get("responsavel_email") or "").strip().lower()
            resp = db.query("SELECT id,name FROM users WHERE email=?", (resp_email,)) if resp_email else []
            resp_id = resp[0]["id"] if resp else None
            resp_nome = resp[0]["name"] if resp else (resp_email if resp_email else None)
            try:
                db.execute("""INSERT INTO movimentos (data, descricao, categoria, forma_pagamento, tipo, valor, cliente_id, status, arquivo_path, vencimento, responsavel_user_id, responsavel_nome, centro_custo, placa, observacao, created_by)
                              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (str(rec.get("data") or ""), str(rec.get("descricao") or ""), str(rec.get("categoria") or ""), str(rec.get("forma_pagamento") or ""), str(rec.get("tipo")), float(rec.get("valor") or 0), cliente_id, str(rec.get("status")), None, str(rec.get("vencimento") or ""), resp_id, resp_nome, str(rec.get("centro_custo") or ""), str(rec.get("placa") or ""), str(rec.get("observacao") or ""), st.session_state.user["id"]))
                ok+=1
            except Exception as e:
                errors_rows.append({"linha": int(i+2), "erro": f"DB: {e}", **{k: rec.get(k) for k in ["descricao","valor","placa","observacao"]}})
                fail+=1
        audit.log(st.session_state.user["id"], "batch_import_validated", "movimentos", batch_id, {"ok":ok,"fail":fail,"batch":nome_lote})
        st.success(f"Lote {nome_lote} importado. OK:{ok} | Falhas:{fail}")
        if errors_rows:
            st.warning("Algumas linhas falharam. Baixe o relatório de erros, corrija e reimporte apenas as linhas problemáticas.")
            err_df = pd.DataFrame(errors_rows)
            st.dataframe(err_df, use_container_width=True, hide_index=True)
            out = BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as w:
                err_df.to_excel(w, index=False, sheet_name="Erros")
            st.download_button("⬇️ Baixar erros em Excel", data=out.getvalue(), file_name=f"errors_{nome_lote}.xlsx", use_container_width=True)
