from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
from app import db

class Activity(db.Model):
    """Base Activity Model"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'transport' or 'energy'
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Carbon emission data
    co2_emission = db.Column(db.Float, nullable=True)  # in kg CO2
    emission_calculated = db.Column(db.Boolean, default=False)
    
    # Polymorphic discrimination
    activity_type = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __mapper_args__ = {
        'polymorphic_identity': 'activity',
        'polymorphic_on': activity_type
    }
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'date': self.date.isoformat(),
            'notes': self.notes,
            'co2_emission': self.co2_emission,
            'emission_calculated': self.emission_calculated,
            'created_at': self.created_at.isoformat()
        }


class TransportActivity(Activity):
    """Transport Activity Model - Electric or Petrol vehicles"""
    __tablename__ = 'transport_activities'
    
    id = db.Column(db.Integer, db.ForeignKey('activities.id'), primary_key=True)
    vehicle_type = db.Column(db.String(20), nullable=False)  # 'electric' or 'petrol'
    distance = db.Column(db.Float, nullable=False)  # in kilometers
    
    # Optional: Vehicle details for more accurate calculations
    vehicle_model = db.Column(db.String(100), nullable=True)
    fuel_efficiency = db.Column(db.Float, nullable=True)  # L/100km for petrol, kWh/100km for electric
    
    __mapper_args__ = {
        'polymorphic_identity': 'transport',
    }
    
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
        """Calculate CO2 emission for transport activity"""
        # Average emission factors
        if self.vehicle_type == 'petrol':
            # Average petrol car: 2.31 kg CO2 per liter
            # Average consumption: 8 L/100km
            if self.fuel_efficiency:
                liters_used = (self.distance / 100) * self.fuel_efficiency
            else:
                liters_used = (self.distance / 100) * 8  # Default 8L/100km
            
            self.co2_emission = liters_used * 2.31  # kg CO2
            
        elif self.vehicle_type == 'electric':
            # Average electric car: 0.5 kg CO2 per kWh (depends on electricity grid)
            # Average consumption: 20 kWh/100km
            if self.fuel_efficiency:
                kwh_used = (self.distance / 100) * self.fuel_efficiency
            else:
                kwh_used = (self.distance / 100) * 20  # Default 20kWh/100km
            
            self.co2_emission = kwh_used * 0.5  # kg CO2
        
        self.emission_calculated = True
        return self.co2_emission


class EnergyActivity(Activity):
    """Energy Activity Model - Various household/office energy usage"""
    __tablename__ = 'energy_activities'
    
    id = db.Column(db.Integer, db.ForeignKey('activities.id'), primary_key=True)
    energy_type = db.Column(db.String(50), nullable=False)  
    # Types: 'home_electricity', 'air_conditioning', 'heating', 'water_heating', 
    #        'office_energy', 'electronics', 'appliances', 'lighting', 'cooking', 'laundry'
    
    usage_kwh = db.Column(db.Float, nullable=False)  # Energy usage in kWh
    
    # Optional: Additional details
    duration_hours = db.Column(db.Float, nullable=True)  # Duration of usage
    appliance_name = db.Column(db.String(100), nullable=True)  # Specific appliance
    
    __mapper_args__ = {
        'polymorphic_identity': 'energy',
    }
    
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
        """Calculate CO2 emission for energy activity"""
        # Global average: 0.5 kg CO2 per kWh
        # This varies by country and electricity grid composition
        # You can make this more accurate by getting country-specific factors
        
        emission_factor = 0.5  # kg CO2 per kWh (global average)
        
        # Country-specific factors (you can expand this)
        country_factors = {
            'US': 0.42,
            'UK': 0.23,
            'DE': 0.35,  # Germany
            'FR': 0.06,  # France (nuclear)
            'CN': 0.58,  # China (coal-heavy)
            'IN': 0.71,  # India
            'KE': 0.35,  # Kenya
        }
        
        # You can get user's country from their profile
        # emission_factor = country_factors.get(user_country, 0.5)
        
        self.co2_emission = self.usage_kwh * emission_factor
        self.emission_calculated = True
        return self.co2_emission


class CarbonEmissionAPI:
    """Service class to interact with external Carbon Emission APIs"""
    
    def __init__(self):
        # You can use APIs like:
        # - CarbonInterface API (https://www.carboninterface.com/)
        # - Climatiq API (https://www.climatiq.io/)
        # - EPA Carbon Footprint API
        self.api_key = os.getenv('CARBON_API_KEY', '')
        self.base_url = os.getenv('CARBON_API_URL', 'https://www.carboninterface.com/api/v1')
    
    def calculate_transport_emission(self, vehicle_type, distance_km, vehicle_model=None):
        """
        Calculate emission using external API for transport
        
        Example using CarbonInterface API
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Map vehicle types
            vehicle_map = {
                'petrol': 'medium_car_petrol',
                'electric': 'medium_car_electric'
            }
            
            payload = {
                'type': 'vehicle',
                'distance_unit': 'km',
                'distance_value': distance_km,
                'vehicle_model_id': vehicle_map.get(vehicle_type, 'medium_car_petrol')
            }
            
            response = requests.post(
                f'{self.base_url}/estimates',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                # API returns emission in kg
                return data['data']['attributes']['carbon_kg']
            else:
                print(f"API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error calling Carbon API: {str(e)}")
            return None
    
    def calculate_energy_emission(self, energy_kwh, country_code='US'):
        """
        Calculate emission using external API for energy consumption
        
        Example using CarbonInterface API
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'type': 'electricity',
                'electricity_unit': 'kwh',
                'electricity_value': energy_kwh,
                'country': country_code
            }
            
            response = requests.post(
                f'{self.base_url}/estimates',
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                return data['data']['attributes']['carbon_kg']
            else:
                print(f"API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error calling Carbon API: {str(e)}")
            return None
    
    def get_emission_factors(self, country_code='US'):
        """
        Get emission factors for a specific country
        """
        # This would call an API endpoint that provides emission factors
        # For now, returning hardcoded values
        factors = {
            'US': {'electricity': 0.42, 'petrol': 2.31},
            'UK': {'electricity': 0.23, 'petrol': 2.31},
            'KE': {'electricity': 0.35, 'petrol': 2.31},
        }
        return factors.get(country_code, {'electricity': 0.5, 'petrol': 2.31})


# Helper functions for activity creation
def create_transport_activity(user_id, vehicle_type, distance, date=None, notes=None, 
                              vehicle_model=None, fuel_efficiency=None, use_api=False):
    """
    Create a transport activity and calculate emissions
    
    Args:
        user_id: User ID
        vehicle_type: 'electric' or 'petrol'
        distance: Distance in km
        date: Activity date (optional)
        notes: Additional notes (optional)
        vehicle_model: Vehicle model (optional)
        fuel_efficiency: Fuel efficiency (optional)
        use_api: Whether to use external API for calculation
    """
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
    
    # Calculate emission
    if use_api:
        api = CarbonEmissionAPI()
        emission = api.calculate_transport_emission(vehicle_type, distance, vehicle_model)
        if emission:
            activity.co2_emission = emission
            activity.emission_calculated = True
        else:
            # Fallback to local calculation
            activity.calculate_emission()
    else:
        activity.calculate_emission()
    
    return activity


def create_energy_activity(user_id, energy_type, usage_kwh, date=None, notes=None,
                          duration_hours=None, appliance_name=None, use_api=False, country_code='US'):
    """
    Create an energy activity and calculate emissions
    
    Args:
        user_id: User ID
        energy_type: Type of energy usage
        usage_kwh: Energy usage in kWh
        date: Activity date (optional)
        notes: Additional notes (optional)
        duration_hours: Duration (optional)
        appliance_name: Appliance name (optional)
        use_api: Whether to use external API for calculation
        country_code: Country code for emission factor
    """
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
    
    # Calculate emission
    if use_api:
        api = CarbonEmissionAPI()
        emission = api.calculate_energy_emission(usage_kwh, country_code)
        if emission:
            activity.co2_emission = emission
            activity.emission_calculated = True
        else:
            # Fallback to local calculation
            activity.calculate_emission()
    else:
        activity.calculate_emission()
    
    return activity


# Example usage and testing
if __name__ == '__main__':
    # Example: Create transport activity
    transport = create_transport_activity(
        user_id=1,
        vehicle_type='petrol',
        distance=50,  # 50 km
        notes='Daily commute'
    )
    print(f"Transport Activity CO2: {transport.co2_emission} kg")
    
    # Example: Create energy activity
    energy = create_energy_activity(
        user_id=1,
        energy_type='air_conditioning',
        usage_kwh=5.5,
        duration_hours=8,
        notes='Office AC usage'
    )
    print(f"Energy Activity CO2: {energy.co2_emission} kg")