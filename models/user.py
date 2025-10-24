from app import db
from datetime import datetime, timedelta

class User(db.Model):

    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    name = db.Column(db.String(80), nullable=True)  # Short name/display name
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    lifestyle_type = db.Column(db.String(50), nullable=True)  # 'urban', 'suburban', 'rural', etc.
    carbon_goal = db.Column(db.Float, nullable=True, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    carbon = db.relationship('Carbon', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def display_name(self):
        return self.name or self.username
    
    @property
    def active_goals_count(self):

        return self.goals.filter_by(is_active=True).count()
    
    @property
    def total_entries_count(self):
        return self.carbon.count()
    
    @property
    def current_weekly_goal(self):
        return self.goals.filter_by(goal_type='weekly', is_active=True).first()
    
    @property
    def current_monthly_goal(self):
        return self.goals.filter_by(goal_type='monthly', is_active=True).first()
    
    # Instance Methods
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
    
    def get_total_emissions(self, days=30):
        from datetime import timedelta
        start_date = datetime.now().date() - timedelta(days=days)
        
        entries = self.carbon.filter(
            db.text('date >= :start_date')
        ).params(start_date=start_date).all()
        
        return sum(entry.total for entry in entries)
    
    def get_average_daily_emissions(self, days=30):
        total = self.get_total_emissions(days)
        entry_count = self.carbon.filter(
            db.text('date >= :start_date')
        ).params(
            start_date=(datetime.now().date() - timedelta(days=days))
        ).count()
        
        return round(total / entry_count, 2) if entry_count > 0 else 0
    
    def create_default_goals(self):
        from models.goal import Goal
        from datetime import timedelta
        
        today = datetime.now().date()
        goals = []
        
        # Create weekly goal
        weekly_goal = Goal(
            user_id=self.id,
            goal_type='weekly',
            target_value=50.0,  # 50 kg CO2 per week
            start_date=today,
            end_date=today + timedelta(days=7),
            title="Weekly Carbon Goal",
            is_active=True
        )
        goals.append(weekly_goal)
        
        # Create monthly goal
        monthly_goal = Goal(
            user_id=self.id,
            goal_type='monthly',
            target_value=200.0,  # 200 kg CO2 per month
            start_date=today,
            end_date=today + timedelta(days=30),
            title="Monthly Carbon Goal",
            is_active=True
        )
        goals.append(monthly_goal)
        
        return goals
    
    def to_dict(self, include_stats=False):
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'display_name': self.display_name,
            'bio': self.bio,
            'location': self.location,
            'lifestyle_type': self.lifestyle_type,
            'carbon_goal': self.carbon_goal,  # Legacy field
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_stats:
            result['stats'] = {
                'active_goals': self.active_goals_count,
                'total_entries': self.total_entries_count,
                'total_emissions_30d': self.get_total_emissions(30),
                'avg_daily_emissions': self.get_average_daily_emissions(30)
            }
        
        return result
    
    def serialize(self):
        return self.to_dict()
    
    # Representation Methods
    def __repr__(self):
        return f'<User {self.username} ({self.email})>'
    
    def __str__(self):
        return f'{self.display_name} (@{self.username})'