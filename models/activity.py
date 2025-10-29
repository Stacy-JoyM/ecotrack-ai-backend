from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
from extensions import db

class Activity(db.Model):
    """Base Activity Model"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False) 
    date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    co2_emission = db.Column(db.Float, nullable=True) 
    emission_calculated = db.Column(db.Boolean, default=False)
    
    activity_type = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __mapper_args__ = {
        'polymorphic_identity': 'activity',
        'polymorphic_on': activity_type
    }
    
    @property
    def safe_date(self):
        """Returns a safe datetime for older rows with null date"""
        return self.date or datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'date': self.safe_date.isoformat(),
            'notes': self.notes,
            'co2_emission': self.co2_emission,
            'emission_calculated': self.emission_calculated,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TransportActivity(Activity):
    """Transport Activity Model"""
    __tablename__ = 'transport_activities'
    
    id = db.Column(db.Integer, db.ForeignKey('activities.id'), primary_key=True)
    vehicle_type = db.Column(db.String(20), nullable=False)  
    distance = db.Column(db.Float, nullable=False) 
    vehicle_model = db.Column(db.String(100), nullable=True)
    fuel_efficiency = db.Column(db.Float, nullable=True)  
    __mapper_args__ = {'polymorphic_identity': 'transport'}
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'vehicle_type': self.vehicle_type,
            'distance': self.distance,
            'vehicle_model': self.vehicle_model,
            'fuel_efficiency': self.fuel_efficiency
        })
        return data
    
    def calculate_emission(self):
        if self.vehicle_type == 'petrol':
            liters = (self.distance / 100) * (self.fuel_efficiency or 8)
            self.co2_emission = liters * 2.31
        elif self.vehicle_type == 'electric':
            kwh = (self.distance / 100) * (self.fuel_efficiency or 20)
            self.co2_emission = kwh * 0.5
        self.emission_calculated = True
        return self.co2_emission


class EnergyActivity(Activity):
    """Energy Activity Model"""
    __tablename__ = 'energy_activities'
    
    id = db.Column(db.Integer, db.ForeignKey('activities.id'), primary_key=True)
    energy_type = db.Column(db.String(50), nullable=False)
    usage_kwh = db.Column(db.Float, nullable=False)
    duration_hours = db.Column(db.Float, nullable=True)
    appliance_name = db.Column(db.String(100), nullable=True)
    
    __mapper_args__ = {'polymorphic_identity': 'energy'}
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'energy_type': self.energy_type,
            'usage_kwh': self.usage_kwh,
            'duration_hours': self.duration_hours,
            'appliance_name': self.appliance_name
        })
        return data
    
    def calculate_emission(self):
        emission_factor = 0.5
        self.co2_emission = self.usage_kwh * emission_factor
        self.emission_calculated = True
        return self.co2_emission


def create_transport_activity(user_id, vehicle_type, distance, date=None, notes=None,
                              vehicle_model=None, fuel_efficiency=None):
    activity = TransportActivity(
        user_id=user_id,
        category='transport',
        vehicle_type=vehicle_type,
        distance=distance,
        date=date or datetime.utcnow(),
        notes=notes,
        vehicle_model=vehicle_model,
        fuel_efficiency=fuel_efficiency
    )
    activity.calculate_emission()
    db.session.add(activity)
    db.session.commit()
    return activity


def create_energy_activity(user_id, energy_type, usage_kwh, date=None, notes=None,
                          duration_hours=None, appliance_name=None):
    activity = EnergyActivity(
        user_id=user_id,
        category='energy',
        energy_type=energy_type,
        usage_kwh=usage_kwh,
        date=date or datetime.utcnow(),
        notes=notes,
        duration_hours=duration_hours,
        appliance_name=appliance_name
    )
    activity.calculate_emission()
    db.session.add(activity)
    db.session.commit()
    return activity
