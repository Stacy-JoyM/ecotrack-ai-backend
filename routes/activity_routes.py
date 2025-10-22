from flask import Blueprint, request, jsonify
from services.activity_service import create_activity, get_user_activities
from app import db

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('', methods=['POST'])
def log_activity():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    user_id = data.get('user_id')
    activity_type = data.get('activity_type')
    if not user_id or not activity_type:
        return jsonify({'error': 'user_id and activity_type are required'}), 400

    try:
        value = float(data.get('value', 1.0))
        activity = create_activity(user_id=user_id, activity_type=activity_type, value=value)
        return jsonify(activity.serialize()), 201
    except ValueError:
        return jsonify({'error': 'Invalid value: must be a number'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to log activity', 'details': str(e)}), 500

@activity_bp.route('/<int:user_id>', methods=['GET'])
def fetch_activities(user_id):
    try:
        activities = get_user_activities(user_id)
        return jsonify([act.serialize() for act in activities]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500