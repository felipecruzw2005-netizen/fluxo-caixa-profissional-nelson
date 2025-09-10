
import streamlit as st
from lib import ui, notify, db
import pandas as pd

def page():
    ui.header("assets/logo.png", "Notificações por E-mail", "Avisos de vencimento (pendentes)")
    tpl = st.selectbox('Template', ['Corporate','Minimal','Dark'], index=0)
    
    tpl_names = [r['name'] for r in db.query('SELECT name FROM email_templates ORDER BY name ASC')]
    tpl_all = ['Corporate','Minimal','Dark'] + (tpl_names if tpl_names else [])
    tpl = st.selectbox('Template (inclui customizados)', tpl_all, index=0)
    days = st.number_input("Dias à frente", min_value=1, max_value=30, value=3, step=1)
    df = notify.fetch_due(days_ahead=int(days))
    
    # carregar configurações
    cfg = {r['key']: r['value'] for r in db.query('SELECT key,value FROM settings')}
    periodo_label = cfg.get('default_period_label', 'próximos dias')
    empresa = cfg.get('company_name', 'Fluxo de Caixa Pro')
    assinatura = cfg.get('email_signature', '')
    periodo_full = f'{int(days)} {periodo_label}'
    
    st.dataframe(df.drop(columns=["vencimento_dt","dias"], errors="ignore"), use_container_width=True, hide_index=True)
    st.markdown('Pré-visualização HTML do e-mail (primeiro destinatário):')
    prev_df = df.copy()
    preview_html = ''
    groups_prev = notify.group_by_responsavel(prev_df)
    if groups_prev:
        first_email = list(groups_prev.keys())[0]
        u = db.query('SELECT name FROM users WHERE email=?', (first_email,))
        nome_prev = u[0]['name'] if u else first_email
        preview_html = (notify.compose_email_html(nome_prev, groups_prev[first_email], template=tpl, logo_path='assets/logo.png') if tpl in ['Corporate','Minimal','Dark'] else notify.compose_email_html_custom(nome_prev, groups_prev[first_email], template_name=tpl, logo_path='assets/logo.png', periodo=periodo_full, empresa=empresa, assinatura=assinatura))
        st.components.v1.html(preview_html, height=380, scrolling=True)
    if st.button("Enviar e-mails agora", type="primary"):
        groups = notify.group_by_responsavel(df)
        if not groups:
            st.info("Nada a enviar.")
        else:
            enviados = 0
            for email, itens in groups.items():
                # busca nome
                u = db.query("SELECT name FROM users WHERE email=?", (email,))
                nome = u[0]["name"] if u else email
                body = notify.compose_email(nome, itens)
                try:
                    html = (notify.compose_email_html(nome, itens, template=tpl, logo_path='assets/logo.png') if tpl in ['Corporate','Minimal','Dark'] else notify.compose_email_html_custom(nome, itens, template_name=tpl, logo_path='assets/logo.png', periodo=periodo_full, empresa=empresa, assinatura=assinatura))
                    notify.send_email(email, "Contas a vencer - Fluxo Pro", body, st=st, body_html=html)
                    notify.log_email(email, "Contas a vencer - Fluxo Pro", tpl, len(itens), "sent")
                    enviados += 1
                except Exception as e:
                    st.error(f"Falha ao enviar para {email}: {e}")
            st.success(f"Notificações enviadas para {enviados} responsável(is).")

    st.markdown('---')
    st.subheader('Log de disparos')
    logs = db.query('SELECT created_at, to_email, subject, template, items_count, status, coalesce(error,"") as error FROM email_log ORDER BY id DESC LIMIT 200')
    st.dataframe(logs, use_container_width=True, hide_index=True)
