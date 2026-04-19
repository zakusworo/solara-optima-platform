#!/usr/bin/env python3
"""
Generate sample data and visualizations for Solar UC/ED Platform
"""
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Generate sample load profile (24 hours, typical Indonesian commercial)
def generate_load_profile():
    hours = 24
    load = []
    
    for h in range(hours):
        if 0 <= h < 6:
            base = 60
        elif 6 <= h < 9:
            base = 80 + (h-6) * 10
        elif 9 <= h < 12:
            base = 120 + (h-9) * 10
        elif 12 <= h < 14:
            base = 140 - (h-12) * 10  # Lunch dip
        elif 14 <= h < 18:
            base = 120 + (h-14) * 10
        elif 18 <= h < 21:
            base = 160 - (h-18) * 10
        else:
            base = 130 - (h-21) * 20
        
        load.append(round(base + np.random.normal(0, 3), 1))
    
    return load

# Generate sample solar generation (clear day, Bandung)
def generate_solar_profile():
    # 6 AM to 6 PM (12 hours of daylight)
    hours = list(range(6, 19))
    generation = []
    
    for h in hours:
        # Bell curve for solar generation
        peak_hour = 12
        distance_from_peak = abs(h - peak_hour)
        gen = 80 * np.exp(-0.5 * (distance_from_peak / 3)**2)
        generation.append(round(gen, 1))
    
    return hours, generation

# Create sample optimization result
def create_sample_result():
    load = generate_load_profile()
    hours, solar = generate_solar_profile()
    
    # Extend solar to 24 hours
    solar_24h = [0]*6 + solar + [0]*11
    
    # Sample generator dispatch
    gas_turbine = []
    for i in range(24):
        net_load = load[i] - solar_24h[i]
        dispatch = max(10, min(200, net_load))  # Within generator limits
        gas_turbine.append(round(dispatch, 1))
    
    result = {
        "status": "Optimal",
        "total_cost": 3408912,
        "solve_time": 0.02,
        "load_profile": load,
        "solar_output": solar_24h,
        "generator_dispatch": gas_turbine,
        "total_solar_generation": sum(solar_24h),
        "peak_solar": max(solar_24h),
    }
    
    return result

# Save sample data
data_dir = Path("~/projects/solar-uc-ed-platform/data").expanduser()
data_dir.mkdir(parents=True, exist_ok=True)

# Save load profile
load_profile = generate_load_profile()
with open(data_dir / "sample_load_profile.json", "w") as f:
    json.dump({
        "timestamps": [(datetime.now() + timedelta(hours=h)).isoformat() for h in range(24)],
        "load_kw": load_profile,
        "peak_kw": max(load_profile),
        "average_kw": sum(load_profile) / 24,
        "total_kwh": sum(load_profile),
    }, f, indent=2)

print(f"✓ Sample load profile saved: {data_dir / 'sample_load_profile.json'}")

# Save solar profile
hours, solar_gen = generate_solar_profile()
with open(data_dir / "sample_solar_profile.json", "w") as f:
    json.dump({
        "location": "Bandung, Indonesia",
        "latitude": -6.9147,
        "longitude": 107.6098,
        "capacity_kw": 100,
        "tilt_deg": 8.4,
        "azimuth_deg": 0,
        "hourly_generation_kw": dict(zip(hours, solar_gen)),
        "total_kwh": sum(solar_gen),
        "peak_kw": max(solar_gen),
        "capacity_factor": sum(solar_gen) / (100 * len(hours)),
    }, f, indent=2)

print(f"✓ Sample solar profile saved: {data_dir / 'sample_solar_profile.json'}")

# Save optimization result
result = create_sample_result()
with open(data_dir / "sample_optimization_result.json", "w") as f:
    json.dump(result, f, indent=2)

print(f"✓ Sample optimization result saved: {data_dir / 'sample_optimization_result.json'}")

# Print summary
print("\n" + "="*60)
print("Sample Data Summary")
print("="*60)
print(f"\nLoad Profile:")
print(f"  Peak: {max(load_profile):.1f} kW")
print(f"  Average: {sum(load_profile)/24:.1f} kW")
print(f"  Total: {sum(load_profile):.1f} kWh")

print(f"\nSolar Generation:")
print(f"  Peak: {max(solar_gen):.1f} kW")
print(f"  Total: {sum(solar_gen):.1f} kWh")
print(f"  Capacity Factor: {sum(solar_gen)/(100*len(hours))*100:.1f}%")

print(f"\nOptimization Result:")
print(f"  Status: {result['status']}")
print(f"  Total Cost: Rp {result['total_cost']:,.0f}")
print(f"  Solve Time: {result['solve_time']:.2f}s")

print("\n" + "="*60)
print("Sample data ready for visualization!")
print("="*60)
