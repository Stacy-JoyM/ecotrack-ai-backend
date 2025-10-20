from app import db
from datetime import datetime
from typing import Dict, Any


class Conversation(db.Model):
    """Model for storing conversation sessions"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', backref='conversation', lazy=True, cascade='all, delete-orphan')
    context_data = db.relationship('ChatContext', backref='conversation', lazy=True, cascade='all, delete-orphan')
    
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages)
        }


class ChatMessage(db.Model):
    """Model for storing individual chat messages"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message_metadata = db.Column(db.JSON)  # Store additional message metadata
    
    def serialize(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.message_metadata or {}
        }


class ChatContext(db.Model):
    """Model for storing conversation context and user data for AI"""
    __tablename__ = 'chat_contexts'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    context_type = db.Column(db.String(50), nullable=False)  # 'carbon_footprint', 'user_preferences', 'goals', etc.
    context_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def serialize(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'context_type': self.context_type,
            'context_data': self.context_data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class AIRecommendation(db.Model):
    """Model for storing AI-generated recommendations"""
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    recommendation_type = db.Column(db.String(100), nullable=False)  # 'carbon_reduction', 'activity_suggestion', etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    action_items = db.Column(db.JSON)  # List of actionable items
    carbon_impact = db.Column(db.Float)  # Estimated carbon impact
    priority_score = db.Column(db.Float, default=0.0)
    is_read = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'description': self.description,
            'action_items': self.action_items or [],
            'carbon_impact': self.carbon_impact,
            'priority_score': self.priority_score,
            'is_read': self.is_read,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat()
        }
