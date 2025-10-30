from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from flask import jsonify
from ..models import Users

def roles_required(*roles):
    """
    Decorador que verifica si el usuario tiene uno de los roles requeridos
    Uso: @roles_required('admin', 'moderator')
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            if user and user.role in roles:
                return fn(*args, **kwargs)
            return jsonify(message=f"Access restricted to {', '.join(roles)}"), 403
        return decorator
    return wrapper

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            if user and user.role == 'admin':
                return fn(*args, **kwargs)
            return jsonify(message="Admins only!"), 403
        return decorator
    return wrapper

def moderator_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            if user and user.role in ['admin', 'moderator']:
                return fn(*args, **kwargs)
            return jsonify(message="Moderators and admins only!"), 403
        return decorator
    return wrapper

def owner_required(model):
    """
    Decorador que verifica si el usuario es el propietario del recurso
    Uso: @owner_required(Post)
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            
            # Obtener el ID del recurso de los argumentos
            resource_id = kwargs.get('id') or kwargs.get('user_id') or kwargs.get('blog_id')
            if not resource_id:
                return jsonify(message="Resource ID not found"), 400
                
            # Obtener el recurso
            resource = model.query.get(resource_id)
            if not resource:
                return jsonify(message="Resource not found"), 404
                
            # Verificar propiedad
            if hasattr(resource, 'user_id') and resource.user_id == user.id:
                return fn(*args, **kwargs)
            return jsonify(message="You don't have permission to access this resource"), 403
        return decorator
    return wrapper

def is_owner_or_admin(model):
    """
    Decorador que verifica si el usuario es el propietario del recurso o es admin
    Uso: @is_owner_or_admin(Post)
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Users.query.get(user_id)
            
            # Los admins siempre tienen acceso
            if user.role == 'admin':
                return fn(*args, **kwargs)
            
            # Obtener el ID del recurso de los argumentos
            resource_id = kwargs.get('id') or kwargs.get('user_id') or kwargs.get('blog_id')
            if not resource_id:
                return jsonify(message="Resource ID not found"), 400
                
            # Obtener el recurso
            resource = model.query.get(resource_id)
            if not resource:
                return jsonify(message="Resource not found"), 404
                
            # Verificar propiedad
            if hasattr(resource, 'user_id') and resource.user_id == user.id:
                return fn(*args, **kwargs)
            return jsonify(message="You don't have permission to access this resource"), 403
        return decorator
    return wrapper