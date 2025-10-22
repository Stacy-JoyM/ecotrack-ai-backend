# routes/activity_routes.py
from flask import Blueprint, request, jsonify
from models.activity import Activity
from services.activity_service import add_activity, get_activities

activity_bp = Blueprint('activity', __name__)

@activity_bp.route('/api/activities', methods=['POST'])
def log_activity():
    data = request.json
    try:
        activity = add_activity(data['category'], data['type'], data['distance'])
        return jsonify(activity), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@activity_bp.route('/api/activities', methods=['GET'])
def list_activities():
    activities = get_activities()
    return jsonify(activities)
