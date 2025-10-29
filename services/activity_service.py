from models.activity import TransportActivity, EnergyActivity
from extensions import db

def create_transport_activity(user_id, vehicle_type, distance=0, notes='', vehicle_model=None, fuel_efficiency=None):
    """Create a transport activity with category and CO2 emission calculated."""
    factor_map = {
        'petrol': 0.21,
        'diesel': 0.25,
        'electric': 0.05,
        'hybrid': 0.15,
        'motorcycle': 0.1,
        'bus': 0.3,
        'van_diesel': 0.28,
        'truck_light': 0.35,
        'truck_heavy': 0.5
    }
    factor = factor_map.get((vehicle_type or '').lower(), 0.0)
    co2_emission = round(factor * (distance or 0), 2)

    activity = TransportActivity(
        user_id=user_id,
        category='transport',        
        vehicle_type=vehicle_type,
        distance=distance,
        vehicle_model=vehicle_model,
        fuel_efficiency=fuel_efficiency,
        notes=notes,
        co2_emission=co2_emission
    )
    db.session.add(activity)
    db.session.commit()
    return activity

def create_energy_activity(user_id, energy_type, usage_kwh=0, notes='', duration_hours=None, appliance_name=None):
    """Create an energy activity with category and CO2 emission calculated."""
    factor_map = {
        'electricity': 0.43,
        'biogas': 0.18,
        'solar': 0.0,
        'gas': 0.25,
        'lpg': 0.24,
        'kerosene': 0.27,
        'wind': 0.0,
        'air_conditioning': 0.5
    }
    factor = factor_map.get((energy_type or '').lower(), 0.3)
    co2_emission = round(factor * (usage_kwh or 0), 2)

    activity = EnergyActivity(
        user_id=user_id,
        category='energy',             # ⚠️ important fix
        energy_type=energy_type,
        usage_kwh=usage_kwh,
        duration_hours=duration_hours,
        appliance_name=appliance_name,
        notes=notes,
        co2_emission=co2_emission
    )
    db.session.add(activity)
    db.session.commit()
    return activity

def get_activity_summary():
    """Return total CO2, activity count, and average impact."""
    activities = TransportActivity.query.all() + EnergyActivity.query.all()
    total_emissions = sum(a.co2_emission or 0 for a in activities)
    activities_logged = len(activities)
    average_impact = total_emissions / activities_logged if activities_logged else 0
    return {
        "total_emissions": round(total_emissions, 2),
        "activities_logged": activities_logged,
        "average_impact": round(average_impact, 2)
    }

def get_activity_history(filter_type='all'):
    """Return activities filtered by type, ordered by date descending."""
    history = []
    if filter_type in ['all', 'transport']:
        history.extend(TransportActivity.query.order_by(TransportActivity.date.desc()).all())
    if filter_type in ['all', 'energy']:
        history.extend(EnergyActivity.query.order_by(EnergyActivity.date.desc()).all())
    return sorted(history, key=lambda x: x.safe_date, reverse=True)

def delete_activity(activity_id):
    """Delete an activity by ID."""
