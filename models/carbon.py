from app import db
from datetime import datetime


class Carbon(db.Model):
    """Basic Carbon model - placeholder for actual carbon implementation"""
    __tablename__ = 'carbon'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    monthly_footprint = db.Column(db.Float, nullable=True, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'monthly_footprint': self.monthly_footprint,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
