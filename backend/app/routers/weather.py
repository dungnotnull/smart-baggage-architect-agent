"""Weather API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from app.services.weather import weather_service

router = APIRouter()


@router.get("/forecast")
async def get_forecast(
    city: str = Query(..., description="Destination city name"),
    days: int = Query(7, ge=1, le=16, description="Forecast days"),
) -> dict:
    """Get weather forecast for a destination city."""
    try:
        forecast = weather_service.get_forecast_for_city(city, days)
        return forecast
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}")


@router.get("/summary")
async def get_weather_summary(
    city: str = Query(..., description="Destination city name"),
    days: int = Query(7, ge=1, le=16, description="Forecast days"),
) -> dict:
    """Get complete weather summary with recommendations."""
    try:
        return weather_service.get_weather_summary(city, days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}")


@router.get("/recommendations")
async def get_clothing_recommendations(
    city: str = Query(..., description="Destination city name"),
) -> dict:
    """Get clothing recommendations based on weather forecast."""
    try:
        forecast = weather_service.get_forecast_for_city(city)
        recs = weather_service.get_clothing_recommendation(forecast)
        return {"city": city, "recommendations": recs}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {e}")


@router.get("/geocode")
async def geocode_city(
    city: str = Query(..., description="City name to geocode"),
) -> dict:
    """Geocode a city name to coordinates."""
    try:
        lat, lon = weather_service.get_coordinates(city)
        return {"city": city, "latitude": lat, "longitude": lon}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
