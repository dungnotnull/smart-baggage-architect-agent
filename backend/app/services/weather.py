"""Open-Meteo weather integration — 7-day forecast for destination."""

import requests

from app.config import settings


class WeatherService:
    """Fetch weather forecast from Open-Meteo API."""

    def __init__(self, base_url: str | None = None, geocoding_url: str | None = None):
        self.base_url = base_url or settings.open_meteo_base_url
        self.geocoding_url = geocoding_url or settings.geocoding_base_url

    def get_coordinates(self, city: str) -> tuple[float, float]:
        """Geocode a city name using Open-Meteo geocoding API."""
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        resp = requests.get(f"{self.geocoding_url}/search", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            raise ValueError(f"Could not geocode city: {city}")
        return results[0]["latitude"], results[0]["longitude"]

    def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> dict:
        """Fetch 7-day weather forecast from Open-Meteo."""
        daily_fields = (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,wind_speed_10m_max,uv_index_max"
        )
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": daily_fields,
            "timezone": "auto",
            "forecast_days": min(days, 16),
        }
        resp = requests.get(f"{self.base_url}/forecast", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_forecast_for_city(self, city: str, days: int = 7) -> dict:
        """Geocode city then fetch forecast."""
        lat, lon = self.get_coordinates(city)
        return self.get_forecast(lat, lon, days)

    def get_clothing_recommendation(self, forecast: dict) -> list[str]:
        """Generate clothing recommendations from weather data (rule-based)."""
        daily = forecast.get("daily", {})
        recommendations: list[str] = []

        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip_prob = daily.get("precipitation_probability_max", [])
        uv_index = daily.get("uv_index_max", [])

        if not temp_max:
            return ["Pack versatile layers for variable conditions"]

        avg_max = sum(temp_max) / len(temp_max)
        avg_min = sum(temp_min) / len(temp_min) if temp_min else avg_max - 5
        max_precip = max(precip_prob) if precip_prob else 0
        max_uv = max(uv_index) if uv_index else 0

        if avg_max > 30:
            recommendations.extend(["Lightweight breathable clothing", "Sun hat", "Sunglasses"])
        elif avg_max > 20:
            recommendations.extend(["T-shirts and light layers", "Light jacket for evenings"])
        elif avg_max > 10:
            recommendations.extend(["Warm layers", "Sweaters", "Medium jacket"])
        else:
            recommendations.extend(["Heavy winter coat", "Thermal base layers", "Warm accessories"])

        if max_precip > 50:
            recommendations.extend(["Rain jacket or umbrella", "Waterproof shoes"])

        if max_uv > 7:
            recommendations.extend(["SPF 50+ sunscreen", "UV-protective clothing"])

        if avg_min < 5:
            recommendations.extend(["Warm pajamas", "Thermal socks for sleeping"])

        if avg_max > 25 and max_precip > 30:
            recommendations.append("Humid-climate clothing: moisture-wicking fabrics")

        return recommendations

    def get_weather_summary(self, city: str, days: int = 7) -> dict:
        """Get a complete weather summary with recommendations."""
        forecast = self.get_forecast_for_city(city, days)
        daily = forecast.get("daily", {})

        temp_max_list = daily.get("temperature_2m_max", [])
        temp_min_list = daily.get("temperature_2m_min", [])
        precip_list = daily.get("precipitation_probability_max", [])
        uv_list = daily.get("uv_index_max", [])
        dates = daily.get("time", [])

        avg_max = sum(temp_max_list) / len(temp_max_list) if temp_max_list else 0
        avg_min = sum(temp_min_list) / len(temp_min_list) if temp_min_list else 0

        return {
            "city": city,
            "days": days,
            "avg_temp_max_c": round(avg_max, 1),
            "avg_temp_min_c": round(avg_min, 1),
            "max_precip_probability": max(prec_list) if (prec_list := precip_list) else 0,
            "max_uv_index": max(uv_list) if uv_list else 0,
            "dates": dates[:days],
            "daily": daily,
            "recommendations": self.get_clothing_recommendation(forecast),
        }


weather_service = WeatherService()
