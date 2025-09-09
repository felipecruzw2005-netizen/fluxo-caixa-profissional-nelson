
import streamlit as st
from lib import ui, db, notify

BASE_STYLE = {
    "bg_header": "#0B0F17",
    "text_header": "#E5E7EB",
    "title": "Contas a vencer",
    "intro": "Olá {{nome}}, você tem {{quantidade}} conta(s) a vencer nos {{periodo}}.",
    "footer": "— {{empresa}}<br/>{{assinatura}}",
    "table_header_bg": "#101725",
    "table_header_text": "#E5E7EB",
}

def page():
    ui.header("assets/logo.png", "Assistente de Template (WYSIWYG)", "Monte um e-mail profissional sem escrever HTML")
    with st.form("wiz"):
        c1,c2 = st.columns(2)
        title = c1.text_input("Título", value=BASE_STYLE["title"])
        intro = c2.text_input("Introdução (suporta placeholders)", value=BASE_STYLE["intro"])
        bg_header = c1.color_picker("Cor do cabeçalho", value=BASE_STYLE["bg_header"])
        text_header = c2.color_picker("Texto do cabeçalho", value=BASE_STYLE["text_header"])
        th_bg = c1.color_picker("Cor da linha de títulos da tabela", value=BASE_STYLE["table_header_bg"])
        th_tx = c2.color_picker("Texto da linha de títulos", value=BASE_STYLE["table_header_text"])
        footer = st.text_area("Rodapé (suporta HTML e placeholders)", value=BASE_STYLE["footer"], height=120)
        name = st.text_input("Nome do novo template", placeholder="Ex: Corporate Branded 2")
        submitted = st.form_submit_button("Gerar e salvar", type="primary")
    if submitted:
        html = f"""
<table width='100%' cellpadding='0' cellspacing='0' style='font-family:Arial, sans-serif;background:#f6f7fb;padding:24px'>
  <tr><td align='center'>
    <table width='560' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden'>
      <tr>
        <td style='background:{bg_header};color:{text_header};padding:16px 20px;display:flex;align-items:center'>
          {{logo}} <strong style='font-size:16px;margin-left:10px'>{{empresa}}</strong>
        </td>
      </tr>
      <tr>
        <td style='padding:20px;color:#111'>
          <h2 style='margin:0 0 8px 0;color:#111'>{title}</h2>
          <p style='margin:0 0 16px 0'>{intro}</p>
          {{tabela_itens_style}}
          <p style='color:#666;margin-top:16px'>{footer}</p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
""".strip()
        # inject table style
        table_style = f"""
<style>
  .tbl th {{ background:{th_bg}; color:{th_tx}; padding:8px; text-align:left; }}
  .tbl td {{ border-bottom:1px solid #eee; padding:8px; }}
</style>
<table class='tbl' width='100%' cellpadding='0' cellspacing='0'>
  <thead><tr><th>ID</th><th>Descrição</th><th style='text-align:right'>Valor</th><th>Vencimento</th></tr></thead>
  <tbody>{{linhas}}</tbody>
</table>
"""
        html = html.replace("{tabela_itens_style}", table_style)
        # Save
        if not name.strip():
            st.error("Informe um nome para o template.")
        else:
            db.execute("INSERT OR REPLACE INTO email_templates (name, html) VALUES (?,?)", (name.strip(), html))
            st.success("Template salvo. Abra a página **Notificações** para testar.")
    st.markdown("---")
    st.caption("Dica: placeholders úteis → {{logo}}, {{empresa}}, {{nome}}, {{quantidade}}, {{periodo}}, {{tabela_itens}}, {{assinatura}}")
