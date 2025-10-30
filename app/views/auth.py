from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import Users, UserCredentials
from ..extensions import db
from ..schemas import UserSchema, UserRegisterSchema
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

class AuthAPI(MethodView):
    """
    Endpoints de autenticación
    ---
    post:
      description: Login de usuario
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        200:
          description: Login exitoso
        401:
          description: Credenciales inválidas
    """
    def post(self):
        """Endpoint de login"""
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400
            
        user = Users.query.filter_by(email=data.get('email')).first()
        
        if not user or not user.check_password(data.get('password')):
            return jsonify({'message': 'Invalid email or password'}), 401
            
        if not user.is_active:
            return jsonify({'message': 'Account is deactivated'}), 401
        
        # Actualizar último login
        if user.credentials:
            user.credentials.last_login = datetime.utcnow()
            db.session.commit()
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role,
                'email': user.email,
                'username': user.username
            }
        )
        
        return jsonify({
            'access_token': access_token,
            'user': UserSchema().dump(user)
        }), 200

class RegisterAPI(MethodView):
    def post(self):
        """Endpoint de registro"""
        try:
            user_data = UserRegisterSchema().load(request.get_json())
            
            # Verificar si el usuario ya existe
            if Users.query.filter(
                (Users.username == user_data['username']) | 
                (Users.email == user_data['email'])
            ).first():
                return jsonify({'message': 'Username or email already exists'}), 400
            
            # Crear el usuario
            new_user = Users(
                username=user_data['username'],
                email=user_data['email'],
                role='user',
                is_active=True
            )
            db.session.add(new_user)
            db.session.flush()  # Para obtener el ID del usuario
            
            # Crear las credenciales
            credentials = UserCredentials(user_id=new_user.id)
            credentials.set_password(user_data['password'])
            db.session.add(credentials)
            
            db.session.commit()
            
            # Crear token de acceso para login automático
            access_token = create_access_token(
                identity=new_user.id,
                additional_claims={
                    'role': new_user.role,
                    'email': new_user.email,
                    'username': new_user.username
                }
            )
            
            return jsonify({
                'message': 'User created successfully',
                'access_token': access_token,
                'user': UserSchema().dump(new_user)
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400


class UserProfileAPI(MethodView):
    decorators = [jwt_required()]
    
    def get(self):
        """Obtener perfil del usuario actual"""
        user_id = get_jwt_identity()
        user = Users.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        return jsonify(UserSchema().dump(user)), 200
    
    def put(self):
        """Actualizar perfil del usuario actual"""
        user_id = get_jwt_identity()
        user = Users.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        try:
            # Actualizar campos permitidos
            if 'username' in data:
                # Verificar si el username ya existe
                existing = Users.query.filter(
                    Users.username == data['username'],
                    Users.id != user_id
                ).first()
                if existing:
                    return jsonify({'message': 'Username already taken'}), 400
                user.username = data['username']
                
            if 'password' in data:
                user.set_password(data['password'])
                
            db.session.commit()
            return jsonify(UserSchema().dump(user)), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400


# Registrar las vistas
auth_bp.add_url_rule('/login', view_func=AuthAPI.as_view('login'))
auth_bp.add_url_rule('/register', view_func=RegisterAPI.as_view('register'))
auth_bp.add_url_rule('/profile', view_func=UserProfileAPI.as_view('profile'))