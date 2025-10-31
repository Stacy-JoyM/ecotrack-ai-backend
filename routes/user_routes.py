from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from services.user_service import UserService
from datetime import timedelta
from models.user import User 
from app import db
from models.activity import Activity

user_bp = Blueprint('user', __name__)
user_service = UserService()


@user_bp.route('/register', methods=['POST'])
def register():
    """
    Register user
    Expected JSON: { "email": "user@example.com", "password": "password123", "username": "john" }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        result = user_service.register_user(data)
        status_code = result.pop('status', 201)
        
        if status_code == 201:
            email = data.get('email')
            
            # Create token
            access_token = create_access_token(
                identity=email, 
                expires_delta=timedelta(hours=6)
            )
            
            # Get user data
            user_data = user_service.get_user_by_email(email)
            
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'access_token': access_token,
                'user': user_data
            }), status_code
        else:
            return jsonify({
                'success': False,
                'message': result.get('message')
            }), status_code
            
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """
    Login user
    Expected JSON: { "email": "user@example.com", "password": "password123" }
    """
    
    try:
        data = request.get_json()
        print(f"1. Received data: {data}")
        
        # Validate we have data
        if not data:
            print("ERROR: No data provided")
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
       
        result = user_service.login_user(data)
        
        status_code = result.pop('status', 200)
        
        # If login failed, return error immediately
        if status_code != 200:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Login failed')
            }), status_code
        
        # Only proceed if login was successful
        email = data.get('email')
        
        # Create access token
        access_token = create_access_token(
            identity=email, 
            expires_delta=timedelta(hours=6)
        )
 
        # Get user data
        user_data = user_service.get_user_by_email(email)
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        

        return jsonify({
            'success': True,
            'message': result.get('message', 'Login successful'),
            'access_token': access_token,
            'user': user_data
        }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500



@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_email = get_jwt_identity()
        user_data = user_service.get_user_by_email(current_user_email)
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    Requires: Authorization header with Bearer token
    Expected JSON: { "name": "John Doe", "carbon_goal": 48.0, "bio": "...", "location": "...", "lifestyle_type": "..." }
    """
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        result = user_service.update_profile(current_user_email, data)
        status_code = result.pop('status', 200)
        
        if status_code == 200:
            # Get updated user data
            user_data = user_service.get_user_by_email(current_user_email)
            
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'user': user_data
            }), status_code
        else:
            return jsonify({
                'success': False,
                'message': result.get('message')
            }), status_code
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500


@user_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current password and new password required'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': 'New password must be at least 6 characters'
            }), 400
        
        result = user_service.change_password(current_user_email, current_password, new_password)
        status_code = result.pop('status', 200)
        
        return jsonify({
            'success': status_code == 200,
            'message': result.get('message')
        }), status_code
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }), 500


@user_bp.route('/profile', methods=['DELETE'])
@jwt_required()
def delete_account():
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        password = data.get('password')
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Password required to confirm account deletion'
            }), 400
        
        result = user_service.delete_account(current_user_email, password)
        status_code = result.pop('status', 200)
        
        return jsonify({
            'success': status_code == 200,
            'message': result.get('message')
        }), status_code
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'Failed to delete account: {str(e)}'
        }), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user (public endpoint - alternative to /register)
    Expected JSON: { "email": "user@example.com", "password": "password123", "username": "john" }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'username']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400
        
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({
                'success': False,
                'message': 'Username already taken'
            }), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            name=data.get('name'),
            bio=data.get('bio'),
            location=data.get('location'),
            lifestyle_type=data.get('lifestyle_type'),
            carbon_goal=data.get('carbon_goal', 0)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.email,
            expires_delta=timedelta(hours=6)
        )
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.name,
                'bio': user.bio,
                'location': user.location,
                'lifestyle_type': user.lifestyle_type,
                'carbon_goal': user.carbon_goal,
                'created_at': user.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to create user: {str(e)}'
        }), 500


@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user details
    Requires: Authorization header with Bearer token
    """
    try:
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get user statistics
        activities = Activity.query.filter_by(user_id=user.id).all()
        total_emissions = 0
        energy_count = 0
        transport_count = 0
        
        for act in activities:
            if act.energy_log:
                total_emissions += act.energy_log.co2_emission or 0
                energy_count += 1
            elif act.transport_log:
                total_emissions += act.transport_log.co2_emission or 0
                transport_count += 1
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'bio': user.bio,
            'location': user.location,
            'lifestyle_type': user.lifestyle_type,
            'carbon_goal': user.carbon_goal,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'statistics': {
                'total_activities': len(activities),
                'energy_activities': energy_count,
                'transport_activities': transport_count,
                'total_emissions_kg': round(total_emissions, 2),
                'average_emission_kg': round(total_emissions / len(activities), 2) if activities else 0
            }
        }
        
        return jsonify({
            'success': True,
            'user': user_data
        }), 200
        
    except Exception as e:
        print(f"Error getting current user: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Failed to get user: {str(e)}'
        }), 500