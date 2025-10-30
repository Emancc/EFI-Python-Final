from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Users, UserCredentials
from ..extensions import db
from ..schemas import UserSchema, UserRegisterSchema
from ..decorators.auth import roles_required, is_owner_or_admin

user_bp = Blueprint('user', __name__)
user_schema = UserSchema()
users_schema = UserSchema(many=True)

class UserAPI(MethodView):
    @jwt_required()
    def get(self, user_id=None):
        if user_id is None:
            users = Users.query.all()
            return jsonify({'users': users_schema.dump(users)}), 200
        
        user = Users.query.get_or_404(user_id)
        return jsonify({'user': user_schema.dump(user)}), 200

    @jwt_required()
    def put(self, user_id):
        user = Users.query.get_or_404(user_id)
        current_user_id = get_jwt_identity()
        
        # Solo el propio usuario o un admin pueden actualizar los datos
        if not is_owner_or_admin(user_id):
            return jsonify({'message': 'Unauthorized'}), 403

        data = request.get_json()
        
        if 'username' in data:
            # Verificar si el username ya existe
            existing_user = Users.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'message': 'Username already exists'}), 400
            user.username = data['username']
            
        if 'email' in data:
            # Verificar si el email ya existe
            existing_user = Users.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'message': 'Email already exists'}), 400
            user.email = data['email']
            
        if 'password' in data:
            user.credentials.set_password(data['password'])
            
        try:
            db.session.commit()
            return jsonify({'user': user_schema.dump(user)}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

    @jwt_required()
    @roles_required('admin')
    def delete(self, user_id):
        user = Users.query.get_or_404(user_id)
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

# Admin endpoints
class UserAdminAPI(MethodView):
    @jwt_required()
    @roles_required('admin')
    def post(self):
        """Endpoint para cambiar el rol de un usuario o desactivarlo"""
        data = request.get_json()
        user_id = data.get('user_id')
        user = Users.query.get_or_404(user_id)
        
        if 'role' in data:
            # Validar que el rol sea válido
            if data['role'] not in ['user', 'moderator', 'admin']:
                return jsonify({'message': 'Invalid role'}), 400
            user.role = data['role']
            user.credentials.role = data['role']  # Mantener sincronizado
            
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        try:
            db.session.commit()
            return jsonify({'user': user_schema.dump(user)}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 500

# Registrar las vistas
user_view = UserAPI.as_view('user_api')
user_bp.add_url_rule('/users', defaults={'user_id': None}, view_func=user_view, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=user_view, methods=['GET', 'PUT', 'DELETE'])

admin_view = UserAdminAPI.as_view('user_admin_api')
user_bp.add_url_rule('/users/admin/manage', view_func=admin_view, methods=['POST'])