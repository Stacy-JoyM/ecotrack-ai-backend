from models.activity import Activity
from extensions import db

def log_activity(data):
    """
    Save a new eco activity to the database.
    Required fields: user_id, category
    Optional: description, latitude, longitude
    """
    activity = Activity(
        user_id=data['user_id'],
        category=data['category'],
        description=data.get('description', ''),
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )
    db.session.add(activity)
    db.session.commit()
    return activity.serialize()

def get_user_activities(user_id):
    """
    Retrieve all activities for a given user, sorted by most recent.
    """
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.timestamp.desc()).all()
    return [a.serialize() for a in activities]
