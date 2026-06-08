"""Tests for weather service."""

from unittest.mock import MagicMock, patch

from app.services.weather import WeatherService


class TestWeatherService:
    """Test suite for WeatherService."""

    def test_get_clothing_recommendation_hot(self):
        """Should recommend lightweight clothing for hot weather."""
        service = WeatherService()
        forecast = {
            "daily": {
                "temperature_2m_max": [35, 34, 33, 36, 35, 34, 35],
                "temperature_2m_min": [25, 24, 25, 26, 25, 24, 25],
                "precipitation_probability_max": [10, 5, 10, 5, 10, 5, 10],
                "uv_index_max": [8, 9, 8, 9, 8, 9, 8],
            }
        }
        recs = service.get_clothing_recommendation(forecast)
        assert "Lightweight breathable clothing" in recs
        assert "SPF 50+ sunscreen" in recs

    def test_get_clothing_recommendation_cold(self):
        """Should recommend warm clothing for cold weather."""
        service = WeatherService()
        forecast = {
            "daily": {
                "temperature_2m_max": [5, 3, 4, 6, 5, 3, 4],
                "temperature_2m_min": [-2, -5, -3, -1, -2, -5, -3],
                "precipitation_probability_max": [20, 30, 20, 20, 20, 30, 20],
                "uv_index_max": [2, 1, 2, 2, 2, 1, 2],
            }
        }
        recs = service.get_clothing_recommendation(forecast)
        assert "Heavy winter coat" in recs

    def test_get_clothing_recommendation_rainy(self):
        """Should recommend rain gear for high precipitation."""
        service = WeatherService()
        forecast = {
            "daily": {
                "temperature_2m_max": [20, 19, 20, 21, 20, 19, 20],
                "temperature_2m_min": [14, 13, 14, 15, 14, 13, 14],
                "precipitation_probability_max": [80, 90, 85, 70, 80, 90, 85],
                "uv_index_max": [3, 2, 3, 3, 3, 2, 3],
            }
        }
        recs = service.get_clothing_recommendation(forecast)
        assert "Rain jacket or umbrella" in recs

    def test_get_clothing_recommendation_empty(self):
        """Should return default when no forecast data."""
        service = WeatherService()
        forecast = {"daily": {}}
        recs = service.get_clothing_recommendation(forecast)
        assert len(recs) > 0  # Should have fallback recommendations

    @patch("app.services.weather.requests.get")
    def test_get_coordinates(self, mock_get):
        """Should geocode a city name."""
        service = WeatherService()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"latitude": 10.82, "longitude": 106.63, "name": "Ho Chi Minh City"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        lat, lon = service.get_coordinates("Ho Chi Minh City")
        assert lat == 10.82
        assert lon == 106.63
