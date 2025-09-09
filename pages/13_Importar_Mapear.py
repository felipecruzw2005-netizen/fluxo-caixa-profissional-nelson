import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from lib import db, ui, audit

st.set_page_config(page_title="Importar Planilha", page_icon="📥", layout="wide")

FIELDS = ["data","descricao","categoria","tipo","valor","forma_pagamento","status","cliente","vencimento","responsavel_email","centro_custo","placa","observacao"]
EXTRA_FIELDS = ["freq_col"]  # ex.: "07/mês"
COLIDX_PREFIX = "__COLIDX_"

def save_mapping(name, mapping):
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (f"mapping:{name}", pd.Series(mapping).to_json()))

def load_mapping(name):
    rows = db.query("SELECT value FROM settings WHERE key=?", (f"mapping:{name}",))
    if rows and rows[0]["value"]:
        try:
            return pd.read_json(BytesIO(rows[0]["value"].encode())).to_dict()
        except Exception:
            return {}
    return {}

def col_choices(df):
    cols = list(df.columns)
    labels = [f"(coluna {i+1})" for i in range(len(cols))]
    return list(cols) + labels, cols

def get_cell(row, mapping_value, cols):
    if not mapping_value or mapping_value == "(ignorar)":
        return None
    if mapping_value in cols:
        return row[mapping_value]
    if mapping_value.startswith("(coluna "):
        i = int(mapping_value.split()[1].strip(")")) - 1
        return row.iloc[i] if i < len(row) else None
    return row.get(mapping_value)

def parse_valor_brl(x):
    if pd.isna(x): return None
    s = str(x).strip().replace("R$","").replace(" ","")
    s = s.replace(".","").replace(",",".")
    try:
        return float(s)
    except Exception:
        return None

ui.header("assets/logo.png", "Importar Planilha (Mapear)", "Suba 1x/mês, o resto edita no sistema")

nome_lote = st.text_input("Nome do lote/mês", value=date.today().strftime("%Y-%m"))
mapping_name = st.text_input("Nome do mapeamento", value="padrao")

up = st.file_uploader("Selecione o arquivo (Excel .xlsx ou .csv)", type=["xlsx","csv"], accept_multiple_files=False)
if not up:
    st.info("Envie sua planilha para aparecer o mapeamento. Dica: se não tem cabeçalho, use os rótulos “(coluna 1)”, “(coluna 2)”.")
    st.stop()

# leitura segura
try:
    if up.name.lower().endswith(".csv"):
        df = pd.read_csv(up, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(up, engine="openpyxl", dtype=str)
except Exception as e:
    st.error(f"Falha ao ler o arquivo: {e}")
    st.stop()

st.write("Prévia da planilha:")
st.dataframe(df.head(30), use_container_width=True, hide_index=True)

st.markdown("### Mapeamento de colunas")
choices, cols = col_choices(df)
defaults = load_mapping(mapping_name)

# Preset rápido (igual à planilha da foto: 1=freq, 2=descricao, 3=valor, 4=placa, 5=observacao)
if st.button("Aplicar preset: Financiamentos (foto)"):
    defaults = {
        "descricao": "(coluna 2)",
        "valor": "(coluna 3)",
        "placa": "(coluna 4)",
        "observacao": "(coluna 5)",
        "freq_col": "(coluna 1)",
        # demais ignorados
    }

mapping = {}
for f in FIELDS + EXTRA_FIELDS:
    default_choice = defaults.get(f, "(ignorar)")
    opts = ["(ignorar)"] + choices
    idx = opts.index(default_choice) if default_choice in opts else 0
    mapping[f] = st.selectbox(f"{f} ↔", opts, index=idx, key=f"map_{f}")

c1,c2 = st.columns(2)
with c1:
    if st.button("Salvar mapeamento"):
        save_mapping(mapping_name, mapping)
        st.success("Mapeamento salvo para reuso.")
with c2:
    go = st.button("Importar linhas", type="primary")

if not go:
    st.stop()

# Importa
batch_id = db.execute("INSERT INTO batches (name, period_label, created_by) VALUES (?,?,?)",
                      (mapping_name, nome_lote, st.session_state.user["id"]))
ok, fail = 0, 0
errors = []

for i, r in df.iterrows():
    rec = {f: get_cell(r, mapping.get(f, "(ignorar)"), cols) for f in FIELDS}
    # anexa freq
    freq_val = get_cell(r, mapping.get("freq_col","(ignorar)"), cols)
    if freq_val:
        rec["observacao"] = (str(rec.get("observacao") or "") + " " + str(freq_val)).strip()

    # defaults
    rec["tipo"] = (rec.get("tipo") or "saida").strip().lower()
    rec["status"] = (rec.get("status") or "pendente").strip().lower()

    # valor
    v = parse_valor_brl(rec.get("valor"))
    if v is None:
        errors.append({"linha": int(i+2), "erro": "valor inválido", "descricao": rec.get("descricao")})
        fail += 1
        continue

    # cliente
    cliente_id = None
    if rec.get("cliente"):
        rows = db.query("SELECT id FROM clientes WHERE nome=?", (str(rec["cliente"]).strip(),))
        cliente_id = rows[0]["id"] if rows else db.execute("INSERT INTO clientes (nome) VALUES (?)",(str(rec["cliente"]).strip(),))

    # responsável
    resp_email = str(rec.get("responsavel_email") or "").strip().lower()
    resp = db.query("SELECT id,name FROM users WHERE email=?", (resp_email,)) if resp_email else []
    resp_id = resp[0]["id"] if resp else None
    resp_nome = resp[0]["name"] if resp else (resp_email if resp_email else None)

    try:
        db.execute("""INSERT INTO movimentos (data, descricao, categoria, forma_pagamento, tipo, valor, cliente_id, status, arquivo_path, vencimento, responsavel_user_id, responsavel_nome, centro_custo, placa, observacao, created_by)
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (str(rec.get("data") or ""), str(rec.get("descricao") or ""), str(rec.get("categoria") or ""),
                    str(rec.get("forma_pagamento") or ""), rec["tipo"], float(v), cliente_id, rec["status"],
                    None, str(rec.get("vencimento") or ""), resp_id, resp_nome,
                    str(rec.get("centro_custo") or ""), str(rec.get("placa") or ""), str(rec.get("observacao") or ""),
                    st.session_state.user["id"]))
        ok += 1
    except Exception as e:
        errors.append({"linha": int(i+2), "erro": f"DB: {e}", "descricao": rec.get("descricao")})
        fail += 1

audit.log(st.session_state.user["id"], "batch_import", "movimentos", batch_id, {"ok":ok,"fail":fail,"lote":nome_lote})
st.success(f"Lote **{nome_lote}** importado. OK: {ok} | Falhas: {fail}")

if errors:
    st.warning("Algumas linhas falharam. Baixe os erros, corrija e re
