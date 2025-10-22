from models.activity import Activity
from app import db
from datetime import datetime

EMISSION_FACTORS = {
    'car_trip': 0.21,
    'bus_ride': 0.08,
    'flight_short': 0.15,
    'electricity_use': 0.475,
    'beef_meal': 2.5,
    'vegetable_meal': 0.5,
}

def calculate_carbon_footprint(activity_type, value=1.0):
    """Calculate carbon footprint based on activity type and optional value."""
    factor = EMISSION_FACTORS.get(activity_type, 0.0)
    return round(factor * value, 2)

def create_activity(user_id, activity_type, value=1.0, activity_date=None):
    """
    Create and save a new activity with auto-calculated carbon footprint.
    
    Args:
        user_id (int): ID of the user
        activity_type (str): e.g., 'car_trip'
        value (float): multiplier (e.g., distance in km, number of meals)
        activity_date (datetime, optional): when the activity happened
    """
    carbon = calculate_carbon_footprint(activity_type, value)
    
    activity = Activity(
        user_id=user_id,
        activity_type=activity_type,
        carbon_footprint=carbon,
        date=activity_date or datetime.utcnow()
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return activity

def get_user_activities(user_id):
    """Get all activities for a user, ordered by date (newest first)."""
    return Activity.query.filter_by(user_id=user_id).order_by(Activity.date.desc()).all()