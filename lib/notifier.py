
"""
Daily notifier: send emails for upcoming vencimentos (due payments)
To run: streamlit run app.py OR schedule `python -m lib.notifier` as a cronjob
"""

import os, datetime, smtplib
from email.message import EmailMessage
from lib import db

def get_upcoming(days:int=3):
    hoje = datetime.date.today()
    limite = hoje + datetime.timedelta(days=days)
    rows = db.query("SELECT m.*, u.email as resp_email FROM movimentos m LEFT JOIN users u ON u.id=m.responsavel_user_id WHERE m.vencimento IS NOT NULL AND date(m.vencimento) BETWEEN ? AND ?", (str(hoje), str(limite)))
    return rows

def send_email(to:str, subject:str, body:str, smtp_conf:dict):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_conf.get("from", smtp_conf["user"])
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP_SSL(smtp_conf["host"], smtp_conf.get("port",465)) as s:
        s.login(smtp_conf["user"], smtp_conf["password"])
        s.send_message(msg)

def main():
    import streamlit as st
    smtp_conf = st.secrets.get("smtp", {})
    if not smtp_conf:
        print("SMTP não configurado.")
        return
    upcoming = get_upcoming()
    if not upcoming:
        print("Nenhum vencimento nos próximos dias.")
        return
    for r in upcoming:
        if not r.get("resp_email"):
            continue
        body = f"Olá, você é responsável pelo pagamento/recebimento:\n\n" \               f"ID {r['id']} | {r['descricao']} | Valor R$ {r['valor']:.2f}\n" \               f"Vencimento: {r['vencimento']} | Status: {r['status']}"
        send_email(r["resp_email"], "Aviso de vencimento", body, smtp_conf)
        print(f"Enviado para {r['resp_email']} movimento {r['id']}")

if __name__ == "__main__":
    main()
