#!/usr/bin/env python3
"""
Test script for Solar UC/ED Platform API
"""
import sys
import json

# Test imports
print("=" * 60)
print("Solar UC/ED Platform - API Test Suite")
print("=" * 60)
print()

try:
    from app.main import app
    print("✓ Backend import successful")
except Exception as e:
    print(f"✗ Backend import failed: {e}")
    sys.exit(1)

try:
    from app.services.optimizer import UCEDOptimizer
    print("✓ Optimizer service loaded")
except Exception as e:
    print(f"✗ Optimizer import failed: {e}")

try:
    from app.services.solar_forecast import SolarForecastService
    print("✓ Solar forecast service loaded")
except Exception as e:
    print(f"✗ Solar forecast import failed: {e}")

try:
    from app.services.ai_forecast import AIForecastingService
    print("✓ AI forecast service loaded")
except Exception as e:
    print(f"✗ AI forecast import failed: {e}")

print()
print("=" * 60)
print("Testing Optimization Engine")
print("=" * 60)
print()

# Test optimization
from app.models.schemas import OptimizationRequest, GeneratorData
from app.services.optimizer import run_optimization

# Create test request
load_profile = [
    80, 75, 70, 65, 60, 65,
    85, 100, 120, 130, 125, 120,
    115, 110, 115, 125, 140, 160,
    170, 165, 150, 130, 110, 95,
]

generators = [
    GeneratorData(
        generator_id=1,
        name="Gas Turbine 1",
        fuel_type="Natural Gas",
        min_output=10,
        max_output=200,  # Increased to meet peak load
        ramp_up=100,
        ramp_down=100,
        min_uptime=2,
        min_downtime=2,
        initial_status=1,
        initial_output=100,
        startup_cost=500000,
        shutdown_cost=0,
        no_load_cost=50000,
        fuel_cost=800,
        emissions_rate=0.45,
    )
]

request = OptimizationRequest(
    load_profile=load_profile,
    generators=generators,
    pv_system_capacity=100,
    bess_capacity=50,
    bess_power_rating=25,
)

print(f"Load profile: {len(load_profile)} hours")
print(f"Generators: {len(generators)}")
print(f"Solar capacity: {request.pv_system_capacity} kW")
print(f"Battery: {request.bess_capacity} kWh / {request.bess_power_rating} kW")
print()

try:
    print("Running optimization...")
    result = run_optimization(request)
    print(f"✓ Optimization completed!")
    print(f"  Status: {result.status}")
    print(f"  Total cost: Rp {result.total_cost:,.0f}")
    print(f"  Solve time: {result.solve_time:.2f}s")
    print(f"  Solar generation: {sum(result.solar_output)/1000:.1f} kWh" if result.solar_output else "")
except Exception as e:
    print(f"✗ Optimization failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Testing Solar Forecast")
print("=" * 60)
print()

try:
    service = SolarForecastService()
    # Use fixed datetime for consistent testing (noon on equinox)
    from datetime import datetime
    forecast = service.generate_forecast(
        capacity=100,
        start=datetime(2024, 3, 21, 6, 0),  # Spring equinox, 6 AM
        end=datetime(2024, 3, 21, 18, 0),   # 6 PM - full daylight
    )
    print(f"✓ Solar forecast generated")
    print(f"  Total generation: {forecast['total_generation']:.1f} kWh")
    print(f"  Peak power: {max(forecast['generation'])/1000:.2f} kW")
    print(f"  Location: Bandung ({service.latitude}°S, {service.longitude}°E)")
except Exception as e:
    print(f"✗ Solar forecast failed: {e}")

print()
print("=" * 60)
print("All Tests Complete")
print("=" * 60)
