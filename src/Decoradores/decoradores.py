from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def role_required(roles):
    """Decorador para verificar si el usuario tiene el rol requerido"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('rol')
            
            # Si roles es string, convertir a lista
            if isinstance(roles, str):
                roles_list = [roles]
            else:
                roles_list = roles
            
            # Verificar si el rol del usuario está en los roles permitidos
            if user_role not in roles_list:
                return jsonify({
                    'mensaje': f"Acceso denegado. Se requiere rol: {', '.join(roles_list)}",
                    'exito': False
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator