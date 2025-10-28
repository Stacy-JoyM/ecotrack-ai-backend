from flask import Blueprint, request, jsonify
from models.activity import Activity
from app import db

activity_bp = Blueprint('activity_bp', __name__, url_prefix='/activity')

@activity_bp.route('/', methods=['GET'])
def get_activities():
    """
    ACT-001: Get all activities
    Returns a list of all activity records
    """
    activities = Activity.query.all()
    result = [activity.to_dict() for activity in activities]
    return jsonify(result), 200
