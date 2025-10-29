from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from services.activity_service import (
    create_transport_activity,
    create_energy_activity,
    get_activity_summary,
    get_activity_history,
    delete_activity
)
from extensions import db

activity_bp = Blueprint('activity_bp', __name__, url_prefix='/api/activities')

def calculate_transport_emission(vehicle_type, distance):
    factor_map = {
        'petrol': 0.21,
        'diesel': 0.25,
        'electric': 0.05,
        'hybrid': 0.15,
        'motorcycle': 0.1,
        'bus': 0.3,
        'van_diesel': 0.28,
        'truck_light': 0.35,
        'truck_heavy': 0.5
    }
    factor = factor_map.get((vehicle_type or '').lower())
    if factor is None or distance <= 0:
        return 0
    return round(factor * distance, 2)

def calculate_energy_emission(energy_type, usage_kwh, duration_hours=None):
    factor_map = {
        'electricity': 0.43,
        'biogas': 0.18,
        'solar': 0.0,
        'gas': 0.25,
        'lpg': 0.24,
        'kerosene': 0.27,
        'wind': 0.0,
        'air_conditioning': 0.5
    }
    factor = factor_map.get((energy_type or '').lower())
    if factor is None or usage_kwh <= 0:
        return 0
    usage = usage_kwh * duration_hours if duration_hours and duration_hours > 0 else usage_kwh
    return round(factor * usage, 2)

@activity_bp.route('', methods=['POST'])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def add_activity():
    data = request.json
    category = data.get('category')
    user_id = data.get('user_id')
    if not category or not user_id:
        return jsonify({"error": "Category and user_id are required"}), 400
    try:
        if category == 'transport':
            activity = create_transport_activity(
                user_id=user_id,
                vehicle_type=data.get('vehicle_type'),
                distance=data.get('distance', 0),
                notes=data.get('notes', ''),
                vehicle_model=data.get('vehicle_model'),
                fuel_efficiency=data.get('fuel_efficiency')
            )
        elif category == 'energy':
            activity = create_energy_activity(
                user_id=user_id,
                energy_type=data.get('energy_type'),
                usage_kwh=data.get('usage_kwh', 0),
                notes=data.get('notes', ''),
                duration_hours=data.get('duration_hours'),
                appliance_name=data.get('appliance_name'),
            )
        else:
            return jsonify({"error": "Invalid category"}), 400
        db.session.add(activity)
        db.session.commit()
        return jsonify({"success": True, "data": activity.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activity_bp.route('/summary', methods=['GET'])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def summary():
    try:
        summary_data = get_activity_summary()
        return jsonify({"success": True, "data": summary_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activity_bp.route('/history', methods=['GET'])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def history():
    try:
        filter_type = request.args.get('filter', 'all')
        activities = get_activity_history(filter_type)
        history_list = []
        for a in activities:
            title = getattr(a, 'vehicle_type', None) or getattr(a, 'energy_type', 'Unknown')
            if a.co2_emission is not None:
                emissions = a.co2_emission
            elif a.category == 'transport':
                emissions = calculate_transport_emission(a.vehicle_type, getattr(a, 'distance', 0))
            elif a.category == 'energy':
                emissions = calculate_energy_emission(a.energy_type, getattr(a, 'usage_kwh', 0), getattr(a, 'duration_hours', None))
            else:
                emissions = 0
            history_list.append({
                "id": a.id,
                "category": a.category.capitalize(),
                "category_lowercase": a.category.lower(),
                "title": title.capitalize(),
                "time": a.safe_date.isoformat(),
                "co2": emissions
            })
        return jsonify({"success": True, "data": history_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activity_bp.route('/<int:activity_id>', methods=['DELETE'])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def delete_activity_route(activity_id):
    try:
        success = delete_activity(activity_id)
        if not success:
            return jsonify({"error": "Activity not found"}), 404
        return jsonify({"success": True, "message": "Activity deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@activity_bp.route('/energy-types', methods=['GET'])
@cross_origin(origins="http://localhost:3000", supports_credentials=True)
def get_energy_types():
    types = [
        "electricity", "gas", "lpg", "kerosene",
        "solar", "wind", "biogas", "air_conditioning"
    ]
    return jsonify({"success": True, "data": types}), 200
