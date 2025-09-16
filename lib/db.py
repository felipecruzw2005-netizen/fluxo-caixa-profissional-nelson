# lib/db.py — compatível com Supabase Transaction Pooler (pgBouncer)
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

def _get_db_url():
    # tenta Streamlit secrets; cai para env var
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL")
    except Exception:
        url = None
    return url or os.environ.get("DATABASE_URL")

_DB_URL = _get_db_url()
if not _DB_URL:
    raise RuntimeError("DATABASE_URL não encontrado em secrets nem em env.")

# Para pgBouncer, evite pool local do SQLAlchemy
use_nullpool = "pooler.supabase.com" in _DB_URL

engine = create_engine(
    _DB_URL,
    future=True,
    poolclass=NullPool if use_nullpool else None,
    pool_pre_ping=True,   # reconecta se a conexão caiu
    # connect_args não é necessário com psycopg3; sslmode já está na URL
)

@contextmanager
def _connect():
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()

def query(sql, params=()):
    with _connect() as conn:
        res = conn.execute(text(sql), params if isinstance(params, (list, tuple, dict)) else {})
        return [dict(r._mapping) for r in res]

def execute(sql, params=()):
    with _connect() as conn:
        res = conn.execute(text(sql), params if isinstance(params, (list, tuple, dict)) else {})
        try:
            last_id = res.inserted_primary_key[0] if res.inserted_primary_key else None
        except Exception:
            last_id = None
        conn.commit()
        return last_id

def executemany(sql, seq_of_params):
    with _connect() as conn:
        conn.execute(text(sql), seq_of_params)
        conn.commit()

def bootstrap():
    # ping simples para falhar cedo com mensagem clara
    query("SELECT 1", {})
