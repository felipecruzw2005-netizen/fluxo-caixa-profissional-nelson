#!/usr/bin/env python3
# CLI para enviar notificações de vencimento (use com cron)
import os, sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lib import notify, db

def main():
    days = int(os.environ.get("NOTIFY_DAYS_AHEAD", "3"))
    df = notify.fetch_due(days_ahead=days)
    groups = notify.group_by_responsavel(df)
    sent = 0
    for email, itens in groups.items():
        u = db.query("SELECT name FROM users WHERE email=?", (email,))
        nome = u[0]["name"] if u else email
        tmpl = os.environ.get('TEMPLATE_NAME')
        if tmpl and tmpl not in ['Corporate','Minimal','Dark']:
            html = notify.compose_email_html_custom(nome, itens, template_name=tmpl)
        else:
            html = notify.compose_email_html(nome, itens, template=(tmpl or 'Corporate'))
        body = notify.compose_email(nome, itens)
        notify.send_email(email, "Contas a vencer - Fluxo Pro", body, body_html=html)
        sent += 1
    print(f"[{datetime.utcnow().isoformat()}] Sent {sent} notification(s).")
if __name__ == "__main__":
    main()
