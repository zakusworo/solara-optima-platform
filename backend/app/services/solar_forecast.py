"""
Solar PV Forecasting Service using pvlib

Generates solar generation forecasts based on:
- Location (latitude, longitude, altitude)
- Weather data (TMY, forecast, or clear-sky)
- PV system specifications
- Southern hemisphere optimization
"""
import pvlib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

from app.core.config import settings
from app.models.schemas import SolarForecastResponse, WeatherData


class SolarForecastService:
    """Solar PV generation forecasting service"""
    
    def __init__(
        self,
        latitude: float = None,
        longitude: float = None,
        altitude: float = None,
        timezone: str = None,
    ):
        self.latitude = latitude or settings.LATITUDE
        self.longitude = longitude or settings.LONGITUDE
        self.altitude = altitude or settings.ALTITUDE
        self.timezone = timezone or settings.TIMEZONE
        
        logger.info(
            f"SolarForecastService initialized for Bandung: "
            f"({self.latitude}, {self.longitude}), altitude {self.altitude}m"
        )
    
    def create_pv_system(
        self,
        capacity: float,
        tilt: Optional[float] = None,
        azimuth: float = None,
        module_efficiency: float = None,
        inverter_efficiency: float = None,
        loss_factor: float = None,
    ) -> pvlib.pvsystem.PVSystem:
        """
        Create pvlib PV system object
        
        For southern hemisphere (Indonesia):
        - Optimal azimuth = 0° (North-facing), NOT 180° (South)
        - Tilt angle ≈ latitude for year-round optimization
        """
        
        # Auto-calculate optimal tilt from latitude
        if tilt is None:
            # Optimal tilt for tropical latitudes: latitude * 0.76 + 3.1°
            tilt = abs(self.latitude) * 0.76 + 3.1
            logger.info(f"Auto-calculated tilt angle: {tilt:.1f}°")
        
        # Southern hemisphere: azimuth 0° = North-facing (optimal)
        if azimuth is None:
            azimuth = settings.OPTIMAL_AZIMUTH  # 0° for North
            logger.info(f"Using azimuth: {azimuth}° (North-facing for southern hemisphere)")
        
        # PV system parameters
        module_efficiency = module_efficiency or settings.PV_MODULE_EFFICIENCY
        inverter_efficiency = inverter_efficiency or settings.PV_INVERTER_EFFICIENCY
        loss_factor = loss_factor or settings.PV_LOSS_FACTOR
        
        # Calculate system area from capacity and efficiency
        # Capacity (W) = Area (m²) × Irradiance (1000 W/m²) × Efficiency
        system_area = (capacity * 1000) / (1000 * module_efficiency)
        
        # Create PV system with default parameters
        # Use simplified model for compatibility
        pv_system = pvlib.pvsystem.PVSystem(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            module_parameters={
                'a_ref': 1.5,
                'I_L_ref': 5.0,
                'I_o_ref': 1e-9,
                'R_sh_ref': 100,
                'R_s': 0.5,
                'Adjust': 10,
                'gamma_pdc': -0.004,
            },
            inverter_parameters={
                'pdc0': capacity * 1.1,
                'eta_inv_nom': inverter_efficiency,
                'eta_inv_ref': inverter_efficiency,
            },
            albedo=0.2,
            surface_type='urban',
            module_type='glass_polymer',
        )
        
        logger.info(
            f"PV system created: {capacity}kW, tilt={tilt:.1f}°, azimuth={azimuth}°, "
            f"area={system_area:.1f}m²"
        )
        
        return pv_system, tilt, azimuth
    
    def get_weather_data(
        self,
        start: datetime,
        end: datetime,
        source: str = 'clearsky',
    ) -> pd.DataFrame:
        """
        Get weather data for solar forecasting
        
        Sources:
        - 'clearsky': Clear-sky model (no weather data needed)
        - 'tmy': Typical Meteorological Year
        - 'forecast': Weather API forecast (future implementation)
        - 'historical': Historical weather data
        """
        
        times = pd.date_range(start=start, end=end, freq='h', tz=self.timezone)
        
        if source == 'clearsky':
            logger.info("Using clear-sky model for weather data")
            location = pvlib.location.Location(
                self.latitude,
                self.longitude,
                tz=self.timezone,
                altitude=self.altitude,
            )
            
            # Calculate clear-sky irradiance
            cs = location.get_clearsky(times, model='ineichen')
            
            # Add temperature (typical tropical values)
            cs['temp_air'] = 27 + 5 * np.sin(np.pi * (times.hour - 6) / 12)
            cs['wind_speed'] = 2.5  # m/s
            
            return cs
        
        elif source == 'tmy':
            # Load TMY data if available
            tmy_file = settings.WEATHER_DIR / "bandung_tmy.csv"
            if tmy_file.exists():
                logger.info(f"Loading TMY data from {tmy_file}")
                tmy = pd.read_csv(tmy_file, index_col=0, parse_dates=True)
                return tmy.loc[start:end]
            else:
                logger.warning("TMY file not found, falling back to clear-sky")
                return self.get_weather_data(start, end, source='clearsky')
        
        else:
            logger.warning(f"Unknown weather source '{source}', using clear-sky")
            return self.get_weather_data(start, end, source='clearsky')
    
    def generate_forecast(
        self,
        capacity: float,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        horizon_hours: Optional[int] = None,
        weather_source: str = 'clearsky',
        tilt: Optional[float] = None,
        azimuth: float = None,
    ) -> Dict:
        """
        Generate solar generation forecast
        
        Args:
            capacity: PV system capacity (kW)
            start: Forecast start time
            end: Forecast end time
            horizon_hours: Forecast horizon (hours), alternative to start/end
            weather_source: Weather data source
            tilt: Panel tilt angle (auto-calculated if None)
            azimuth: Panel azimuth angle (0° = North for southern hemisphere)
        
        Returns:
            Dictionary with timestamps, generation, irradiance, temperature
        """
        
        # Determine time range
        if start is None:
            start = datetime.now()
        
        if end is None:
            if horizon_hours:
                end = start + timedelta(hours=horizon_hours)
            else:
                end = start + timedelta(days=1)
        
        logger.info(f"Generating solar forecast: {start} to {end}, capacity={capacity}kW")
        
        # Create PV system
        pv_system, tilt, azimuth = self.create_pv_system(
            capacity=capacity,
            tilt=tilt,
            azimuth=azimuth,
        )
        
        # Get weather data
        weather = self.get_weather_data(start, end, source=weather_source)
        
        # Calculate solar position
        solpos = pvlib.solarposition.get_solarposition(
            time=weather.index,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
        )
        
        # Calculate POA (Plane of Array) irradiance
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt,
            surface_azimuth=azimuth,
            dni=weather['dni'],
            ghi=weather['ghi'],
            dhi=weather['dhi'],
            solar_zenith=solpos['zenith'],
            solar_azimuth=solpos['azimuth'],
        )
        
        # Calculate cell temperature (simplified model)
        # T_cell = T_air + (GPOA/800) × (NOCT - 20)
        NOCT = 45  # Nominal Operating Cell Temperature
        temp_cell = weather['temp_air'] + (poa['poa_global'] / 800) * (NOCT - 20)
        
        # Calculate DC power (simplified model)
        # P_dc = Capacity × (GPOA/1000) × [1 + γ × (Tcell - 25)] × η_module
        gamma_pdc = -0.004  # Temperature coefficient
        
        pdc = capacity * (
            poa['poa_global'] / 1000 * 
            (1 + gamma_pdc * (temp_cell - 25))
        )
        
        # AC output (inverter efficiency with clipping)
        pac = pdc * settings.PV_INVERTER_EFFICIENCY
        
        # Apply inverter clipping at rated capacity
        pac = pac.clip(upper=capacity * 1.1)
        
        # Apply additional losses
        pac = pac * (1 - settings.PV_LOSS_FACTOR)
        
        # Ensure non-negative
        pac = pac.clip(lower=0)
        
        # Prepare results
        timestamps = pac.index.tolist()
        generation = pac.values.tolist()
        
        result = {
            'timestamps': timestamps,
            'generation': [max(0, g) for g in generation],
            'irradiance': weather['ghi'].tolist(),
            'temperature': weather['temp_air'].tolist(),
            'capacity_factor': [g / capacity for g in generation],
            'total_generation': sum(generation),  # kWh (hourly data)
            'peak_generation': max(generation),  # kW
        }
        
        logger.info(
            f"Forecast generated: {result['total_generation']:.1f} kWh total, "
            f"peak: {result['peak_generation']:.2f} kW"
        )
        
        return result
    
    def generate_forecast_response(
        self,
        capacity: float,
        horizon_hours: int = 24,
    ) -> SolarForecastResponse:
        """Generate forecast and return as Pydantic model"""
        
        forecast = self.generate_forecast(
            capacity=capacity,
            horizon_hours=horizon_hours,
        )
        
        return SolarForecastResponse(
            timestamps=forecast['timestamps'],
            generation=forecast['generation'],
            irradiance=forecast['irradiance'],
            temperature=forecast['temperature'],
            capacity_factor=forecast['capacity_factor'],
            total_generation=forecast['total_generation'],
        )
    
    def get_optimal_tilt(self, month: Optional[int] = None) -> float:
        """
        Calculate optimal tilt angle for given month or year-round
        
        For tropical latitudes (like Indonesia):
        - Year-round: latitude × 0.76 + 3.1°
        - Wet season (Nov-Mar): latitude × 0.50
        - Dry season (Apr-Oct): latitude × 0.90
        """
        
        if month is None:
            # Year-round optimization
            tilt = abs(self.latitude) * 0.76 + 3.1
        elif month in [11, 12, 1, 2, 3]:
            # Wet season: lower tilt to capture higher sun
            tilt = abs(self.latitude) * 0.50
        else:
            # Dry season: higher tilt
            tilt = abs(self.latitude) * 0.90
        
        logger.info(f"Optimal tilt for month {month}: {tilt:.1f}°")
        return tilt


# Convenience function
async def generate_solar_forecast(
    capacity: float,
    horizon_hours: int = 24,
    location: Optional[Dict] = None,
) -> SolarForecastResponse:
    """Generate solar forecast with optional location override"""
    
    if location:
        service = SolarForecastService(
            latitude=location.get('latitude'),
            longitude=location.get('longitude'),
            altitude=location.get('altitude'),
        )
    else:
        service = SolarForecastService()
    
    return service.generate_forecast_response(capacity, horizon_hours)
