from app import db
from datetime import datetime


class User(db.Model):
    """Basic User model - placeholder for actual user implementation"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    lifestyle_type = db.Column(db.String(50), nullable=True)
    carbon_goal = db.Column(db.Float, nullable=True, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'location': self.location,
            'lifestyle_type': self.lifestyle_type,
            'carbon_goal': self.carbon_goal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
