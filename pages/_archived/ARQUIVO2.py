
import streamlit as st
from lib import ui, db, notify

DEFAULT_HTML = """
<table width='100%' cellpadding='0' cellspacing='0' style='font-family:Arial, sans-serif;background:#f6f7fb;padding:24px'>
  <tr><td align='center'>
    <table width='560' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden'>
      <tr><td style='background:#0B0F17;color:#E5E7EB;padding:16px 20px;display:flex;align-items:center'>
        {{logo}} <strong style='font-size:16px;margin-left:10px'>Fluxo de Caixa Pro</strong>
      </td></tr>
      <tr><td style='padding:20px;color:#111'>
        <h2 style='margin:0 0 8px 0;color:#111'>Contas a vencer</h2>
        <p style='margin:0 0 16px 0'>Olá {{nome}}, você tem {{quantidade}} conta(s) a vencer (ou vencidas).</p>
        {{tabela_itens}}
        <p style='color:#666;margin-top:16px'>— Equipe Financeira</p>
      </td></tr>
    </table>
  </td></tr>
</table>
""".strip()

def page():
    ui.header("assets/logo.png", "Templates de E-mail", "Edite o HTML com placeholders e pré-visualize")
    st.caption("Placeholders disponíveis: {{logo}}, {{nome}}, {{quantidade}}, {{tabela_itens}}")
    # List existing templates
    rows = db.query("SELECT id, name, updated_at FROM email_templates ORDER BY name ASC")
    names = [r["name"] for r in rows]
    c1,c2 = st.columns([0.6,0.4])
    with c1:
        mode = st.radio("Ação", ["Criar novo", "Editar existente"], horizontal=True)
    if mode == "Criar novo":
        name = st.text_input("Nome do template", placeholder="Ex: Corporate Branded")
        html = st.text_area("HTML do template", value=DEFAULT_HTML, height=360)
        if st.button("Salvar template", type="primary"):
            if not name.strip():
                st.error("Informe um nome.")
            else:
                db.execute("INSERT OR REPLACE INTO email_templates (name, html) VALUES (?,?)", (name.strip(), html))
                st.success("Template salvo.")
    else:
        if not names:
            st.info("Não há templates. Crie um agora.")
        else:
            sel = st.selectbox("Escolha o template", names)
            rec = db.query("SELECT id, html FROM email_templates WHERE name=?", (sel,))[0]
            html = st.text_area("HTML do template", value=rec["html"], height=360, key="edit_html")
            if st.button("Atualizar", type="primary"):
                db.execute("UPDATE email_templates SET html=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (html, rec["id"]))
                st.success("Template atualizado.")
            st.markdown("---")
            st.write("Pré-visualização")
            # sample preview with fake items
            mock = [ {"id":101, "descricao":"Assinatura SaaS", "valor":199.90, "vencimento":"2025-09-10"},
                     {"id":102, "descricao":"Produção Vídeo", "valor":1500.00, "vencimento":"2025-09-12"} ]
            html_prev = notify.compose_email_html_custom("Time Financeiro", mock, template_name=sel, logo_path="assets/logo.png")
            st.components.v1.html(html_prev, height=420, scrolling=True)
    st.markdown("---")
    st.caption("Dica: defina um padrão nas Notificações.")


    st.markdown("### Criador rápido (Builder)")
    with st.expander("Gerar template com formulário (sem HTML)"):
        titulo = st.text_input("Título", "Contas a vencer")
        cor_fundo = st.color_picker("Cor de fundo", "#ffffff")
        cor_titulo = st.color_picker("Cor do título", "#111111")
        assinatura = st.text_input("Assinatura", "{{assinatura}}")
        if st.button("Gerar HTML base"):
            html_gen = f"""
            <div style='font-family:Arial,sans-serif;background:{cor_fundo};padding:20px;border-radius:12px'>
              {{logo}}<h2 style='color:{cor_titulo}'>{titulo}</h2>
              <p>Olá {{nome}}, você tem {{quantidade}} conta(s) a vencer no período {{periodo}}.</p>
              {{tabela_itens}}
              <p style='margin-top:16px'>{assinatura}</p>
            </div>
            """
            st.code(html_gen.strip(), language="html")
            st.session_state.generated_html = html_gen.strip()
        if "generated_html" in st.session_state:
            st.markdown("Pré-visualização")
            mock = [ {"id":201, "descricao":"Hospedagem", "valor":99.90, "vencimento":"2025-09-10"} ]
            html_prev = notify.render_template(st.session_state.generated_html, "Usuário Exemplo", mock, logo_path="assets/logo.png")
            st.components.v1.html(html_prev, height=300, scrolling=True)
            if st.button("Salvar template gerado"):
                name_gen = st.text_input("Nome do template gerado", "Novo Template")
                if name_gen:
                    db.execute("INSERT OR REPLACE INTO email_templates (name, html) VALUES (?,?)", (name_gen.strip(), st.session_state.generated_html))
                    st.success("Template salvo com sucesso.")
    
