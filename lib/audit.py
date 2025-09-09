
import json
from . import db

def log(user_id:int|None, action:str, entity:str|None=None, entity_id:int|None=None, meta:dict|None=None):
    db.execute("INSERT INTO audit_log (user_id, action, entity, entity_id, meta_json) VALUES (?,?,?,?,?)",
               (user_id, action, entity, entity_id, json.dumps(meta or {})))
