
import streamlit as st
from lib import ui, db

def get_setting(key, default=""):
    rows = db.query("SELECT value FROM settings WHERE key=?", (key,))
    return rows[0]["value"] if rows else default

def set_setting(key, value):
    db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))

def page():
    ui.header("assets/logo.png", "Configurações", "Identidade da empresa e padrões de notificação")
    empresa = st.text_input("Nome da empresa", value=get_setting("company_name",""))
    assinatura = st.text_area("Assinatura (HTML permitido)", value=get_setting("email_signature",""), height=120)
    periodo_padrao = st.text_input("Rótulo de período padrão", value=get_setting("default_period_label","próximos dias"))
    if st.button("Salvar", type="primary"):
        set_setting("company_name", empresa.strip())
        set_setting("email_signature", assinatura.strip())
        set_setting("default_period_label", periodo_padrao.strip())
        st.success("Configurações salvas.")
    st.caption("Placeholders disponíveis nos templates: {{empresa}}, {{assinatura}}, {{periodo}}")
