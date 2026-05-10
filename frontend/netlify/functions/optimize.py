"""
Netlify Function: Run UC/ED Optimization
Serverless Python function for MILP optimization
"""
import json
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.optimizer import run_optimization
from app.models.schemas import OptimizationRequest, GeneratorData


def handler(event, context):
    """
    Netlify Function handler for optimization
    
    Event format:
    {
      "httpMethod": "POST",
      "body": "{\"load_profile\": [...], \"generators\": [...]}"
    }
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Only accept POST
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if 'load_profile' not in body or 'generators' not in body:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required fields: load_profile, generators'
                })
            }
        
        # Build request object
        generators = [GeneratorData(**g) for g in body['generators']]
        
        request = OptimizationRequest(
            load_profile=body['load_profile'],
            generators=generators,
            pv_system_capacity=body.get('pv_system_capacity'),
            bess_capacity=body.get('bess_capacity', 0),
            bess_power_rating=body.get('bess_power_rating', 0),
        )
        
        # Run optimization
        result = run_optimization(request)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': {
                    'status': result.status,
                    'total_cost': result.total_cost,
                    'solve_time': result.solve_time,
                    'generator_schedules': [s.model_dump() for s in result.generator_schedules],
                    'solar_output': result.solar_output,
                    'battery_operation': result.battery_operation.model_dump() if result.battery_operation else None,
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
