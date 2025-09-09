import streamlit as st, pandas as pd
from lib import db, ui, storage

st.set_page_config(page_title="Comprovantes", page_icon="🧾", layout="wide")
ui.header("assets/logo.png", "Comprovantes", "Upload, galeria e download")

# Upload
with st.expander("Enviar novo comprovante"):
    up = st.file_uploader("Arquivo (png, jpg, jpeg, pdf)", type=["png","jpg","jpeg","pdf"])
    mov_id = st.number_input("ID do movimento (opcional)", min_value=0, step=1)
    if st.button("Enviar", type="primary") and up:
        path = storage.save_upload(up)
        if mov_id:
            db.execute("UPDATE movimentos SET arquivo_path=? WHERE id=?", (path, int(mov_id)))
        st.success("Arquivo enviado.")
        st.experimental_rerun()

# Listagem
rows = db.query("""SELECT id, descricao, arquivo_path FROM movimentos 
                   WHERE arquivo_path IS NOT NULL AND deleted_at IS NULL 
                   ORDER BY id DESC LIMIT 300""", ())
df = pd.DataFrame(rows)
if df.empty:
    st.info("Nenhum comprovante.")
else:
    for _, r in df.iterrows():
        c1,c2,c3 = st.columns([5,3,2])
        c1.write(f"**#{int(r['id'])}** — {r['descricao']}")
        url = storage.public_url(r["arquivo_path"])
        if str(r["arquivo_path"]).lower().endswith((".png",".jpg",".jpeg")):
            if url: c2.image(url, width=160)
            else:   c2.image(r["arquivo_path"], width=160)
        else:
            c2.write("PDF")
        if url:
            c3.download_button("Baixar", data=storage.read_bytes(r["arquivo_path"]), file_name=f"comprovante_{int(r['id'])}.{'pdf' if r['arquivo_path'].lower().endswith('pdf') else 'bin'}", use_container_width=True)
        else:
            c3.download_button("Baixar", data=storage.read_bytes(r["arquivo_path"]), file_name=f"comprovante_{int(r['id'])}.bin", use_container_width=True)
