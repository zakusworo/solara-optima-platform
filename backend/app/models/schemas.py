"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GeneratorStatus(str, Enum):
    """Generator operational status"""
    ON = "on"
    OFF = "off"
    STARTING = "starting"
    STOPPING = "stopping"


class GeneratorData(BaseModel):
    """Generator technical and economic parameters"""
    generator_id: int
    name: str
    fuel_type: str = "Natural Gas"
    
    # Technical parameters
    min_output: float = Field(ge=0, description="Minimum output (kW)")
    max_output: float = Field(ge=0, description="Maximum output (kW)")
    ramp_up: float = Field(ge=0, description="Ramp up rate (kW/hour)")
    ramp_down: float = Field(ge=0, description="Ramp down rate (kW/hour)")
    min_uptime: int = Field(ge=0, description="Minimum uptime (hours)")
    min_downtime: int = Field(ge=0, description="Minimum downtime (hours)")
    
    # Initial state
    initial_status: int = Field(ge=0, le=1, description="Initial on/off status")
    initial_output: float = Field(ge=0, description="Initial power output (kW)")
    
    # Economic parameters
    startup_cost: float = Field(ge=0, description="Startup cost (Rp)")
    shutdown_cost: float = Field(ge=0, description="Shutdown cost (Rp)")
    no_load_cost: float = Field(ge=0, description="No-load cost (Rp/hour)")
    fuel_cost: float = Field(ge=0, description="Fuel cost (Rp/kWh)")
    
    # Emissions
    emissions_rate: float = Field(ge=0, description="CO2 emissions rate (kg/kWh)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "generator_id": 1,
                "name": "Gas Turbine 1",
                "fuel_type": "Natural Gas",
                "min_output": 10,
                "max_output": 100,
                "ramp_up": 50,
                "ramp_down": 50,
                "min_uptime": 2,
                "min_downtime": 2,
                "initial_status": 1,
                "initial_output": 50,
                "startup_cost": 500000,
                "shutdown_cost": 0,
                "no_load_cost": 50000,
                "fuel_cost": 800,
                "emissions_rate": 0.45,
            }
        }


class SolarForecast(BaseModel):
    """Solar PV generation forecast"""
    timestamps: List[datetime]
    generation: List[float] = Field(..., description="Expected generation (kW)")
    capacity: float = Field(ge=0, description="Installed capacity (kW)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamps": ["2024-01-01T06:00:00", "2024-01-01T07:00:00"],
                "generation": [0, 5.2],
                "capacity": 100,
            }
        }


class BatteryConfig(BaseModel):
    """Battery energy storage configuration"""
    capacity: float = Field(ge=0, description="Battery capacity (kWh)")
    power_rating: float = Field(ge=0, description="Power rating (kW)")
    efficiency: float = Field(ge=0, le=1, default=0.90, description="Round-trip efficiency")
    min_soc: float = Field(ge=0, le=1, default=0.10, description="Minimum SOC")
    max_soc: float = Field(ge=0, le=1, default=0.90, description="Maximum SOC")
    initial_soc: float = Field(ge=0, le=1, default=0.50, description="Initial SOC (kWh)")
    final_soc: Optional[float] = Field(None, ge=0, le=1, description="Target final SOC (kWh)")
    degradation_cost: float = Field(ge=0, default=100, description="Degradation cost (Rp/kWh)")


class OptimizationRequest(BaseModel):
    """Request for UC/ED optimization"""
    # Time series data
    load_profile: List[float] = Field(..., min_length=1, description="Load profile (kW)")
    timestamps: Optional[List[datetime]] = Field(None, description="Timestamps for load profile")
    
    # Generators
    generators: List[GeneratorData] = Field(..., min_length=1)
    
    # Solar PV
    solar_forecast: Optional[List[float]] = Field(None, description="Solar generation forecast (kW)")
    pv_system_capacity: Optional[float] = Field(None, ge=0, description="PV system capacity (kW)")
    
    # Battery storage
    bess_capacity: float = Field(default=0, ge=0, description="Battery capacity (kWh)")
    bess_power_rating: float = Field(default=0, ge=0, description="Battery power rating (kW)")
    bess_efficiency: float = Field(default=0.90, ge=0, le=1)
    bess_min_soc: float = Field(default=0.10, ge=0, le=1)
    bess_max_soc: float = Field(default=0.90, ge=0, le=1)
    bess_initial_soc: float = Field(default=0.50, ge=0, le=1)
    bess_final_soc: Optional[float] = Field(None, ge=0, le=1)
    bess_degradation_cost: float = Field(default=100, ge=0)
    
    # Market settings
    tou_prices: Optional[List[float]] = Field(None, description="Time-of-use electricity prices (Rp/kWh)")
    grid_import_limit: Optional[float] = Field(None, ge=0, description="Max grid import (kW)")
    grid_export_limit: Optional[float] = Field(None, ge=0, description="Max grid export (kW)")
    
    # Optimization settings
    allow_load_shedding: bool = Field(default=False, description="Allow load shedding")
    load_shedding_cost: float = Field(default=10000, ge=0, description="Load shedding penalty (Rp/kWh)")
    solver_name: str = Field(default="cbc", description="MILP solver name")
    time_limit: int = Field(default=300, ge=1, description="Solver time limit (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "load_profile": [100, 120, 150, 180, 200, 190],
                "generators": [
                    {
                        "generator_id": 1,
                        "name": "Gas Turbine 1",
                        "min_output": 10,
                        "max_output": 100,
                        "ramp_up": 50,
                        "ramp_down": 50,
                        "min_uptime": 2,
                        "min_downtime": 2,
                        "initial_status": 1,
                        "initial_output": 50,
                        "startup_cost": 500000,
                        "shutdown_cost": 0,
                        "no_load_cost": 50000,
                        "fuel_cost": 800,
                        "emissions_rate": 0.45,
                    }
                ],
                "solar_forecast": [0, 0, 5, 20, 35, 40],
                "bess_capacity": 50,
                "bess_power_rating": 25,
            }
        }


class GeneratorSchedule(BaseModel):
    """Generator dispatch schedule"""
    generator_id: int
    status: List[int] = Field(..., description="On/off status (0/1)")
    output: List[float] = Field(..., description="Power output (kW)")
    startup: List[int] = Field(..., description="Startup events (0/1)")
    shutdown: List[int] = Field(..., description="Shutdown events (0/1)")
    reserve: List[float] = Field(..., description="Spinning reserve (kW)")


class BatteryOperation(BaseModel):
    """Battery operation schedule"""
    charge: List[float] = Field(..., description="Charging power (kW)")
    discharge: List[float] = Field(..., description="Discharging power (kW)")
    soc: List[float] = Field(..., description="State of charge (kWh)")


class OptimizationStatus(str, Enum):
    """Optimization solution status"""
    Optimal = "Optimal"
    Feasible = "Feasible"
    Infeasible = "Infeasible"
    Unbounded = "Unbounded"
    NotSolved = "Not Solved"
    TimeLimit = "Time Limit"


class OptimizationResult(BaseModel):
    """Optimization result"""
    status: OptimizationStatus
    total_cost: float = Field(..., description="Total operational cost (Rp)")
    generator_schedules: List[GeneratorSchedule]
    solar_output: Optional[List[float]] = Field(None, description="Solar generation (kW)")
    battery_operation: Optional[BatteryOperation] = Field(None)
    load_served: List[float] = Field(..., description="Load served (kW)")
    emissions: float = Field(default=0, description="Total CO2 emissions (kg)")
    solve_time: float = Field(..., description="Solution time (seconds)")
    messages: Optional[List[str]] = Field(None, description="Solver messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Optimal",
                "total_cost": 15750000,
                "generator_schedules": [
                    {
                        "generator_id": 1,
                        "status": [1, 1, 1, 1, 1, 1],
                        "output": [50, 70, 90, 100, 100, 95],
                        "startup": [0, 0, 0, 0, 0, 0],
                        "shutdown": [0, 0, 0, 0, 0, 0],
                        "reserve": [50, 30, 10, 0, 0, 5],
                    }
                ],
                "solar_output": [0, 0, 5, 20, 35, 40],
                "solve_time": 2.34,
            }
        }


class ForecastRequest(BaseModel):
    """Request for load or solar forecasting"""
    start_date: datetime
    end_date: datetime
    location: Optional[Dict[str, float]] = Field(None, description="Location coordinates")
    historical_data: Optional[List[float]] = Field(None, description="Historical load/generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-02T00:00:00",
                "location": {"latitude": -6.9147, "longitude": 107.6098},
            }
        }


class SolarForecastResponse(BaseModel):
    """Solar generation forecast response"""
    timestamps: List[datetime]
    generation: List[float]
    irradiance: Optional[List[float]] = Field(None, description="Global horizontal irradiance (W/m²)")
    temperature: Optional[List[float]] = Field(None, description="Ambient temperature (°C)")
    capacity_factor: List[float] = Field(..., description="Capacity factor (0-1)")
    total_generation: float = Field(..., description="Total generation (kWh)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamps": ["2024-01-01T06:00:00", "2024-01-01T07:00:00"],
                "generation": [0, 5.2],
                "irradiance": [0, 250],
                "temperature": [25, 27],
                "capacity_factor": [0, 0.052],
                "total_generation": 125.5,
            }
        }


class LoadForecastResponse(BaseModel):
    """Load forecast response"""
    timestamps: List[datetime]
    load: List[float]
    confidence_lower: Optional[List[float]] = Field(None, description="Lower confidence bound")
    confidence_upper: Optional[List[float]] = Field(None, description="Upper confidence bound")
    peak_load: float = Field(..., description="Peak load (kW)")
    total_energy: float = Field(..., description="Total energy (kWh)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamps": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
                "load": [100, 95],
                "peak_load": 200,
                "total_energy": 2400,
            }
        }


class WeatherData(BaseModel):
    """Weather data for solar forecasting"""
    timestamps: List[datetime]
    ghi: List[float] = Field(..., description="Global horizontal irradiance (W/m²)")
    dhi: List[float] = Field(..., description="Diffuse horizontal irradiance (W/m²)")
    dni: List[float] = Field(..., description="Direct normal irradiance (W/m²)")
    temperature: List[float] = Field(..., description="Dry bulb temperature (°C)")
    wind_speed: List[float] = Field(..., description="Wind speed (m/s)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamps": ["2024-01-01T06:00:00"],
                "ghi": [0],
                "dhi": [0],
                "dni": [0],
                "temperature": [25],
                "wind_speed": [2.5],
            }
        }


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
            }
        }
