from flask import Blueprint

discover_bp = Blueprint('discover', __name__)

@discover_bp.route('/')
def health():
    return {'status': 'discover routes placeholder'}
