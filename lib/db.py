
from __future__ import annotations
import os
from typing import Iterable, Any, Dict, List
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# DATABASE_URL examples:
# - Postgres: postgresql+psycopg://user:pass@host:5432/dbname
# - SQLite (fallback): sqlite:///fluxo.db
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{os.environ.get('FC_DB_PATH','fluxo.db')}"

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SCHEMA_SQLITE = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS movimentos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  descricao TEXT NOT NULL,
  categoria TEXT,
  centro_custo TEXT,
  placa TEXT,
  observacao TEXT,
  forma_pagamento TEXT,
  tipo TEXT CHECK(tipo IN ('entrada','saida')) NOT NULL,
  valor REAL NOT NULL,
  cliente_id INTEGER,
  status TEXT DEFAULT 'confirmado',
  arquivo_path TEXT,
  vencimento TEXT,
  responsavel_user_id INTEGER,
  responsavel_nome TEXT,
  created_by INTEGER,
  deleted_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentos(data);
CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimentos(tipo);
CREATE TABLE IF NOT EXISTS permissions (
  user_id INTEGER PRIMARY KEY,
  can_view_reports INTEGER DEFAULT 1,
  can_create_movements INTEGER DEFAULT 1,
  can_edit_movements INTEGER DEFAULT 1,
  can_delete_movements INTEGER DEFAULT 0,
  can_manage_users INTEGER DEFAULT 0,
  can_view_all_clients INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS password_resets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS movement_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  movimento_id INTEGER NOT NULL,
  before_json TEXT NOT NULL,
  changed_by INTEGER NOT NULL,
  changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
  action TEXT CHECK(action IN ('update','delete')) NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT NOT NULL,
  entity TEXT,
  entity_id INTEGER,
  meta_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS email_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  to_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  template TEXT NOT NULL,
  items_count INTEGER DEFAULT 0,
  status TEXT NOT NULL,
  error TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS email_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  html TEXT NOT NULL,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  period_label TEXT,
  created_by INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""".strip()

SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS clientes (
  id SERIAL PRIMARY KEY,
  nome TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS movimentos (
  id SERIAL PRIMARY KEY,
  data TEXT NOT NULL,
  descricao TEXT NOT NULL,
  categoria TEXT,
  centro_custo TEXT,
  placa TEXT,
  observacao TEXT,
  forma_pagamento TEXT,
  tipo TEXT CHECK(tipo IN ('entrada','saida')) NOT NULL,
  valor DOUBLE PRECISION NOT NULL,
  cliente_id INTEGER REFERENCES clientes(id),
  status TEXT DEFAULT 'confirmado',
  arquivo_path TEXT,
  vencimento TEXT,
  responsavel_user_id INTEGER REFERENCES users(id),
  responsavel_nome TEXT,
  created_by INTEGER REFERENCES users(id),
  deleted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentos((data));
CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimentos(tipo);
CREATE TABLE IF NOT EXISTS permissions (
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  can_view_reports INTEGER DEFAULT 1,
  can_create_movements INTEGER DEFAULT 1,
  can_edit_movements INTEGER DEFAULT 1,
  can_delete_movements INTEGER DEFAULT 0,
  can_manage_users INTEGER DEFAULT 0,
  can_view_all_clients INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS password_resets (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  token TEXT UNIQUE NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS movement_history (
  id SERIAL PRIMARY KEY,
  movimento_id INTEGER NOT NULL REFERENCES movimentos(id),
  before_json TEXT NOT NULL,
  changed_by INTEGER NOT NULL REFERENCES users(id),
  changed_at TIMESTAMPTZ DEFAULT now(),
  action TEXT CHECK(action IN ('update','delete')) NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  action TEXT NOT NULL,
  entity TEXT,
  entity_id INTEGER,
  meta_json TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS email_log (
  id SERIAL PRIMARY KEY,
  to_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  template TEXT NOT NULL,
  items_count INTEGER DEFAULT 0,
  status TEXT NOT NULL,
  error TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS email_templates (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  html TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS batches (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  period_label TEXT,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
""".strip()

def bootstrap():
    ddl = SCHEMA_POSTGRES if DATABASE_URL.startswith("postgresql") else SCHEMA_SQLITE
    with engine.begin() as conn:
        for stmt in [s.strip() for s in ddl.split(';') if s.strip()]:
            conn.exec_driver_sql(stmt)

def query(sql: str, params: Iterable[Any]=()) -> List[Dict[str, Any]]:
    with engine.begin() as conn:
        res = conn.execute(text(sql), params if isinstance(params, dict) else params)
        cols = res.keys()
        return [dict(zip(cols, row)) for row in res.fetchall()]

def execute(sql: str, params: Iterable[Any]=()) -> int:
    with engine.begin() as conn:
        res = conn.execute(text(sql), params if isinstance(params, dict) else params)
        # emulate lastrowid (best-effort)
        try:
            return res.lastrowid or 0
        except Exception:
            return 0
