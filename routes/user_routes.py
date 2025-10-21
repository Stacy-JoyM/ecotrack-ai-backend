from flask import Blueprint

user_bp = Blueprint('users', __name__)

@user_bp.route('/')
def health():
    return {'status': 'user routes placeholder'}
