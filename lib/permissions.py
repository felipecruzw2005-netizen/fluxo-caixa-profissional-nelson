
import streamlit as st
from . import db

DEFAULT_PERMS = {
    "can_view_reports": 1,
    "can_create_movements": 1,
    "can_edit_movements": 1,
    "can_delete_movements": 0,
    "can_manage_users": 0,
    "can_view_all_clients": 1
}

def get_perms(user_id:int):
    rows = db.query("SELECT * FROM permissions WHERE user_id=?", (user_id,))
    if not rows:
        # seed defaults
        db.execute("INSERT OR IGNORE INTO permissions (user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients) VALUES (?,?,?,?,?,?,?)",
                   (user_id, DEFAULT_PERMS["can_view_reports"], DEFAULT_PERMS["can_create_movements"], DEFAULT_PERMS["can_edit_movements"], DEFAULT_PERMS["can_delete_movements"], DEFAULT_PERMS["can_manage_users"], DEFAULT_PERMS["can_view_all_clients"]))
        rows = db.query("SELECT * FROM permissions WHERE user_id=?", (user_id,))
    return rows[0]

def can(user, key:str) -> bool:
    if user is None: 
        return False
    p = get_perms(user["id"])
    return bool(p.get(key, 0))
