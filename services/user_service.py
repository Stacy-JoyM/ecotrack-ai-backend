from app import db
from models.user import User
from extensions import bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta



class UserService:
    """Handles all user-related operations like registration, login, and retrieval."""

    def register_user(self, data):
        email = data.get('email')
        password = data.get('password')
        username = data.get('username') 

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        # Check if user exists
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return {"message": "User with this email or username already exists", "status": 409}

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            email=email,
            username=username,
            password_hash=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()
        
        # Update last login
        new_user.update_last_login()
        db.session.commit()

        access_token = create_access_token(identity=email, expires_delta=timedelta(hours=6))
        return {"message": "User registered successfully", "access_token": access_token, "status": 201}

    def login_user(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return {"message": "Invalid credentials", "status": 401}

        # Update last login
        user.update_last_login()
        db.session.commit()

        access_token = create_access_token(identity=email, expires_delta=timedelta(hours=6))
        return {"message": "Login successful", "access_token": access_token, "status": 200}

    def get_user_by_email(self, email):
        """Retrieve a user's details by email."""
        user = User.query.filter_by(email=email).first()
        return user.to_dict() if user else None