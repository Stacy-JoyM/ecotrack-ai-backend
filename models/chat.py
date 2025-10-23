# models/chat.py
from app import db
from datetime import datetime

class Chat(db.Model):
    """Stores user-AI chat sessions"""
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
