from flask import Blueprint, jsonify
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from ..models import Users, Blogs, Comment
from ..extensions import db
from app.decorators.auth import admin_required, moderator_required

stats_bp = Blueprint('stats', __name__)

class StatsAPI(MethodView):
    @moderator_required()
    def get(self):
        total_users = Users.query.count()
        total_posts = Blogs.query.count()
        total_comments = Comment.query.count()
        active_users = Users.query.filter_by(is_active=True).count()
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'total_posts': total_posts,
                'total_comments': total_comments
            }
        }), 200

class DetailedStatsAPI(MethodView):
    @admin_required()
    def get(self):
        # Estadísticas detalladas para administradores
        user_roles = db.session.query(
            Users.role, db.func.count(Users.id)
        ).group_by(Users.role).all()
        
        comments_per_post = db.session.query(
            db.func.avg(db.func.count(Comment.id))
        ).group_by(Comment.post_id).scalar() or 0
        
        posts_per_user = db.session.query(
            db.func.avg(db.func.count(Blogs.id))
        ).group_by(Blogs.user_id).scalar() or 0
        
        return jsonify({
            'detailed_stats': {
                'users_by_role': dict(user_roles),
                'avg_comments_per_post': float(comments_per_post),
                'avg_posts_per_user': float(posts_per_user)
            }
        }), 200

# Registrar las vistas
stats_bp.add_url_rule('/stats', view_func=StatsAPI.as_view('stats'))
stats_bp.add_url_rule('/stats/detailed', view_func=DetailedStatsAPI.as_view('detailed_stats'))