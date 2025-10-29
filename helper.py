# helper.py - UPDATED FOR KENYA

# Energy emission factors (kg CO2 per unit)
ENERGY_EMISSIONS = {
    'electricity': 0.25,     # kg CO₂/kWh (Kenya's clean grid: 90%+ renewables)
    'natural gas': 2.75,     # kg CO₂/m³
    'gas': 2.75,             # kg CO₂/m³
    'lpg (cooking gas)': 2.98,  # kg CO₂/kg (accurate)
    'lpg': 2.98,             # kg CO₂/kg
    'kerosene': 2.52,        # kg CO₂/liter (accurate)
    'solar energy': 0.0,     # kg CO₂/kWh (renewable)
    'solar': 0.0,            # kg CO₂/kWh
    'wind energy': 0.0,      # kg CO₂/kWh (renewable)
    'wind': 0.0,             # kg CO₂/kWh
    'biogas': 0.2,           # kg CO₂/m³ (lower emissions)
    'charcoal': 3.7,         # kg CO₂/kg
    'firewood': 1.8,         # kg CO₂/kg
}

# Transport emission factors (kg CO2 per km)
# Note: Kenya's vehicles are typically older, poorly maintained, and less fuel-efficient
TRANSPORT_EMISSIONS = {
    'petrol': 0.25,          # kg CO₂/km (higher for older Kenyan fleet)
    'electric': 0.03,        # kg CO₂/km (Kenya's clean grid makes EVs very low-carbon)
    'diesel': 0.22,          # kg CO₂/km (higher for older Kenyan fleet)
    'hybrid': 0.15,          # kg CO₂/km
    'motorcycle': 0.10,      # kg CO₂/km (bodabodas)
    'bus': 0.12,             # kg CO₂/km per passenger (matatus use more fuel)
    'van_diesel': 0.25,      # kg CO₂/km
    'truck_light': 0.30,     # kg CO₂/km
    'truck_heavy': 0.50,     # kg CO₂/km
}