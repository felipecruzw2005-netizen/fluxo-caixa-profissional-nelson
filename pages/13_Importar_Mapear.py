import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from lib import db

st.set_page_config(page_title="Importar Planilha (Mapear)", page_icon="📥", layout="wide")

FIELDS = ["data","descricao","categoria","tipo","valor","forma_pagamento","status","cliente","vencimento","responsavel_email","centro_custo","placa","observacao"]
EXTRA_FIELDS = ["freq_col"]  # ex.: "07/mês"

def _header():
    st.title("📥 Importar Planilha (Mapear)")
    st.caption("Suba o Excel/CSV uma vez por mês e edite só pelo sistema.")

def _col_choices(df: pd.DataFrame):
    cols = list(df.columns)
    labels = [f"(coluna {i+1})" for i in range(len(cols))]
    return ["(ignorar)"] + cols + labels, cols

def _get_cell(row, choice, cols):
    if not choice or choice == "(ignorar)":
        return None
    if choice in cols:
        return row[choice]
    if choice.startswith("(coluna "):
        i = int(choice.split()[1].strip(")")) - 1
        return row.iloc[i] if i < len(row) else None
    return row.get(choice)

def _parse_brl(x):
    if pd.isna(x): return None
    s = str(x).strip().replace("R$","").replace(" ","")
    s = s.replace(".","").replace(",",".")
    try:
        return float(s)
    except: return None

_header()

# --- CONTROLES BÁSICOS ---
c1, c2 = st.columns([2,1])
with c1:
    nome_lote = st.text_input("Nome do lote/mês", value=date.today().strftime("%Y-%m"))
with c2:
    mapping_preset = st.selectbox("Preset", ["(nenhum)","Financiamentos (foto)"])

up = st.file_uploader("Selecione o arquivo (Excel .xlsx ou .csv)", type=["xlsx","csv"], accept_multiple_files=False)

# GARANTIR QUE O BOTÃO SEMPRE APARECE
btn_cols = st.columns([1,1,6])
save_map = btn_cols[0].button("Salvar mapeamento")
go_import = btn_cols[1].button("Importar linhas", type="primary")

# Se não enviou arquivo, mostra instruções mas NÃO some com a página
if not up:
    st.info("Envie a planilha para mapear as colunas. Se não tem cabeçalho, use os rótulos '(coluna 1)', '(coluna 2)'.")
    st.stop()

# Ler o arquivo de forma segura
try:
    if up.name.lower().endswith(".csv"):
        df = pd.read_csv(up, dtype=str, keep_default_na=False)
    else:
        df = pd.read_excel(up, engine="openpyxl", dtype=str)
except Exception as e:
    st.error(f"Falha ao ler o arquivo: {e}")
    st.stop()

st.markdown("### Prévia da planilha")
st.dataframe(df.head(30), use_container_width=True, hide_index=True)

# PREENCHER MAPEAMENTO
st.markdown("### Mapeamento de colunas")
choices, cols = _col_choices(df)

defaults = {}
if mapping_preset == "Financiamentos (foto)":
    # 1=freq, 2=descricao, 3=valor, 4=placa, 5=observacao
    defaults = {
        "descricao": "(coluna 2)",
        "valor": "(coluna 3)",
        "placa": "(coluna 4)",
        "observacao": "(coluna 5)",
        "freq_col": "(coluna 1)",
        # outros ignorados
    }

mapping = {}
for f in FIELDS + EXTRA_FIELDS:
    idx = (choices.index(defaults[f]) if f in defaults and defaults[f] in choices else 0)
    mapping[f] = st.selectbox(f"{f} ↔", choices, index=idx, key=f"map_{f}")

if save_map:
    # Persistir em settings (opcional – simples)
    db.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (f"mapping:last", pd.Series(mapping).to_json()))
    st.success("Mapeamento salvo (settings:mapping:last).")

if not go_import:
    st.stop()

# --- IMPORTAÇÃO ---
batch_id = db.execute("INSERT INTO batches (name, period_label, created_by) VALUES (?,?,?)",
                      ("mapping:last", nome_lote, 0))

ok, fail = 0, 0
errors = []

for i, r in df.iterrows():
    rec = {f: _get_cell(r, mapping.get(f, "(ignorar)"), cols) for f in FIELDS}
    # freq -> observacao
    freq_val = _get_cell(r, mapping.get("freq_col", "(ignorar)"), cols)
    if freq_val:
        rec["observacao"] = (str(rec.get("observacao") or "") + " " + str(freq_val)).strip()

    # defaults
    tipo = (rec.get("tipo") or "saida").strip().lower()
    status = (rec.get("status") or "pendente").strip().lower()

    # valor
    v = _parse_brl(rec.get("valor"))
    if v is None:
        errors.append({"linha": int(i+2), "erro": "valor inválido", "descricao": rec.get("descricao")})
        fail += 1
        continue

    # cliente (resolve id)
    cliente_id = None
    if rec.get("cliente"):
        rows = db.query("SELECT id FROM clientes WHERE nome = ?", (str(rec["cliente"]).strip(),))
        cliente_id = rows[0]["id"] if rows else db.execute("INSERT INTO clientes (nome) VALUES (?)", (str(rec["cliente"]).strip(),))

    # responsável (opcional)
    resp_id, resp_nome = None, None

    try:
        db.execute(
            """INSERT INTO movimentos (data, descricao, categoria, forma_pagamento, tipo, valor, cliente_id, status, arquivo_path, vencimento, responsavel_user_id, responsavel_nome, centro_custo, placa, observacao, created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(rec.get("data") or ""),
                str(rec.get("descricao") or ""),
                str(rec.get("categoria") or ""),
                str(rec.get("forma_pagamento") or ""),
                tipo,
                float(v),
                cliente_id,
                status,
                None,
                str(rec.get("vencimento") or ""),
                resp_id,
                resp_nome,
                str(rec.get("centro_custo") or ""),
                str(rec.get("placa") or ""),
                str(rec.get("observacao") or ""),
                0,
            ),
        )
        ok += 1
    except Exception as e:
        errors.append({"linha": int(i+2), "erro": f"DB: {e}", "descricao": rec.get("descricao")})
        fail += 1

st.success(f"Lote **{nome_lote}** importado. OK: {ok} | Falhas: {fail}")

if errors:
    st.warning("Algumas linhas falharam. Baixe e corrija para reimportar apenas as problemáticas.")
    err_df = pd.DataFrame(errors)
    st.dataframe(err_df, use_container_width=True, hide_index=True)
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        err_df.to_excel(w, index=False, sheet_name="Erros")
    st.download_button("⬇️ Baixar erros (Excel)", data=out.getvalue(), file_name=f"errors_{nome_lote}.xlsx", use_container_width=True)
