from flask import Flask, request
from marshmallow import ValidationError
from extensions import db
from schemas import UserSchema, BlogSchema, CommentSchema

app = Flask(__name__)
# Configuración de la aplicación
app.config['SECRET_KEY'] = 'mi_super_secreto_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/db_blogs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la extensión db con la aplicación
db.init_app(app)

# Importar los modelos después de inicializar db
from models import Users, Blogs, Category, Comment

# Crear un contexto de aplicación para crear las tablas
with app.app_context():
    # Crear todas las tablas definidas en los modelos
    db.create_all()

@app.route('/users', methods=['POST', 'GET'])
def users():
    if request.method == 'POST':
        try:
            user_data = UserSchema().load(request.json)
            new_user = Users(
                username=user_data['username'],
                email=user_data['email']
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
def get_user(user_id):
    user = Users.query.get(user_id)
    if request.method == 'PUT':
        try:
            user_data = UserSchema().load(request.json)
            user.username = user_data['username']
            user.email = user_data['email']
            if 'password' in user_data:
                user.set_password(user_data['password'])
            db.session.commit()
        except ValidationError as err:
            return{'Mensaje': f'Error en la validación: {err.messages}'},400
                   

    if request.method == 'PATCH':
        try:
            user_data = UserSchema().load(request.json, partial=True)
            for key, value in user_data.items():
                setattr(user, key, value)
            db.session.commit()
            return UserSchema().dump(user), 200
        except ValidationError as err:
            return {'Mensaje': f'Error en la validación: {err.messages}'}, 400
    if user is None:
        return {'Mensaje': 'Usuario no encontrado'}, 404
    return UserSchema().dump(user), 200

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
