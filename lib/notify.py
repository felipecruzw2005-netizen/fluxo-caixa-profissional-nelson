
import os
import smtplib
import base64
from email.message import EmailMessage
from datetime import date, datetime, timedelta
import pandas as pd
from . import db

SMTP = {
    "host": os.environ.get("SMTP_HOST"),
    "port": int(os.environ.get("SMTP_PORT", "465")),
    "user": os.environ.get("SMTP_USER"),
    "password": os.environ.get("SMTP_PASSWORD"),
    "from": os.environ.get("SMTP_FROM")
}

def _smtp_from_secrets(st):
    s = getattr(st, "secrets", {}).get("smtp", {})
    if s and s.get("host"):
        return {
            "host": s.get("host"),
            "port": int(s.get("port", 465)),
            "user": s.get("user"),
            "password": s.get("password"),
            "from": s.get("from", s.get("user"))
        }
    return None

def send_email(to:str, subject:str, body:str, st=None, body_html:str|None=None):
    cfg = _smtp_from_secrets(st) if st else None
    cfg = cfg or SMTP
    if not cfg or not cfg.get("host"):
        raise RuntimeError("SMTP não configurado (.streamlit/secrets.toml ou variáveis de ambiente)")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.get("from") or cfg["user"]
    msg["To"] = to
    msg.set_content(body)
    if body_html:
        msg.add_alternative(body_html, subtype='html')
    with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as s:
        s.login(cfg["user"], cfg["password"])
        s.send_message(msg)

def fetch_due(days_ahead:int=3):
    hoje = date.today()
    limite = hoje + timedelta(days=days_ahead)
    rows = db.query("""
        SELECT m.id, m.descricao, m.valor, m.vencimento, m.status,
               u.email as responsavel_email, u.name as responsavel_nome
        FROM movimentos m
        LEFT JOIN users u ON u.id = m.responsavel_user_id
        WHERE m.status IN ('pendente')
          AND m.vencimento IS NOT NULL
    """)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["id","descricao","valor","vencimento","status","responsavel_email","responsavel_nome","categoria"])
    df["vencimento_dt"] = pd.to_datetime(df["vencimento"], errors="coerce").dt.date
    df = df.dropna(subset=["vencimento_dt"])
    df["dias"] = (df["vencimento_dt"] - hoje).apply(lambda x: x.days)
    return df[(df["dias"] <= days_ahead)]

def group_by_responsavel(df: pd.DataFrame):
    groups = {}
    for _, r in df.iterrows():
        email = r.get("responsavel_email") or ""
        if not email:
            continue
        groups.setdefault(email, []).append(r.to_dict())
    return groups

def compose_email(nome:str, itens:list):
    linhas = []
    atrasados = 0
    for it in itens:
        d = it.get("vencimento") or ""
        try:
            d = str(pd.to_datetime(d).date())
        except:
            d = str(d)
        flag = "ATRASADO" if pd.to_datetime(d) < pd.Timestamp.today().normalize() else ""
        if flag: atrasados += 1
        linhas.append(f"- #{it['id']} | {it['descricao']} | R$ {it['valor']:.2f} | vence: {d} {flag}")
    head = f"Olá {nome},\n\nVocê tem {len(itens)} conta(s) a vencer (ou vencidas)."
    if atrasados > 0:
        head += f" {atrasados} item(ns) estão ATRASADOS."
    body = head + "\n\n" + "\n".join(linhas) + "\n\n— Fluxo de Caixa Pro"
    return body


def _logo_data_uri(logo_path:str|None):
    if not logo_path or not os.path.exists(logo_path):
        return None
    with open(logo_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    ext = "png" if logo_path.lower().endswith("png") else "jpeg"
    return f"data:image/{ext};base64,{b64}"

TEMPLATES = {
    "Minimal": lambda nome, linhas, logo_uri: f"""
    <div style='font-family: Inter, Arial, sans-serif; color:#111; line-height:1.5'>
      <div style='display:flex;align-items:center;gap:12px'>
        {f"<img src='{logo_uri}' alt='logo' style='height:36px;border-radius:6px'/>" if logo_uri else ""}
        <h2 style='margin:0'>Contas a vencer</h2>
      </div>
      <p>Olá {nome},<br/>você tem {len(linhas)} conta(s) a vencer (ou vencidas).</p>
      <ul>
        {''.join([f"<li>#{it['id']} — {it['descricao']} — R$ {it['valor']:.2f} — vence: {it['vencimento']}</li>" for it in linhas])}
      </ul>
      <p style='color:#666'>— Fluxo de Caixa Pro</p>
    </div>
    """,
    "Corporate": lambda nome, linhas, logo_uri: f"""
    <table width='100%' cellpadding='0' cellspacing='0' style='font-family:Arial, sans-serif;background:#f6f7fb;padding:24px'>
      <tr><td align='center'>
        <table width='560' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;overflow:hidden'>
          <tr>
            <td style='background:#0B0F17;color:#E5E7EB;padding:16px 20px;display:flex;align-items:center'>
              {f"<img src='{logo_uri}' alt='logo' style='height:32px;margin-right:10px;border-radius:6px'/>" if logo_uri else ""}
              <strong style='font-size:16px'>Fluxo de Caixa Pro</strong>
            </td>
          </tr>
          <tr>
            <td style='padding:20px;color:#111'>
              <h2 style='margin:0 0 8px 0;color:#111'>Contas a vencer</h2>
              <p style='margin:0 0 16px 0'>Olá {nome}, você tem {len(linhas)} conta(s) a vencer (ou vencidas).</p>
              <table width='100%' cellpadding='8' cellspacing='0' style='border-collapse:collapse'>
                <thead>
                  <tr style='background:#101725;color:#E5E7EB'>
                    <th align='left'>ID</th><th align='left'>Descrição</th><th align='right'>Valor</th><th align='left'>Vencimento</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join([f"<tr style='border-bottom:1px solid #eee'><td>#{it['id']}</td><td>{it['descricao']}</td><td align='right'>R$ {it['valor']:.2f}</td><td>{it['vencimento']}</td></tr>" for it in linhas])}
                </tbody>
              </table>
              <p style='color:#666;margin-top:16px'>— Equipe Financeira</p>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>
    """,
    "Dark": lambda nome, linhas, logo_uri: f"""
    <div style='font-family:Arial, sans-serif;background:#0B0F17;color:#E5E7EB;padding:24px'>
      <div style='max-width:680px;margin:auto'>
        <div style='display:flex;align-items:center;gap:12px;margin-bottom:12px'>
          {f"<img src='{logo_uri}' alt='logo' style='height:36px;border-radius:6px'/>" if logo_uri else ""}
          <h2 style='margin:0;color:#E5E7EB'>Contas a vencer</h2>
        </div>
        <p>Olá {nome}, você tem {len(linhas)} conta(s) a vencer (ou vencidas).</p>
        <ul>
          {''.join([f"<li>#{it['id']} — {it['descricao']} — R$ {it['valor']:.2f} — vence: {it['vencimento']}</li>" for it in linhas])}
        </ul>
        <p style='color:#9CA3AF'>— Fluxo de Caixa Pro</p>
      </div>
    </div>
    """
}

def compose_email_html(nome:str, itens:list, template:str="Corporate", logo_path:str|None=None):
    logo_uri = _logo_data_uri(logo_path) if logo_path else None
    return TEMPLATES.get(template, TEMPLATES["Corporate"])(nome, itens, logo_uri)

def log_email(to_email:str, subject:str, template:str, items_count:int, status:str, error:str|None=None):
    try:
        from . import db
        db.execute("INSERT INTO email_log (to_email, subject, template, items_count, status, error) VALUES (?,?,?,?,?,?)",
                   (to_email, subject, template, int(items_count), status, error))
    except Exception as e:
        # Fallback: ignore logging errors
        pass


def render_template(html:str, nome:str, itens:list, logo_path:str|None=None, periodo:str="", empresa:str="", assinatura:str=""):
    logo_uri = _logo_data_uri(logo_path) if logo_path else ""
    # Build rows HTML
    rows = "".join([f"<tr><td>#{it['id']}</td><td>{it['descricao']}</td><td align='right'>R$ {it['valor']:.2f}</td><td>{it['vencimento']}</td></tr>" for it in itens])
    table = f"""
    <table width='100%' cellpadding='8' cellspacing='0' style='border-collapse:collapse'>
      <thead><tr><th align='left'>ID</th><th align='left'>Descrição</th><th align='right'>Valor</th><th align='left'>Vencimento</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """
    # Token replacement
    out = (html
           .replace("{{periodo}}", periodo)
           .replace("{{empresa}}", empresa)
           .replace("{{assinatura}}", assinatura)
           .replace("{{nome}}", nome)
           .replace("{{quantidade}}", str(len(itens)))
           .replace("{{logo}}", f"<img src='{logo_uri}' alt='logo' style='height:32px;border-radius:6px'/>" if logo_uri else "")
           .replace("{{tabela_itens}}", table))
    return out

def compose_email_html_custom(nome:str, itens:list, template_name:str, logo_path:str|None=None, periodo:str="", empresa:str="", assinatura:str=""):
    try:
        from . import db
        rows = db.query("SELECT html FROM email_templates WHERE name=?", (template_name,))
        if not rows:
            return compose_email_html(nome, itens, template='Corporate', logo_path=logo_path)
        html = rows[0]['html']
        return render_template(html, nome, itens, logo_path, periodo, empresa, assinatura)
    except Exception:
        return compose_email_html(nome, itens, template='Corporate', logo_path=logo_path)
