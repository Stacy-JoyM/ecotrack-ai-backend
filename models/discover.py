from app import db


class Discover(db.Model):
    """Basic Discover model - placeholder"""
    __tablename__ = 'discover'
    
    id = db.Column(db.Integer, primary_key=True)
    
    def serialize(self):
        return {
            'id': self.id
        }
