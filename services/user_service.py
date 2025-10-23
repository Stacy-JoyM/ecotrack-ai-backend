from app import db
from models.user import User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta

bcrypt = Bcrypt()

class UserService:
    """Handles all user-related operations like registration, login, and retrieval."""

    def register_user(self, data):
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {"message": "User already exists", "status": 409}

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, name=name, password_hash=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        token = create_access_token(identity=email, expires_delta=timedelta(hours=6))
        return {"message": "User registered successfully", "token": token, "status": 201}

    def login_user(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {"message": "Email and password required", "status": 400}

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return {"message": "Invalid credentials", "status": 401}

        token = create_access_token(identity=email, expires_delta=timedelta(hours=6))
        return {"message": "Login successful", "token": token, "status": 200}

    def get_user_by_email(self, email):
        """Retrieve a user’s details by email."""
        user = User.query.filter_by(email=email).first()
        return user.serialize() if user else None
