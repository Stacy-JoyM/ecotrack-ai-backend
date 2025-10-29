from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
from app import db

class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # e.g. 'Energy' or 'Transport'
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    energy_log = db.relationship('EnergyLog', backref='activity', uselist=False, cascade="all, delete")
    transport_log = db.relationship('TransportLog', backref='activity', uselist=False, cascade="all, delete")


class EnergyLog(db.Model):
    __tablename__ = 'energy_logs'

    id = db.Column(db.Integer, primary_key=True)
    energy_type = db.Column(db.String(50), nullable=False)
    energy_amount = db.Column(db.Float, nullable=False)
    energy_unit = db.Column(db.String(50), nullable=False)  # e.g. 'kWh'
    co2_emission = db.Column(db.Float, default=0)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)


class TransportLog(db.Model):
    __tablename__ = 'transport_logs'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_type = db.Column(db.String(50), nullable=False)
    distance = db.Column(db.Float, nullable=False)  # e.g. km
    co2_emission = db.Column(db.Float, default=0)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)