from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.activity import Activity, EnergyLog, TransportLog
from models.user import User
from app import db
from helper import ENERGY_EMISSIONS, TRANSPORT_EMISSIONS

activity_bp = Blueprint('activity_bp', __name__)

@activity_bp.route('/activities', methods=['POST'])
@jwt_required()  # ✅ Add authentication
def log_activity():
    """Create new activity"""
    try:
        # Get current user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        # ✅ Normalize category (lowercase to Title case)
        category = data.get('category', '').lower()
        category_title = category.capitalize()  # 'energy' -> 'Energy'
        
        notes = data.get('notes', '')

        # Create activity with user_id
        activity = Activity(
            category=category_title,
            notes=notes,
            user_id=user.id  # ✅ Add user_id
        )
        db.session.add(activity)
        db.session.flush()

        co2_emission = 0

        # ✅ Handle 'energy' category
        if category == 'energy':
            energy_type = data.get('energy_type')
            energy_amount = data.get('energy_amount')
        
            if not energy_type or energy_amount is None:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'energy_type and energy_amount are required for energy activities'
                }), 400
        
            energy_amount = float(energy_amount)
            energy_unit = data.get('energy_unit', 'kwh').lower()
        
            # ✅ Convert MWh to kWh if needed
            if energy_unit == 'mwh':
                energy_amount = energy_amount * 1000  # Convert to kWh
        
            # Normalize energy_type
            energy_type_key = energy_type.lower().strip()
            emission_factor = ENERGY_EMISSIONS.get(energy_type_key, 0)
        
            if emission_factor == 0:
                print(f"⚠️ Warning: No emission factor found for '{energy_type_key}'")
                print(f"Available types: {list(ENERGY_EMISSIONS.keys())}")
        
            co2_emission = energy_amount * emission_factor

            energy_log = EnergyLog(
                activity_id=activity.id,
                energy_type=energy_type,
                energy_amount=energy_amount,
                energy_unit='kwh',  # Store everything as kWh
                co2_emission=co2_emission
            )
            db.session.add(energy_log)

        # ✅ Handle 'transport' category
        elif category == 'transport':
            vehicle_type = data.get('vehicle_type')
            distance = data.get('distance_km')
            
            if not vehicle_type or distance is None:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'vehicle_type and distance_km are required for transport activities'
                }), 400
            
            distance = float(distance)
            
            # Normalize vehicle_type
            vehicle_type_key = vehicle_type.lower().strip()
            emission_factor = TRANSPORT_EMISSIONS.get(vehicle_type_key, 0)
            
            if emission_factor == 0:
                print(f"⚠️ Warning: No emission factor found for '{vehicle_type_key}'")
                print(f"Available types: {list(TRANSPORT_EMISSIONS.keys())}")
            
            co2_emission = distance * emission_factor

            transport_log = TransportLog(
                activity_id=activity.id,
                vehicle_type=vehicle_type,
                distance=distance,
                co2_emission=co2_emission
            )
            db.session.add(transport_log)

        db.session.commit()
        
        # ✅ Return format matching frontend expectations
        return jsonify({
            'success': True,
            'message': 'Activity logged successfully',
            'activity': {
                'id': activity.id,
                'category': category,
                'notes': notes,
                'timestamp': activity.timestamp.isoformat()
            },
            'emission_kg': round(co2_emission, 2)  # ✅ Round for clean display
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to log activity: {str(e)}'
        }), 500

@activity_bp.route('/activities', methods=['GET'])
@jwt_required()  # ✅ Add authentication
def get_activities():
    """Get all activities for current user"""
    try:
        # Get current user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Filter by user and optionally by category
        category = request.args.get('category')
        
        query = Activity.query.filter_by(user_id=user.id)
        
        if category and category != 'all':
            query = query.filter_by(category=category.capitalize())
        
        activities = query.order_by(Activity.timestamp.desc()).all()
        
        data = []
        for act in activities:
            co2 = 0
            title = act.notes or act.category
            
            # Get CO2 from related logs
            if act.energy_log:
                co2 = act.energy_log.co2_emission
                title = act.notes or act.energy_log.energy_type
            elif act.transport_log:
                co2 = act.transport_log.co2_emission
                title = act.notes or act.transport_log.vehicle_type
            
            entry = {
                "id": act.id,
                "title": title,
                "category": act.category.lower(),  # ✅ Return lowercase to match frontend
                "co2": co2,
                "time": act.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "notes": act.notes,
                "timestamp": act.timestamp.isoformat(),
            }
            
            # Add detailed info
            if act.energy_log:
                entry["details"] = {
                    "energy_type": act.energy_log.energy_type,
                    "energy_amount": act.energy_log.energy_amount,
                    "energy_unit": act.energy_log.energy_unit,
                    "co2_emission": act.energy_log.co2_emission
                }
            elif act.transport_log:
                entry["details"] = {
                    "vehicle_type": act.transport_log.vehicle_type,
                    "distance": act.transport_log.distance,
                    "co2_emission": act.transport_log.co2_emission
                }
            
            data.append(entry)
        
        return jsonify({
            'success': True,
            'data': data
        }), 200
        
    except Exception as e:
        print(f"Error getting activities: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to get activities: {str(e)}'
        }), 500


@activity_bp.route('/activities/<int:activity_id>', methods=['DELETE'])
@jwt_required()  # ✅ Add authentication
def delete_activity(activity_id):
    """Delete activity"""
    try:
        # Get current user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Find activity and verify ownership
        activity = Activity.query.filter_by(id=activity_id, user_id=user.id).first()
        
        if not activity:
            return jsonify({
                'success': False,
                'message': 'Activity not found or unauthorized'
            }), 404

        db.session.delete(activity)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Activity deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting activity: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to delete activity: {str(e)}'
        }), 500


@activity_bp.route('/summary', methods=['GET'])
@jwt_required()  # ✅ Add authentication
def get_summary():
    """Get activity summary for current user"""
    try:
        # Get current user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Get all activities for user
        activities = Activity.query.filter_by(user_id=user.id).all()
        
        total_emissions = 0
        for act in activities:
            if act.energy_log:
                total_emissions += act.energy_log.co2_emission or 0
            elif act.transport_log:
                total_emissions += act.transport_log.co2_emission or 0
        
        count = len(activities)
        average = total_emissions / count if count > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_emissions': round(total_emissions, 2),
                'activities_logged': count,
                'average_impact': round(average, 2)
            }
        }), 200
        
    except Exception as e:
        print(f"Error getting summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to get summary: {str(e)}'
        }), 500