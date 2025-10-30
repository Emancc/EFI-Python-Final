from flask import Flask, request, jsonify
from marshmallow import ValidationError
from extensions import db
from schemas import UserSchema, BlogSchema, CommentSchema
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

app = Flask(__name__)
# Configuración de la aplicación
app.config['SECRET_KEY'] = 'mi_super_secreto_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/db_blogs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Inicializar extensiones
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Endpoint de login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Users.query.filter_by(email=data.get('email')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'Invalid email or password'}), 401
        
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated'}), 401
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'role': user.role,
            'email': user.email
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'user': UserSchema().dump(user)
    }), 200

# Importar los modelos después de inicializar db
from models import Users, Blogs, Category, Comment

# Crear un contexto de aplicación para crear las tablas
with app.app_context():
    # Crear todas las tablas definidas en los modelos
    db.create_all()


#-------------------------------------------CRUD USERS-------------------------------------------
@app.route('/users', methods=['POST', 'GET'])
@jwt_required(optional=True)  # Permitir GET sin token, pero requerir token para POST
def users():
    if request.method == 'POST':
        try:
            user_data = UserSchema().load(request.json)
            new_user = Users(
                username=user_data['username'],
                email=user_data['email'],
                role='user',  # Por defecto, los nuevos usuarios son 'user'
                is_active=True
            )
            new_user.set_password(user_data['password'])
            db.session.add(new_user)
            db.session.commit()
            return UserSchema().dump(new_user), 201
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400
    
    # Manejo para el método GET
    elif request.method == 'GET':
        all_users = Users.query.all()
        return {'users': UserSchema(many=True).dump(all_users)}, 200

@app.route('/users/<int:user_id>', methods=['GET','PATCH','PUT','DELETE'])
@jwt_required()  # Requerir token para todas las operaciones
def user(user_id):
    user = Users.query.get(user_id)
    if user is None:
        return {'Mensaje': 'Usuario no encontrado'}, 404
    elif request.method == 'PUT':
        try:
            user_data = UserSchema().load(request.json)
            user.username = user_data['username']
            user.email = user_data['email']
            if 'password' in user_data:
                user.set_password(user_data['password'])
            db.session.commit()
        except ValidationError as err:
            return{'Mensaje': f'Error en la validación: {err.messages}'},400
            

    elif request.method == 'PATCH':
        try:
            user_data = UserSchema().load(request.json, partial=True)
            for key, value in user_data.items():
                setattr(user, key, value)
            db.session.commit()
            return UserSchema().dump(user), 200
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400


    elif request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return {'Mensaje': 'Usuario eliminado correctamente'}, 200
    
    elif request.method == 'GET':
        return UserSchema().dump(user), 200

#-------------------------------------------CRUD BLOGS-------------------------------------------

@app.route('/blogs', methods=['POST','GET'])
def blogs():
    if request.method == 'POST':
        try:
            blog_data = BlogSchema().load(request.json)
            new_blog = Blogs(
                title=blog_data['title'],
                description=blog_data['description'],
                user_id=blog_data['user_id'],
                category_id=blog_data.get('category_id')
            )
            db.session.add(new_blog)
            db.session.commit()
            return BlogSchema().dump(new_blog), 201
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400
    
    # Manejo para el método GET
    elif request.method == 'GET':
        all_blogs = Blogs.query.all()
        return {'blogs': BlogSchema(many=True).dump(all_blogs)}, 200

@app.route('/blogs/<int:blog_id>', methods=['GET','PUT','PATCH','DELETE'])
def blog(blog_id):
    blog = Blogs.query.get(blog_id)
    if not blog:
        return {'Mensaje': 'Blog no encontrado'}, 404

    if request.method == 'PUT':
        try:
            blog_data = BlogSchema().load(request.json)
            blog.title = blog_data['title']
            blog.description = blog_data['description']
            blog.user_id = blog_data['user_id']
            if 'category_id' in blog_data:
                blog.category_id = blog_data['category_id']
            db.session.commit()
            return BlogSchema().dump(blog), 200
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400

    elif request.method == 'PATCH':
        try:
            blog_data = BlogSchema().load(request.json, partial=True)
            for key, value in blog_data.items():
                if hasattr(blog, key):  # Solo actualizar atributos existentes
                    setattr(blog, key, value)
            db.session.commit()
            return BlogSchema().dump(blog), 200
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400

    elif request.method == 'DELETE':
        db.session.delete(blog)
        db.session.commit()
        return {'Mensaje': 'Blog eliminado correctamente'}, 200
        
    elif request.method == 'GET':
        blog = Blogs.query.get(blog_data['id'])
        return BlogSchema().dump(blog), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
