from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from services.user_service import UserService
from datetime import timedelta

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
    """
    Get current user's profile
    Requires: Authorization header with Bearer token
    """
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