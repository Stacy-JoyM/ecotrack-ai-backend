from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token  # ✅ Add this
from services.user_service import UserService

user_bp = Blueprint('user', __name__)
user_service = UserService()

@user_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    Expected JSON: { "email": "user@example.com", "password": "password123", "name": "John Doe" }
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
        
        # Format response based on status
        if status_code == 201:
            # Get the user to create token
            user_data = user_service.get_user_by_email(data.get('email'))
            
            # Create access token using user email as identity
            access_token = create_access_token(identity=data.get('email'))
            
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'access_token': access_token,  # ✅ Changed from 'token' to 'access_token'
                'user': user_data
            }), status_code
        else:
            return jsonify({
                'success': False,
                'message': result.get('message')
            }), status_code
            
    except Exception as e:
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
        
        # First validate login credentials
        result = user_service.login_user(data)
        status_code = result.pop('status', 200)
        
        # Format response based on status
        if status_code == 200:
            # Create access token using email as identity
            access_token = create_access_token(identity=data.get('email'))
            
            return jsonify({
                'success': True,
                'message': result.get('message'),
                'access_token': access_token,  # ✅ Changed from 'token' to 'access_token'
                'user': user_service.get_user_by_email(data.get('email'))
            }), status_code
        else:
            return jsonify({
                'success': False,
                'message': result.get('message')
            }), status_code
            
    except Exception as e:
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
            'message': f'Failed to fetch profile: {str(e)}'
        }), 500


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    Expected JSON: { "name": "New Name", "bio": "My bio", "location": "City", ... }
    """
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        from models.user import User
        from app import db
        
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Update allowed fields
        allowed_fields = ['name', 'bio', 'location', 'lifestyle_type', 'carbon_goal']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500


@user_bp.route('/profile/stats', methods=['GET'])
@jwt_required()
def get_profile_stats():
    """
    Get user profile with statistics
    Requires: Authorization header with Bearer token
    """
    try:
        current_user_email = get_jwt_identity()
        
        from models.user import User
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict(include_stats=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch profile stats: {str(e)}'
        }), 500


@user_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if the token is valid
    Requires: Authorization header with Bearer token
    """
    try:
        current_user_email = get_jwt_identity()
        user_data = user_service.get_user_by_email(current_user_email)
        
        if not user_data:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Token is valid',
            'user': user_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Invalid or expired token'
        }), 401


@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (client-side should remove token)
    Requires: Authorization header with Bearer token
    """
    try:
        # In a JWT system, logout is mainly client-side (remove token)
        # You could implement token blacklisting here if needed
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500


# Optional: Password change endpoint
@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    Expected JSON: { "current_password": "old123", "new_password": "new123" }
    """
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'Current password and new password are required'
            }), 400
        
        from models.user import User
        from app import db
        from flask_bcrypt import Bcrypt
        
        bcrypt = Bcrypt()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Verify current password
        if not bcrypt.check_password_hash(user.password_hash, data['current_password']):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 401
        
        # Set new password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }), 500

