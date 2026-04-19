"""
Netlify Function: Solar Forecast
Serverless Python function for pvlib solar forecasting
"""
import json
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.solar_forecast import SolarForecastService


def handler(event, context):
    """
    Netlify Function handler for solar forecasting
    
    Query params: capacity, hours, latitude, longitude
    """
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {})
        
        capacity = float(params.get('capacity', 100))
        hours = int(params.get('hours', 24))
        
        # Optional location override
        latitude = params.get('latitude')
        longitude = params.get('longitude')
        
        # Create service (with optional custom location)
        if latitude and longitude:
            service = SolarForecastService(
                latitude=float(latitude),
                longitude=float(longitude),
            )
        else:
            service = SolarForecastService()
        
        # Generate forecast
        forecast = service.generate_forecast(
            capacity=capacity,
            horizon_hours=hours,
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': {
                    'timestamps': [ts.isoformat() for ts in forecast['timestamps']],
                    'generation': forecast['generation'],
                    'irradiance': forecast['irradiance'],
                    'temperature': forecast['temperature'],
                    'total_generation': forecast['total_generation'],
                    'peak_generation': max(forecast['generation']),
                    'capacity_factor': forecast['capacity_factor'],
                    'location': {
                        'latitude': service.latitude,
                        'longitude': service.longitude,
                    }
                }
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
