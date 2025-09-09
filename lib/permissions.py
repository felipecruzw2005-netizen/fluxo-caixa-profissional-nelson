import os
from . import db

# Permissões padrão (1 = permitido, 0 = negado)
DEFAULT_PERMS = {
    "can_view_reports": 1,
    "can_create_movements": 1,
    "can_edit_movements": 1,
    "can_delete_movements": 0,
    "can_manage_users": 0,
    "can_view_all_clients": 1,
}

def get_perms(user_id: int):
    """
    Garante que exista um registro na tabela permissions para o user_id
    e retorna um dict com as permissões.
    Compatível com Postgres (ON CONFLICT) e SQLite (OR IGNORE).
    """
    is_pg = os.environ.get("DATABASE_URL", "").startswith("postgresql")

    params = (
        user_id,
        DEFAULT_PERMS["can_view_reports"],
        DEFAULT_PERMS["can_create_movements"],
        DEFAULT_PERMS["can_edit_movements"],
        DEFAULT_PERMS["can_delete_movements"],
        DEFAULT_PERMS["can_manage_users"],
        DEFAULT_PERMS["can_view_all_clients"],
    )

    if is_pg:
        # Postgres
        db.execute(
            "INSERT INTO permissions (user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT (user_id) DO NOTHING",
            params,
        )
    else:
        # SQLite
        db.execute(
            "INSERT OR IGNORE INTO permissions (user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients) "
            "VALUES (?,?,?,?,?,?,?)",
            params,
        )

    rows = db.query(
        "SELECT user_id, can_view_reports, can_create_movements, can_edit_movements, can_delete_movements, can_manage_users, can_view_all_clients "
        "FROM permissions WHERE user_id = ?",
        (user_id,),
    )
    if rows:
        # Garante chaves faltantes com defaults
        r = rows[0]
        for k, v in DEFAULT_PERMS.items():
            if k not in r or r[k] is None:
                r[k] = v
        return r

    # fallback (não deveria acontecer)
    out = {"user_id": user_id}
    out.update(DEFAULT_PERMS)
    return out

def can(user: dict | None, perm: str) -> bool:
    """
    Retorna True/False se o usuário possui a permissão.
    Aceita user=None (retorna False).
    """
    if not user or "id" not in user:
        return False
    p = get_perms(int(user["id"]))
    return bool(p.get(perm, DEFAULT_PERMS.get(perm, 0)))
