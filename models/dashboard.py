from app import db


class Dashboard(db.Model):
    """Basic Dashboard model - placeholder"""
    __tablename__ = 'dashboard'
    
    id = db.Column(db.Integer, primary_key=True)
    
    def serialize(self):
        return {
            'id': self.id
        }
