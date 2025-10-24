from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from models.activity import (
    db, Activity, TransportActivity, EnergyActivity,
    create_transport_activity, create_energy_activity
)

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/activities', methods=['POST'])
@jwt_required()
def create_activity():
    """
    Create a new activity (transport or energy)
    
    For Transport:
    {
        "category": "transport",
        "vehicle_type": "petrol" | "electric",
        "distance": 50.5,
        "notes": "Car Journey" (optional),
        "date": "2025-10-24T10:30:00Z" (optional)
    }
    
    For Energy:
    {
        "category": "energy",
        "energy_type": "air_conditioning",
        "usage_kwh": 12.5,
        "notes": "Office AC" (optional),
        "date": "2025-10-24T10:30:00Z" (optional)
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate category
        category = data.get('category')
        if not category or category not in ['transport', 'energy']:
            return jsonify({
                'success': False,
                'error': 'category must be either "transport" or "energy"'
            }), 400
        
        # Parse date if provided
        activity_date = None
        if 'date' in data:
            try:
                activity_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
            except:
                activity_date = datetime.utcnow()
        
        # Handle based on category
        if category == 'transport':
            # Validate transport fields
            if 'vehicle_type' not in data or 'distance' not in data:
                return jsonify({
                    'success': False,
                    'error': 'vehicle_type and distance are required for transport'
                }), 400
            
            if data['vehicle_type'] not in ['electric', 'petrol']:
                return jsonify({
                    'success': False,
                    'error': 'vehicle_type must be either "electric" or "petrol"'
                }), 400
            
            # Create transport activity
            activity = create_transport_activity(
                user_id=user_id,
                vehicle_type=data['vehicle_type'],
                distance=float(data['distance']),
                date=activity_date,
                notes=data.get('notes'),
                vehicle_model=data.get('vehicle_model'),
                fuel_efficiency=data.get('fuel_efficiency'),
                use_api=data.get('use_api', False)
            )
            
        elif category == 'energy':
            # Validate energy fields
            if 'energy_type' not in data or 'usage_kwh' not in data:
                return jsonify({
                    'success': False,
                    'error': 'energy_type and usage_kwh are required for energy'
                }), 400
            
            # Valid energy types
            valid_types = [
                'home_electricity', 'air_conditioning', 'heating', 'water_heating',
                'office_energy', 'electronics', 'appliances', 'lighting', 'cooking', 'laundry'
            ]
            
            if data['energy_type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': f'Invalid energy_type. Must be one of: {", ".join(valid_types)}'
                }), 400
            
            # Create energy activity
            activity = create_energy_activity(
                user_id=user_id,
                energy_type=data['energy_type'],
                usage_kwh=float(data['usage_kwh']),
                date=activity_date,
                notes=data.get('notes'),
                duration_hours=data.get('duration_hours'),
                appliance_name=data.get('appliance_name'),
                use_api=data.get('use_api', False),
                country_code=data.get('country_code', 'US')
            )
        
        # Save to database
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{category.capitalize()} activity created successfully',
            'data': activity.to_dict()
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Invalid data format: {str(e)}'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== GET ACTIVITIES ====================

@activity_bp.route('/activities', methods=['GET'])
@jwt_required()
def get_activities():
    """
    Get all activities for the current user
    
    Query params:
    - category: 'transport' or 'energy' or 'all' (default: 'all')
    - page: page number (default: 1)
    - per_page: items per page (default: 20)
    """
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        category = request.args.get('category', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        query = Activity.query.filter_by(user_id=user_id)
        
        if category and category != 'all':
            query = query.filter_by(category=category)
        
        # Order by date descending
        query = query.order_by(Activity.date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert to dict
        activities = []
        for activity in pagination.items:
            activity_dict = activity.to_dict()
            # Add a display name for the frontend
            if isinstance(activity, TransportActivity):
                activity_dict['display_name'] = activity.notes or f"{activity.vehicle_type.capitalize()} - {activity.distance}km"
            elif isinstance(activity, EnergyActivity):
                activity_dict['display_name'] = activity.notes or f"{activity.energy_type.replace('_', ' ').title()} - {activity.usage_kwh}kWh"
            activities.append(activity_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'activities': activities,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@activity_bp.route('/activities/<int:activity_id>', methods=['DELETE'])
@jwt_required()
def delete_activity(activity_id):
    """Delete an activity"""
    try:
        user_id = get_jwt_identity()
        
        activity = Activity.query.filter_by(id=activity_id, user_id=user_id).first()
        
        if not activity:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404
        
        db.session.delete(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== STATISTICS (For Top Cards) ====================

@activity_bp.route('/activities/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """
    Get summary statistics for the top cards
    Total Emissions, Activities Logged, Average Impact
    """
    try:
        user_id = get_jwt_identity()
        
        # Get all activities
        activities = Activity.query.filter_by(user_id=user_id).all()
        
        if not activities:
            return jsonify({
                'success': True,
                'data': {
                    'total_emissions': 0,
                    'activities_logged': 0,
                    'average_impact': 0
                }
            }), 200
        
        # Calculate totals
        total_co2 = sum(a.co2_emission or 0 for a in activities)
        total_count = len(activities)
        average_co2 = total_co2 / total_count if total_count > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_emissions': round(total_co2, 1),
                'activities_logged': total_count,
                'average_impact': round(average_co2, 1)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@activity_bp.route('/activities/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    Get activity history with filtering
    
    Query params:
    - filter: 'all', 'transport', 'food', 'energy' (default: 'all')
    - limit: number of results (default: 10)
    """
    try:
        user_id = get_jwt_identity()
        filter_type = request.args.get('filter', 'all')
        limit = int(request.args.get('limit', 10))
        
        # Build query
        query = Activity.query.filter_by(user_id=user_id)
        
        if filter_type != 'all':
            query = query.filter_by(category=filter_type)
        
        # Order by date descending and limit
        activities = query.order_by(Activity.date.desc()).limit(limit).all()
        
        # Format for frontend
        history = []
        for activity in activities:
            if isinstance(activity, TransportActivity):
                history.append({
                    'id': activity.id,
                    'title': activity.notes or 'Car Journey',
                    'time': f"{int((datetime.utcnow() - activity.date).total_seconds() // 3600)} hours ago",
                    'co2': round(activity.co2_emission or 0, 1),
                    'category': 'Transport',
                    'category_lowercase': 'transport'
                })
            elif isinstance(activity, EnergyActivity):
                history.append({
                    'id': activity.id,
                    'title': activity.notes or activity.energy_type.replace('_', ' ').title(),
                    'time': f"{int((datetime.utcnow() - activity.date).total_seconds() // 3600)} hours ago",
                    'co2': round(activity.co2_emission or 0, 1),
                    'category': 'Energy',
                    'category_lowercase': 'energy'
                })
        
        return jsonify({
            'success': True,
            'data': history
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ENERGY TYPES LIST ====================

@activity_bp.route('/activities/energy-types', methods=['GET'])
def get_energy_types():
    """Get list of valid energy types for dropdown"""
    energy_types = [
        {'value': 'home_electricity', 'label': 'Home Electricity'},
        {'value': 'air_conditioning', 'label': 'Air Conditioning'},
        {'value': 'heating', 'label': 'Heating'},
        {'value': 'water_heating', 'label': 'Water Heating'},
        {'value': 'office_energy', 'label': 'Office Energy'},
        {'value': 'electronics', 'label': 'Electronics'},
        {'value': 'appliances', 'label': 'Appliances'},
        {'value': 'lighting', 'label': 'Lighting'},
        {'value': 'cooking', 'label': 'Cooking'},
        {'value': 'laundry', 'label': 'Laundry'}
    ]
    
    return jsonify({
        'success': True,
        'data': energy_types
    }), 200