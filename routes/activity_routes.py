from flask import Blueprint

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/')
def health():
    return {'status': 'activity routes placeholder'}
