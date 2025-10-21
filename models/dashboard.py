from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
from app import db

class UserGoal(db.Model):
    """Model for storing user's carbon emission goals"""
    
    __tablename__ = 'user_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    weekly_goal = db.Column(db.Float, nullable=False, default=45.0)  # kg CO2
    monthly_goal = db.Column(db.Float, nullable=False, default=180.0)  # kg CO2
    yearly_goal = db.Column(db.Float, default=2160.0)  # kg CO2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('goal', uselist=False))
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weekly_goal': self.weekly_goal,
            'monthly_goal': self.monthly_goal,
            'yearly_goal': self.yearly_goal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserGoal User:{self.user_id} Weekly:{self.weekly_goal}>'


class NationalAverage(db.Model):
    """Model for storing national average carbon emissions"""
    
    __tablename__ = 'national_averages'
    
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False, index=True)
    average_daily = db.Column(db.Float, nullable=False, default=9.8)  # kg CO2 per day
    year = db.Column(db.Integer, nullable=False, default=datetime.utcnow().year)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'country': self.country,
            'average_daily': self.average_daily,
            'year': self.year,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<NationalAverage {self.country} - {self.average_daily} kg/day>'
