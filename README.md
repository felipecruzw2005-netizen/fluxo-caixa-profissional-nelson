
# Fluxo de Caixa Pro (Streamlit + SQLite)

Entrega profissional: dashboard elegante, filtros inteligentes, gestão de comprovantes, relatórios em Excel/PDF com logo e arquitetura modular.

## Como rodar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Diferenciais
- Layout dark premium com cards, ícones e gráficos Plotly.
- Filtros por período, status, forma de pagamento, tipo, valor e busca.
- Upload de comprovantes com pré-visualização (imagem) e galeria com download.
- Relatórios: Excel + PDF com logo e resumo financeiro.
- Código organizado em módulos (`lib/`) e páginas.
- Autenticação simples com seed automático de admin (email: admin@example.com, senha: admin) — altere depois.

## Estrutura
```
app.py
lib/
  auth.py
  db.py
  filters.py
  reporting.py
  storage.py
pages/
  1_Dashboard.py
  2_Movimentos.py
  3_Comprovantes.py
  4_Relatorios.py
  5_Usuarios.py (opcional)
assets/
  logo.png
.streamlit/config.toml
```

## Segurança e Multiusuário (opcional)
- Papéis: `admin` e `user`. A página de usuários só aparece para admin.
- Para permissões granulares (por cliente ou por operação), expanda a coluna `role` e adicione checagens nas páginas.

## Migração de dados
- O banco `fluxo.db` será criado automaticamente na primeira execução. Se você já possui um `movimentos` antigo, ajuste o `SCHEMA` em `lib/db.py` ou crie um script de migração.
```


## Notificações por e-mail (vencimentos)
- Página **Notificações**: selecione o horizonte de dias e clique **Enviar e-mails agora**.
- **Agendamento (cron)**: use o script CLI `bin/notify_due.py`.

### Exemplo de cron (diário às 8h)
Configure variáveis de ambiente SMTP e caminho do DB:
```bash
export FC_DB_PATH="/caminho/para/fluxo.db"
export SMTP_HOST="smtp.seuprovedor.com"
export SMTP_PORT="465"
export SMTP_USER="no-reply@seusistema.com"
export SMTP_PASSWORD="SENHA_AQUI"
export SMTP_FROM="no-reply@seusistema.com"
export NOTIFY_DAYS_AHEAD="3"
/usr/bin/python3 /caminho/para/projeto/bin/notify_due.py
```

> Dica: em servidores Linux, coloque isso no `crontab -e` (ex.: `0 8 * * * /usr/bin/env bash -lc '/usr/bin/python3 /caminho/.../notify_due.py'`).
```


## 🔔 Notificações de Vencimento
- Script `lib/notifier.py` envia e-mails para responsáveis (`responsavel`) de movimentos com vencimento nos próximos 3 dias.
- Requer SMTP configurado em `.streamlit/secrets.toml`.
- Pode ser rodado manualmente:
```bash
python -m lib.notifier
```
- Ou agendado no servidor (cron/Windows Task Scheduler) para rodar diariamente.

## Entrega de e-mails (SPF/DKIM/DMARC)
Para e-mails não caírem no spam:
1. **SPF**: Crie/edite o registro TXT do domínio:  
   `v=spf1 include:_spf.seuprovedor.com ~all`
2. **DKIM**: Ative no provedor de e-mail e publique o `TXT` na chave informada (ex.: `default._domainkey`).
3. **DMARC**: Publique `TXT` em `_dmarc.seudominio.com`:  
   `v=DMARC1; p=quarantine; rua=mailto:postmaster@seudominio.com; ruf=mailto:postmaster@seudominio.com; fo=1`
> Dica: ajuste `p=none/quarantine/reject` conforme maturidade. Teste com **MXToolbox** e **Gmail Postmaster**.

## Templates de e-mail (customizados)
- Página **Templates de E-mail**: crie/edite templates com placeholders:
  - `{{logo}}` — logo embutido
  - `{{nome}}` — nome do responsável
  - `{{quantidade}}` — número de itens
  - `{{tabela_itens}}` — tabela HTML dos itens
- Nas **Notificações**, escolha qualquer template (built-in ou custom).  
- No CLI, defina `TEMPLATE_NAME="Meu Template"`.


## Templates: modo visual (WYSIWYG)
- Páginas **Assistente de Template (WYSIWYG)** e **Templates de E-mail**:
  - Monte o e-mail ajustando cores, títulos e blocos (sem mexer no HTML).
  - Placeholders suportados: `{{logo}}`, `{{empresa}}`, `{{nome}}`, `{{quantidade}}`, `{{periodo}}`, `{{tabela_itens}}`, `{{assinatura}}`.
- Página **Configurações**:
  - Defina **Nome da empresa**, **Assinatura (HTML)** e rótulo do **período padrão**.
- Notificações usam essas configs automaticamente.


## Deploy na Streamlit Community Cloud (grátis)

1. Suba este projeto para um repositório no GitHub.
2. Crie um app em https://share.streamlit.io e aponte para `app.py`.
3. Em **Settings → Secrets**, cole algo como:

```toml
DATABASE_URL = "postgresql+psycopg://USER:PASS@HOST:5432/DBNAME"

[supabase]
url = "https://your-project.supabase.co"
key = "SUPABASE_SERVICE_OR_ANON_KEY"
bucket = "uploads"

[smtp]
host = "smtp.seuprovedor.com"
port = 465
user = "no-reply@seusistema.com"
password = "SENHA_AQUI"
from = "no-reply@seusistema.com"
```

4. Clique em **Deploy**. O banco e os uploads ficarão externos (persistentes).
5. **Limitações**: tarefas agendadas automáticas não rodam na Community Cloud; use o botão de envio de notificações ou dispare o script `bin/notify_due.py` via GitHub Actions/cron externo se precisar.
