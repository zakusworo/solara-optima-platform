"""
Location management API with geocoding and reverse geocoding
Uses Nominatim (OpenStreetMap) - free, no API key required
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

from app.core.config import settings

router = APIRouter()


class LocationData(BaseModel):
    latitude: float
    longitude: float
    altitude: float = 0
    timezone: str = "Asia/Jakarta"
    name: str = "Custom Location"


class GeocodeResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    altitude: float = 0


# In-memory location store (refreshed on restart)
current_location = {
    "latitude": settings.LATITUDE,
    "longitude": settings.LONGITUDE,
    "altitude": settings.ALTITUDE,
    "timezone": settings.TIMEZONE,
    "name": "Bandung, Indonesia",
}


def get_geolocator():
    return Nominatim(user_agent="solara-optima-platform/1.0")


@router.get("/current")
async def get_current_location():
    """Get currently configured location"""
    return {
        "success": True,
        "data": current_location,
        "message": f"Current location: {current_location['name']}",
    }


@router.post("/update")
async def update_location(location: LocationData):
    """Update application location settings"""
    global current_location
    current_location = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "altitude": location.altitude,
        "timezone": location.timezone,
        "name": location.name,
    }
    settings.LATITUDE = location.latitude
    settings.LONGITUDE = location.longitude
    settings.ALTITUDE = location.altitude
    settings.TIMEZONE = location.timezone

    hemisphere = "southern" if location.latitude < 0 else "northern"
    optimal_azimuth = 0.0 if location.latitude < 0 else 180.0

    return {
        "success": True,
        "data": {
            **current_location,
            "hemisphere": hemisphere,
            "optimal_azimuth": optimal_azimuth,
            "optimal_tilt": abs(location.latitude) * 0.76 + 3.1,
        },
        "message": f"Location updated to {location.name}",
    }


@router.get("/geocode")
async def geocode_address(
    q: str = Query(..., description="Address or place name to search")
):
    """Geocode an address to lat/lon using Nominatim (OpenStreetMap)"""
    try:
        geolocator = get_geolocator()
        location = geolocator.geocode(q, language="en", exactly_one=False)
        if not location:
            return {
                "success": False,
                "data": None,
                "message": f"No results found for '{q}'",
            }
        results = []
        for loc in location[:5]:
            results.append({
                "name": loc.address,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "altitude": getattr(loc, 'altitude', 0) or 0,
            })
        return {
            "success": True,
            "data": results,
            "message": f"Found {len(results)} result(s) for '{q}'",
        }
    except GeocoderTimedOut:
        raise HTTPException(status_code=504, detail="Geocoding timed out")
    except GeocoderServiceError as e:
        raise HTTPException(status_code=503, detail=f"Geocoding service error: {str(e)}")


@router.get("/reverse")
async def reverse_geocode(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """Reverse geocode lat/lon to address using Nominatim"""
    try:
        geolocator = get_geolocator()
        location = geolocator.reverse(f"{lat}, {lon}", language="en")
        if not location:
            return {
                "success": False,
                "data": None,
                "message": "No address found for these coordinates",
            }
        return {
            "success": True,
            "data": {
                "name": location.address,
                "latitude": lat,
                "longitude": lon,
            },
            "message": location.address,
        }
    except GeocoderTimedOut:
        raise HTTPException(status_code=504, detail="Reverse geocoding timed out")
    except GeocoderServiceError as e:
        raise HTTPException(status_code=503, detail=f"Geocoding service error: {str(e)}")


@router.get("/timezone")
async def get_timezone(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """Get timezone from coordinates using free API"""
    try:
        url = f"https://api.wheretheiss.at/v1/coordinates/{lat},{lon}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            timezone = data.get("timezone_id", "UTC")
            return {
                "success": True,
                "data": {"timezone": timezone, "latitude": lat, "longitude": lon},
                "message": f"Timezone: {timezone}",
            }
        return {
            "success": True,
            "data": {"timezone": "UTC", "latitude": lat, "longitude": lon},
            "message": "Defaulting to UTC (API unavailable)",
        }
    except Exception as e:
        return {
            "success": True,
            "data": {"timezone": "UTC", "latitude": lat, "longitude": lon},
            "message": f"Defaulting to UTC: {str(e)}",
        }


@router.get("/search")
async def search_places(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Max results", ge=1, le=10)
):
    """Search places interactively via Nominatim"""
    try:
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        resp = requests.get(
            nominatim_url,
            params={
                "q": q,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
                "accept-language": "en",
            },
            headers={"User-Agent": "solara-optima-platform/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = []
        for item in resp.json():
            results.append({
                "name": item.get("display_name", ""),
                "latitude": float(item.get("lat", 0)),
                "longitude": float(item.get("lon", 0)),
                "type": item.get("type", ""),
                "class": item.get("class", ""),
            })
        return {
            "success": True,
            "data": results,
            "message": f"Found {len(results)} result(s)",
        }
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Search service unavailable")
