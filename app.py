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

@app.route('/blogs', methods=['POST', 'GET'])
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
