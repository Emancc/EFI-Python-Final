from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Blogs, Users
from app.schemas import BlogSchema
from app.decorators.auth import owner_required

post_bp = Blueprint('post', __name__)

class PostAPI(MethodView):
    decorators = [jwt_required()]
    
    def get(self, post_id=None):
        if post_id is None:
            posts = Blogs.query.all()
            return jsonify({'posts': BlogSchema(many=True).dump(posts)}), 200
            
        post = Blogs.query.get_or_404(post_id)
        return jsonify({'post': BlogSchema().dump(post)}), 200
    
    def post(self):
        try:
            data = BlogSchema().load(request.get_json())
            new_post = Blogs(
                title=data['title'],
                description=data['description'],
                user_id=get_jwt_identity(),
                category_id=data.get('category_id')
            )
            db.session.add(new_post)
            db.session.commit()
            return BlogSchema().dump(new_post), 201
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @owner_required(Blogs)
    def put(self, post_id):
        post = Blogs.query.get_or_404(post_id)
        try:
            data = BlogSchema().load(request.get_json())
            for key, value in data.items():
                setattr(post, key, value)
            db.session.commit()
            return BlogSchema().dump(post), 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @owner_required(Blogs)
    def delete(self, post_id):
        post = Blogs.query.get_or_404(post_id)
        try:
            db.session.delete(post)
            db.session.commit()
            return {'message': 'Post deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400

# Registrar las vistas
post_view = PostAPI.as_view('post_api')
post_bp.add_url_rule('/posts', defaults={'post_id': None}, view_func=post_view, methods=['GET'])
post_bp.add_url_rule('/posts', view_func=post_view, methods=['POST'])
post_bp.add_url_rule('/posts/<int:post_id>', view_func=post_view, methods=['GET', 'PUT', 'DELETE'])