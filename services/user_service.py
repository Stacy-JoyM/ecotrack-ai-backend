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