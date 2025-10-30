from marshmallow import Schema, fields, validates, ValidationError
from .extensions import ma
from .models import Users, UserCredentials, Blogs, Comment, Category

class UserCredentialsSchema(ma.SQLAlchemySchema):
    class Meta:
        model = UserCredentials
        load_instance = True
    
    password = fields.Str(load_only=True, required=True)
    last_login = fields.DateTime(dump_only=True)

class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Users
        load_instance = True

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class UserRegisterSchema(UserSchema):
    password = fields.Str(load_only=True, required=True)

class BlogSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Blogs

    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    content = fields.Str(required=True)
    user_id = fields.Int(dump_only=True)
    category_id = fields.Int(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Campos anidados
    author = fields.Nested(UserSchema(only=('id', 'username')), dump_only=True)
    category = fields.Nested('CategorySchema', only=('id', 'name'), dump_only=True)

class CommentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Comment

    id = fields.Int(dump_only=True)
    content = fields.Str(required=True)
    user_id = fields.Int(dump_only=True)
    post_id = fields.Int(required=True)
    parent_id = fields.Int(allow_none=True)
    is_approved = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Campos anidados
    author = fields.Nested(UserSchema(only=('id', 'username')), dump_only=True)
    replies = fields.Nested('self', many=True, dump_only=True)

class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)