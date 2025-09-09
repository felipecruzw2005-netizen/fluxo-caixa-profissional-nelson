
import streamlit as st
import pandas as pd
from lib import db, ui, storage
import os, base64

def page():
    ui.header("assets/logo.png", "Comprovantes", "Galeria e downloads")
    rows = db.query("SELECT id, data, descricao, tipo, valor, arquivo_path FROM movimentos WHERE arquivo_path IS NOT NULL ORDER BY date(data) DESC")
    if not rows:
        st.info("Nenhum comprovante anexado.")
        return
    for r in rows:
        with st.container(border=True):
            c1,c2,c3,c4 = st.columns([0.2,0.4,0.2,0.2])
            c1.write(str(r["data"]))
            c2.write(f"{r['descricao']} — R$ {r['valor']:.2f}")
            url = storage.public_url(r['arquivo_path'])
            if str(r["arquivo_path"]).lower().endswith((".png",".jpg",".jpeg")):
                if url:
                    c3.image(url, width=160)
                else:
                    c3.image(r['arquivo_path'], width=160)
            else:
                c3.write("PDF")
            bytes_data = storage.read_bytes(r["arquivo_path"])
            st.download_button("Baixar", data=bytes_data, file_name=os.path.basename(r["arquivo_path"]), key=f"dwn{r['id']}")
