from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Crear instancias de las extensiones
db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()
cors = CORS()