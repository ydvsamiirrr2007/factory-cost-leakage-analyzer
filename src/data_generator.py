import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Create data directory if missing
os.makedirs('data', exist_ok=True)

np.random.seed(42)
random.seed(42)

# ---- Dimensions ----
products = pd.DataFrame({
    'product_id': range(1, 21),
    'product_name': [f'Product_{i}' for i in range(1, 21)],
    'product_category': np.random.choice(['A', 'B', 'C'], 20),
    'standard_cost': np.random.uniform(100, 500, 20),
    'selling_price': np.random.uniform(200, 800, 20)
})

machines = pd.DataFrame({
    'machine_id': range(1, 11),
    'machine_type': np.random.choice(['Press', 'Lathe', 'Mill', 'Grinder'], 10),
    'installation_date': [datetime(2015,1,1) + timedelta(days=np.random.randint(0, 2000)) for _ in range(10)],
    'maintenance_interval_days': np.random.choice([30, 45, 60, 90], 10)
})

suppliers = pd.DataFrame({
    'supplier_id': range(1, 6),
    'supplier_name': [f'Supplier_{chr(65+i)}' for i in range(5)],
    'supplier_rating': np.random.uniform(3.0, 5.0, 5),
    'location': np.random.choice(['Mumbai', 'Delhi', 'Chennai', 'Bangalore'], 5)
})

operators = pd.DataFrame({
    'operator_id': range(1, 51),
    'operator_name': [f'Op_{i}' for i in range(1, 51)],
    'skill_level': np.random.choice(['Low', 'Medium', 'High'], 50, p=[0.2, 0.5, 0.3]),
    'shift_preference': np.random.choice(['Morning', 'Afternoon', 'Night'], 50)
})

# ---- Generate fact records ----
dates = pd.date_range('2025-01-01', '2025-12-31', freq='D')
records = []
for _ in range(5000):
    date = np.random.choice(dates)
    product = products.sample(1).iloc[0]
    machine = machines.sample(1).iloc[0]
    supplier = suppliers.sample(1).iloc[0]
    operator = operators.sample(1).iloc[0]
    shift = np.random.choice(['Morning', 'Afternoon', 'Night'], p=[0.4, 0.35, 0.25])
    department = np.random.choice(['Assembly', 'Machining', 'Painting', 'Welding'])

    planned_qty = np.random.randint(50, 500)
    # Realistic relationships
    machine_age_days = (date - machine['installation_date']).days
    base_downtime = max(0, 0.5 + machine_age_days * 0.001 + np.random.normal(0, 0.5))
    downtime_hrs = max(0, base_downtime + np.random.exponential(0.5))
    actual_qty = max(0, planned_qty - (downtime_hrs * np.random.uniform(2, 5)) + np.random.normal(0, 10))
    actual_qty = int(round(actual_qty))

    standard_material = planned_qty * np.random.uniform(0.5, 2.0)
    supplier_quality_factor = 1 + (5 - supplier['supplier_rating']) * 0.05
    actual_material = standard_material * (1 + np.random.uniform(0.02, 0.15) * supplier_quality_factor)
    material_waste = actual_material - standard_material
    material_cost = actual_material * np.random.uniform(10, 30)

    rejection_base = 0.02 + (machine_age_days / 1000) * 0.01 + downtime_hrs * 0.005
    shift_factor = {'Morning': 1.0, 'Afternoon': 1.1, 'Night': 1.3}[shift]
    rejection_rate = min(0.30, max(0, rejection_base * shift_factor + np.random.normal(0, 0.005)))
    rejected_units = int(round(actual_qty * rejection_rate))
    rework_units = int(rejected_units * np.random.uniform(0.2, 0.6))
    rework_cost = rework_units * np.random.uniform(20, 60)

    maintenance_cost = max(0, 50 + machine_age_days * 0.2 + np.random.normal(0, 100))
    energy_consumption = actual_qty * np.random.uniform(0.3, 1.2) + downtime_hrs * 2
    energy_cost = energy_consumption * np.random.uniform(8, 15)

    shortfall = max(0, planned_qty - actual_qty)
    overtime_hours = (shortfall / 50) * np.random.uniform(0.5, 2) + (shift == 'Night') * 0.5 + np.random.exponential(0.5)
    overtime_cost = overtime_hours * np.random.uniform(250, 500)

    transport_cost = np.random.uniform(100, 1000) + (supplier['location'] == 'Mumbai') * 200

    total_cost = (material_cost + 
                  actual_qty * np.random.uniform(5, 15) + 
                  rework_cost + 
                  maintenance_cost + 
                  energy_cost + 
                  overtime_cost + 
                  transport_cost +
                  downtime_hrs * np.random.uniform(100, 300))

    records.append({
        'date': date,
        'product_id': product['product_id'],
        'machine_id': machine['machine_id'],
        'shift': shift,
        'operator_id': operator['operator_id'],
        'supplier_id': supplier['supplier_id'],
        'department': department,
        'planned_quantity': planned_qty,
        'actual_quantity': actual_qty,
        'production_time_hrs': np.random.uniform(2, 12),
        'standard_material_usage': standard_material,
        'actual_material_usage': actual_material,
        'material_waste': material_waste,
        'material_cost': material_cost,
        'rejected_units': rejected_units,
        'rejection_rate': rejection_rate,
        'rework_units': rework_units,
        'rework_cost': rework_cost,
        'downtime_hrs': downtime_hrs,
        'downtime_reason': np.random.choice(['Breakdown', 'Setup', 'Maintenance', 'No Power'], p=[0.4, 0.3, 0.2, 0.1]),
        'maintenance_cost': maintenance_cost,
        'energy_consumption_kwh': energy_consumption,
        'energy_cost': energy_cost,
        'overtime_hours': overtime_hours,
        'overtime_cost': overtime_cost,
        'transportation_cost': transport_cost,
        'fuel_consumption': transport_cost / np.random.uniform(80, 120),
        'total_production_cost': total_cost
    })

df = pd.DataFrame(records)
df.to_csv('data/raw_factory_data.csv', index=False)
print("✅ Dataset generated with 5,000 records.")