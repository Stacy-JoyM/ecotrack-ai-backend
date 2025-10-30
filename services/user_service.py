from app import db
from models.user import User


class UserService:
    """Handles all user-related operations like registration, login, and retrieval."""

    def register_user(self, data):
        email = data.get('email')
        password = data.get('password')
        username = data.get('username') 

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return {"message": "User with this email or username already exists", "status": 409}

        new_user = User(
            email=email,
            username=username
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        
        new_user.update_last_login()
        db.session.commit()

        return {"message": "User registered successfully", "status": 201}
 
    def login_user(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return {"message": "Invalid credentials", "status": 401}

        user.update_last_login()
        db.session.commit()

        return {"message": "Login successful", "status": 200}

    def get_user_by_email(self, email):
        """Retrieve a user's details by email."""
        user = User.query.filter_by(email=email).first()
        return user.to_dict() if user else None  
    
    def update_profile(self, email, data):
        """Update user profile information."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {"message": "User not found", "status": 404}
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name']
        if 'bio' in data:
            user.bio = data['bio']
        if 'location' in data:
            user.location = data['location']
        if 'lifestyle_type' in data:
            user.lifestyle_type = data['lifestyle_type']
        if 'carbon_goal' in data:
            user.carbon_goal = data['carbon_goal']
        
        try:
            db.session.commit()
            return {"message": "Profile updated successfully", "status": 200}
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to update profile: {str(e)}", "status": 500}
    
    def change_password(self, email, current_password, new_password):
        """Change user password."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {"message": "User not found", "status": 404}
        
        # Verify current password
        if not user.check_password(current_password):
            return {"message": "Current password is incorrect", "status": 401}
        
        # Update to new password
        user.set_password(new_password)
        
        try:
            db.session.commit()
            return {"message": "Password changed successfully", "status": 200}
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to change password: {str(e)}", "status": 500}
    
    def delete_account(self, email, password):
        """Delete user account (requires password confirmation)."""
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return {"message": "User not found", "status": 404}
        
        # Verify password before deletion
        if not user.check_password(password):
            return {"message": "Incorrect password", "status": 401}
        
        try:
            db.session.delete(user)
            db.session.commit()
            return {"message": "Account deleted successfully", "status": 200}
        except Exception as e:
            db.session.rollback()
            return {"message": f"Failed to delete account: {str(e)}", "status": 500}
