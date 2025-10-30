from flask import Flask
from datetime import timedelta
from dotenv import load_dotenv
from .extensions import db, ma, jwt, cors
import os

# Cargar variables de entorno
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'mi_super_secreto_12345'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/db_blogs'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Configuración CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],  # Ajusta según tu frontend
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Inicializar extensiones con la aplicación
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    
    # Registrar blueprints
    from .views.auth import auth_bp
    from .views.user import user_bp
    from .views.post import post_bp
    from .views.comment import comment_bp
    from .views.category import category_bp
    from .views.stats import stats_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(post_bp, url_prefix='/api')
    app.register_blueprint(comment_bp, url_prefix='/api')
    app.register_blueprint(category_bp, url_prefix='/api')
    app.register_blueprint(stats_bp, url_prefix='/api')
    
    # Manejadores de error
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal Server Error'}, 500

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return {'message': 'Missing Authorization Header'}, 401
    
    return app