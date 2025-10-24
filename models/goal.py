
from datetime import datetime, timedelta
from app import db



class Goal(db.Model):
    __tablename__ = 'goals'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to User
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Goal configuration
    goal_type = db.Column(
        db.String(20), 
        nullable=False
    )  # 'daily', 'weekly', 'monthly'
    
    target_value = db.Column(
        db.Float, 
        nullable=False
    )  # Target CO2 in kg
    
    # Date range
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_achieved = db.Column(db.Boolean, default=False, nullable=False)
    
    # Optional metadata
    title = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(20), nullable=True)  # Optional: 'transport', 'food', 'energy', or 'all'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    achieved_at = db.Column(db.DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_active', 'user_id', 'is_active'),
        db.Index('idx_goal_type', 'goal_type'),
    )
    
    # Computed Properties
    @property
    def is_expired(self):
        if self.end_date:
            return datetime.now().date() > self.end_date
        return False
    
    @property
    def days_remaining(self):
        if not self.end_date:
            return None
        
        today = datetime.now().date()
        if today > self.end_date:
            return 0
        
        return (self.end_date - today).days
    
    @property
    def duration_days(self):
        if not self.end_date:
            return None
        
        return (self.end_date - self.start_date).days + 1
    
    @property
    def default_title(self):
        if self.title:
            return self.title
        return f"{self.goal_type.capitalize()} Goal: {self.target_value}kg CO2"
    
    # Instance Methods
    def calculate_progress(self, current_value):
        if self.target_value == 0:
            percentage = 0
        else:
            # Progress percentage (100% means at target, >100% means over target)
            percentage = (current_value / self.target_value) * 100
        
        remaining = max(self.target_value - current_value, 0)
        over_under = current_value - self.target_value
        
        return {
            'target': round(self.target_value, 2),
            'current': round(current_value, 2),
            'percentage': round(min(percentage, 100), 1),
            'remaining': round(remaining, 2),
            'over_under': round(over_under, 2),
            'is_met': current_value <= self.target_value,
            'status': 'achieved' if current_value <= self.target_value else 'in_progress'
        }
    
    def mark_achieved(self):
        self.is_achieved = True
        self.achieved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def extend_deadline(self, days):
        if self.end_date:
            self.end_date += timedelta(days=days)
        else:
            self.end_date = datetime.now().date() + timedelta(days=days)
        
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_progress=False, current_value=None):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type,
            'target_value': round(self.target_value, 2),
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'is_achieved': self.is_achieved,
            'is_expired': self.is_expired,
            'title': self.default_title,
            'description': self.description,
            'category': self.category,
            'days_remaining': self.days_remaining,
            'duration_days': self.duration_days,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None
        }
        
        if include_progress and current_value is not None:
            result['progress'] = self.calculate_progress(current_value)
        
        return result
    
    # Static Methods
    @staticmethod
    def get_default_goals():
        return {
            'daily': 8.0,     # 8 kg CO2 per day
            'weekly': 50.0,   # 50 kg CO2 per week  
            'monthly': 200.0  # 200 kg CO2 per month
        }
    
    @staticmethod
    def validate_goal_type(goal_type):
        return goal_type in ['daily', 'weekly', 'monthly']
    
    # Representation Methods
    def __repr__(self):
        status = "✓" if self.is_achieved else "○"
        active = "🟢" if self.is_active else "🔴"
        return f'<Goal {active}{status} {self.goal_type} - {self.target_value} kg CO2>'
    
    def __str__(self):
        return f'{self.default_title}: {self.target_value} kg CO2 ({self.goal_type})'