from datetime import datetime,timezone

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def utc_now_datetime():
    return datetime.now(timezone.utc)

from functools import wraps
from flask_jwt_extended import get_jwt,jwt_required
from flask import jsonify

def roles_requiered(*roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args,**kwargs):
            claims = get_jwt()
            if claims.get('role') in roles:
                return fn(*args,**kwargs)
            else:
                return jsonify(msg="Access Forbidden: Insufficient permissions")
            
        return decorator
    return wrapper