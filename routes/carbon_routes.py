from flask import Blueprint

carbon_bp = Blueprint('carbon', __name__)

@carbon_bp.route('/')
def health():
    return {'status': 'carbon routes placeholder'}
