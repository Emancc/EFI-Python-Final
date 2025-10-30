from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from app.models import db, Category
from app.schemas import CategorySchema
from app.decorators.auth import admin_required

category_bp = Blueprint('category', __name__)

class CategoryAPI(MethodView):
    def get(self, category_id=None):
        if category_id is None:
            categories = Category.query.all()
            return jsonify({'categories': CategorySchema(many=True).dump(categories)}), 200
            
        category = Category.query.get_or_404(category_id)
        return jsonify({'category': CategorySchema().dump(category)}), 200
    
    @admin_required()
    def post(self):
        try:
            data = CategorySchema().load(request.get_json())
            new_category = Category(
                name=data['name'],
                slug=data['slug'],
                description=data.get('description')
            )
            db.session.add(new_category)
            db.session.commit()
            return CategorySchema().dump(new_category), 201
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @admin_required()
    def put(self, category_id):
        category = Category.query.get_or_404(category_id)
        try:
            data = CategorySchema().load(request.get_json())
            for key, value in data.items():
                setattr(category, key, value)
            db.session.commit()
            return CategorySchema().dump(category), 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @admin_required()
    def delete(self, category_id):
        category = Category.query.get_or_404(category_id)
        try:
            db.session.delete(category)
            db.session.commit()
            return {'message': 'Category deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400

# Registrar las vistas
category_view = CategoryAPI.as_view('category_api')
category_bp.add_url_rule('/categories', defaults={'category_id': None}, 
                        view_func=category_view, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=category_view, methods=['POST'])
category_bp.add_url_rule('/categories/<int:category_id>', 
                        view_func=category_view, methods=['GET', 'PUT', 'DELETE'])