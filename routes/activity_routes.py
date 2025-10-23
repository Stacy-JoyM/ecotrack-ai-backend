from flask import Blueprint, request, jsonify
from services.activity_service import log_activity, get_user_activities

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activities')

@activity_bp.route('/track', methods=['POST'])
def track_activity():
    data = request.get_json()
    required = ['user_id', 'category']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    activity = log_activity(data)
    return jsonify(activity), 201

@activity_bp.route('/history/<int:user_id>', methods=['GET'])
def activity_history(user_id):
    activities = get_user_activities(user_id)
    return jsonify(activities)
