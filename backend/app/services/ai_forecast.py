"""
AI Forecasting Service using Ollama

Provides load and solar generation forecasting using local LLMs.
Supports multiple models and ensemble forecasting.
"""
import ollama
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger

from app.core.config import settings


class AIForecastingService:
    """AI-powered forecasting using Ollama LLMs"""
    
    def __init__(
        self,
        model: str = None,
        host: str = None,
    ):
        self.model = model or settings.FORECAST_MODEL
        self.host = host or settings.OLLAMA_HOST
        logger.info(f"AIForecastingService initialized with {self.model} at {self.host}")
    
    def check_availability(self) -> bool:
        """Check if Ollama is available and models are loaded"""
        try:
            response = ollama.list()
            models = [m['name'] for m in response.get('models', [])]
            logger.info(f"Available Ollama models: {models}")
            return True
        except Exception as e:
            logger.warning(f"Ollama not available: {str(e)}")
            return False
    
    def generate_load_forecast(
        self,
        historical_data: List[float],
        horizon_hours: int = 24,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate load forecast using LLM pattern recognition
        
        Args:
            historical_data: Historical load values (hourly)
            horizon_hours: Forecast horizon
            context: Additional context (day of week, weather, events)
        
        Returns:
            Dictionary with forecast values and confidence
        """
        
        logger.info(f"Generating AI load forecast: {len(historical_data)} historical points, {horizon_hours}h horizon")
        
        # Prepare prompt
        prompt = self._create_load_forecast_prompt(
            historical_data,
            horizon_hours,
            context,
        )
        
        try:
            # Call Ollama
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
            )
            
            # Parse response
            forecast_text = response.get('response', '')
            forecast_values = self._parse_forecast_response(forecast_text, horizon_hours)
            
            # Calculate confidence (based on pattern consistency)
            confidence = self._estimate_confidence(historical_data, forecast_values)
            
            result = {
                'forecast': forecast_values,
                'confidence': confidence,
                'model': self.model,
                'method': 'LLM pattern recognition',
            }
            
            logger.info(f"AI load forecast generated: {len(forecast_values)} values, confidence={confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"AI load forecasting failed: {str(e)}")
            # Fallback to simple average
            return self._fallback_forecast(historical_data, horizon_hours)
    
    def _create_load_forecast_prompt(
        self,
        historical_data: List[float],
        horizon_hours: int,
        context: Optional[Dict],
    ) -> str:
        """Create prompt for load forecasting"""
        
        # Sample historical data (last 7 days = 168 hours max)
        sample_size = min(len(historical_data), 168)
        sampled_data = historical_data[-sample_size:]
        
        # Format as comma-separated values
        data_str = ', '.join([f'{v:.2f}' for v in sampled_data])
        
        # Build context string
        context_str = ""
        if context:
            if context.get('day_of_week'):
                context_str += f"Day of week: {context['day_of_week']}\n"
            if context.get('weather'):
                context_str += f"Weather: {context['weather']}\n"
            if context.get('temperature'):
                context_str += f"Temperature: {context['temperature']}°C\n"
            if context.get('special_event'):
                context_str += f"Special event: {context['special_event']}\n"
        
        prompt = f"""You are an expert power systems load forecasting AI.

Historical load data (kW), hourly for the past {sample_size} hours:
[{data_str}]

{context_str}
Task: Forecast the next {horizon_hours} hours of load demand.

Consider:
1. Daily patterns (peak hours, nighttime minimum)
2. Weekly patterns (weekday vs weekend)
3. Trends in the historical data
4. Typical load profiles for tropical regions (Indonesia)

Output ONLY a JSON array of {horizon_hours} numbers representing forecasted load in kW.
Format: [value1, value2, value3, ...]

Example output: [95.5, 92.3, 88.7, 85.2, ...]

Forecast:"""
        
        return prompt
    
    def _parse_forecast_response(
        self,
        response_text: str,
        horizon_hours: int,
    ) -> List[float]:
        """Parse LLM response to extract forecast values"""
        
        try:
            # Try to extract JSON array
            import re
            json_match = re.search(r'\[([\d.,\s-]+)\]', response_text)
            if json_match:
                array_str = json_match.group(1)
                values = [float(x.strip()) for x in array_str.split(',') if x.strip()]
                
                # Ensure correct length
                if len(values) >= horizon_hours:
                    return values[:horizon_hours]
                else:
                    # Pad with last value
                    return values + [values[-1]] * (horizon_hours - len(values))
            
            # Fallback: extract all numbers
            numbers = re.findall(r'-?\d+\.?\d*', response_text)
            values = [float(n) for n in numbers[:horizon_hours]]
            
            if len(values) < horizon_hours:
                # Use average
                avg = sum(values) / len(values) if values else 100
                values.extend([avg] * (horizon_hours - len(values)))
            
            return values
            
        except Exception as e:
            logger.error(f"Failed to parse forecast response: {str(e)}")
            return [100.0] * horizon_hours
    
    def _estimate_confidence(
        self,
        historical: List[float],
        forecast: List[float],
    ) -> float:
        """Estimate forecast confidence based on pattern consistency"""
        
        if len(historical) < 48:
            return 0.5  # Low confidence with limited data
        
        # Calculate coefficient of variation in historical data
        hist_mean = np.mean(historical[-48:])
        hist_std = np.std(historical[-48:])
        cv = hist_std / hist_mean if hist_mean > 0 else 1
        
        # Lower CV = higher confidence
        if cv < 0.1:
            return 0.9
        elif cv < 0.2:
            return 0.75
        elif cv < 0.3:
            return 0.6
        else:
            return 0.45
    
    def _fallback_forecast(
        self,
        historical: List[float],
        horizon_hours: int,
    ) -> Dict:
        """Fallback forecasting when AI is unavailable"""
        
        logger.warning("Using fallback forecasting method")
        
        # Use hour-of-day averaging
        if len(historical) >= 24:
            hourly_avg = []
            for h in range(24):
                hour_values = [historical[i] for i in range(h, min(len(historical), 168), 24)]
                hourly_avg.append(np.mean(hour_values) if hour_values else 100)
            
            forecast = [hourly_avg[h % 24] for h in range(horizon_hours)]
        else:
            avg = np.mean(historical) if historical else 100
            forecast = [avg] * horizon_hours
        
        return {
            'forecast': forecast,
            'confidence': 0.5,
            'model': 'fallback',
            'method': 'Hour-of-day averaging',
        }
    
    def generate_solar_forecast_refinement(
        self,
        pvlib_forecast: List[float],
        weather_forecast: Dict,
        horizon_hours: int = 24,
    ) -> Dict:
        """
        Refine pvlib solar forecast using AI weather interpretation
        
        Args:
            pvlib_forecast: Base forecast from pvlib
            weather_forecast: Weather predictions (cloud cover, etc.)
            horizon_hours: Forecast horizon
        
        Returns:
            Refined forecast with uncertainty bounds
        """
        
        logger.info("Refining solar forecast with AI weather analysis")
        
        # Prepare prompt
        prompt = f"""You are a solar generation forecasting expert.

Base pvlib forecast (kW) for {horizon_hours} hours:
{pvlib_forecast}

Weather forecast:
- Cloud cover: {weather_forecast.get('cloud_cover', 'unknown')}
- Temperature: {weather_forecast.get('temperature', 'unknown')}°C
- Humidity: {weather_forecast.get('humidity', 'unknown')}%

Task: Adjust the forecast based on weather conditions.
Consider:
1. Cloud cover reduces generation (thick clouds: 50-80% reduction)
2. High temperature reduces panel efficiency (~0.4%/°C above 25°C)
3. Humidity affects atmospheric transparency

Output JSON with:
{{
  "adjusted_forecast": [values],
  "uncertainty_lower": [lower bounds],
  "uncertainty_upper": [upper bounds],
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
            )
            
            # Parse response
            import re
            json_match = re.search(r'\{.*\}', response.get('response', ''), re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            
        except Exception as e:
            logger.error(f"AI solar refinement failed: {str(e)}")
        
        # Return pvlib forecast with generic uncertainty
        return {
            'adjusted_forecast': pvlib_forecast,
            'uncertainty_lower': [v * 0.8 for v in pvlib_forecast],
            'uncertainty_upper': [v * 1.2 for v in pvlib_forecast],
            'confidence': 0.7,
            'reasoning': 'AI refinement unavailable, using pvlib base forecast',
        }
    
    def compare_forecasting_methods(
        self,
        historical_data: List[float],
        horizon_hours: int = 24,
    ) -> Dict:
        """
        Compare AI forecasting with traditional methods
        
        Returns comparison metrics
        """
        
        logger.info("Comparing forecasting methods")
        
        # AI forecast
        ai_result = self.generate_load_forecast(historical_data, horizon_hours)
        
        # Simple average forecast
        avg_value = np.mean(historical_data[-24:]) if len(historical_data) >= 24 else np.mean(historical_data)
        avg_forecast = [avg_value] * horizon_hours
        
        # Hour-of-day average
        hourly_avg = []
        for h in range(horizon_hours):
            hour_values = [historical_data[i] for i in range(h, len(historical_data), 24)]
            hourly_avg.append(np.mean(hour_values) if hour_values else avg_value)
        
        return {
            'ai_forecast': {
                'values': ai_result['forecast'],
                'confidence': ai_result['confidence'],
                'method': ai_result['method'],
            },
            'simple_average': {
                'values': avg_forecast,
                'method': 'Simple mean',
            },
            'hourly_average': {
                'values': hourly_avg,
                'method': 'Hour-of-day averaging',
            },
        }


# Convenience function
async def generate_ai_load_forecast(
    historical_data: List[float],
    horizon_hours: int = 24,
    context: Optional[Dict] = None,
    model: Optional[str] = None,
) -> Dict:
    """Generate AI load forecast"""
    
    service = AIForecastingService(model=model)
    
    # Check availability
    if not service.check_availability():
        logger.warning("Ollama not available, using fallback")
        return service._fallback_forecast(historical_data, horizon_hours)
    
    return service.generate_load_forecast(historical_data, horizon_hours, context)
