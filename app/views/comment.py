from flask import Blueprint, request, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Comment, Blogs
from app.schemas import CommentSchema
from app.decorators.auth import owner_required, moderator_required

comment_bp = Blueprint('comment', __name__)

class CommentAPI(MethodView):
    decorators = [jwt_required()]
    
    def get(self, post_id, comment_id=None):
        if comment_id is None:
            comments = Comment.query.filter_by(post_id=post_id).all()
            return jsonify({'comments': CommentSchema(many=True).dump(comments)}), 200
            
        comment = Comment.query.get_or_404(comment_id)
        if comment.post_id != post_id:
            return {'message': 'Comment not found in this post'}, 404
        return jsonify({'comment': CommentSchema().dump(comment)}), 200
    
    def post(self, post_id):
        post = Blogs.query.get_or_404(post_id)
        try:
            data = CommentSchema().load(request.get_json())
            new_comment = Comment(
                content=data['content'],
                user_id=get_jwt_identity(),
                post_id=post_id,
                is_visible=True
            )
            db.session.add(new_comment)
            db.session.commit()
            return CommentSchema().dump(new_comment), 201
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @owner_required(Comment)
    def put(self, post_id, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        if comment.post_id != post_id:
            return {'message': 'Comment not found in this post'}, 404
            
        try:
            data = CommentSchema().load(request.get_json())
            comment.content = data['content']
            db.session.commit()
            return CommentSchema().dump(comment), 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400
    
    @owner_required(Comment)
    def delete(self, post_id, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        if comment.post_id != post_id:
            return {'message': 'Comment not found in this post'}, 404
            
        try:
            db.session.delete(comment)
            db.session.commit()
            return {'message': 'Comment deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400

class CommentModeration(MethodView):
    decorators = [jwt_required(), moderator_required()]
    
    def put(self, comment_id):
        comment = Comment.query.get_or_404(comment_id)
        data = request.get_json()
        
        if 'is_visible' in data:
            comment.is_visible = data['is_visible']
            
        try:
            db.session.commit()
            return CommentSchema().dump(comment), 200
        except Exception as e:
            db.session.rollback()
            return {'message': str(e)}, 400

# Registrar las vistas
comment_view = CommentAPI.as_view('comment_api')
moderation_view = CommentModeration.as_view('comment_moderation')

comment_bp.add_url_rule('/posts/<int:post_id>/comments', 
                       defaults={'comment_id': None}, 
                       view_func=comment_view, 
                       methods=['GET'])
comment_bp.add_url_rule('/posts/<int:post_id>/comments',
                       view_func=comment_view,
                       methods=['POST'])
comment_bp.add_url_rule('/posts/<int:post_id>/comments/<int:comment_id>',
                       view_func=comment_view,
                       methods=['GET', 'PUT', 'DELETE'])
comment_bp.add_url_rule('/comments/<int:comment_id>/moderate',
                       view_func=moderation_view,
                       methods=['PUT'])