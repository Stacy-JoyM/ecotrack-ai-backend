from app import db
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(80))
    location = db.Column(db.String(200))
    lifestyle_type = db.Column(db.String(50))
    carbon_goal = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check a given password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "location": self.location,
            "lifestyle_type": self.lifestyle_type,
            "carbon_goal": self.carbon_goal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"
