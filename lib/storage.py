
import os, uuid, io
from typing import Optional
from . import db

SUPABASE_URL = os.environ.get("SUPABASE_URL") or (getattr(__import__('streamlit'), 'secrets', {}).get('supabase', {}).get('url') if hasattr(__import__('streamlit'), 'secrets') else None)
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or (getattr(__import__('streamlit'), 'secrets', {}).get('supabase', {}).get('key') if hasattr(__import__('streamlit'), 'secrets') else None)
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "uploads")

_use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)

def _client():
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = os.environ.get("FC_UPLOAD_DIR", "uploads")

def ensure_dirs():
    if not _use_supabase:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_upload(file) -> str:
    ensure_dirs()
    ext = os.path.splitext(file.name)[1].lower() if getattr(file, 'name', None) else ""
    fname = f"{uuid.uuid4().hex}{ext}"
    if _use_supabase:
        data = file.getvalue() if hasattr(file, 'getvalue') else file.getbuffer()
        _client().storage.from_(SUPABASE_BUCKET).upload(f"{fname}", data, {"content-type": getattr(file, 'type', 'application/octet-stream')})
        return f"supabase://{SUPABASE_BUCKET}/{fname}"
    else:
        path = os.path.join(UPLOAD_DIR, fname)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        return path

def read_bytes(path: str) -> bytes:
    if path and path.startswith("supabase://"):
        bucket_key = path.replace("supabase://","").split("/",1)
        bucket = bucket_key[0]; key = bucket_key[1]
        return _client().storage.from_(bucket).download(key)
    with open(path, "rb") as f:
        return f.read()

def public_url(path: str) -> Optional[str]:
    if path and path.startswith("supabase://"):
        bucket_key = path.replace("supabase://","").split("/",1)
        bucket = bucket_key[0]; key = bucket_key[1]
        # signed URL valid for 1 hour
        resp = _client().storage.from_(bucket).create_signed_url(key, 3600)
        return resp.get("signedURL") or resp.get("signed_url")
    return None
