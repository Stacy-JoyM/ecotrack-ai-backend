
from datetime import datetime
from sqlalchemy import Index, UniqueConstraint
from flask_sqlalchemy import SQLAlchemy
from app import db



class Carbon(db.Model):
    __tablename__ = 'carbon'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Date of the entry
    date = db.Column(
        db.Date, 
        nullable=False, 
        default=lambda: datetime.utcnow().date(),
        index=True
    )
    
    # Carbon emissions by category (in kg CO2)
    transport = db.Column(db.Float, default=0.0, nullable=False)
    energy = db.Column(db.Float, default=0.0, nullable=False)
    
    location = db.Column(db.String(100), nullable=True)  # Optional: track location
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Constraints and indexes
    __table_args__ = (
        # Ensure one entry per user per date
        UniqueConstraint('user_id', 'date', name='unique_user_date'),
        # Composite index for common queries
        Index('idx_user_date', 'user_id', 'date'),
    )
    
    # Properties
    @property
    def total(self):
        """Calculate total CO2 emissions across all categories"""
        return self.transport + self.energy
    
    @property
    def category_percentages(self):
        """Calculate percentage breakdown by category"""
        total = self.total
        if total == 0:
            return {'transport': 0, 'food': 0, 'energy': 0}
        
        return {
            'transport': round((self.transport / total) * 100, 1),
            'energy': round((self.energy / total) * 100, 1)
        }
    
    @property
    def is_high_emission(self, threshold=10.0):
        """Check if daily emissions exceed threshold (default 10kg CO2)"""
        return self.total > threshold
    
    # Methods
    def update_from_dict(self, data):
    
        if 'transport' in data:
            self.transport = float(data['transport'])
        if 'energy' in data:
            self.energy = float(data['energy'])
        if 'notes' in data:
            self.notes = data['notes']
        if 'location' in data:
            self.location = data['location']
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_percentages=False):
        
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'transport': round(self.transport, 2),
            'energy': round(self.energy, 2),
            'total': round(self.total, 2),
            'notes': self.notes,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_percentages:
            result['percentages'] = self.category_percentages
        
        return result
    
    def to_chart_data(self, date_format='%a'):
    
        return {
            'date': self.date.strftime(date_format),
            'transport': round(self.transport, 1),
            'energy': round(self.energy, 1),
            'total': round(self.total, 1)
        }
    
    @staticmethod
    def get_category_totals(entries):
       
        total_transport = sum(entry.transport for entry in entries)
        total_food = sum(entry.food for entry in entries)
        total_energy = sum(entry.energy for entry in entries)
        total = total_transport + total_food + total_energy
        
        return {
            'transport': round(total_transport, 2),
            'food': round(total_food, 2),
            'energy': round(total_energy, 2),
            'total': round(total, 2),
            'percentages': {
                'transport': round((total_transport / total * 100), 1) if total > 0 else 0,
                'energy': round((total_energy / total * 100), 1) if total > 0 else 0
            }
        }
    
    def __repr__(self):
        """String representation of the entry"""
        return f'<Carbon {self.date} - {self.total:.2f} kg CO2>'
    
    def __str__(self):
        """Human-readable string representation"""
        return f'Carbon for {self.date}: {self.total:.2f} kg CO2 (T:{self.transport}, E:{self.energy})'