"""Tests for packing list generator."""

from unittest.mock import patch

from app.models.packing import ItemCategory
from app.services.packing_list import PackingListGenerator


class TestPackingListGenerator:
    """Test suite for PackingListGenerator."""

    @patch("app.services.packing_list.weather_service")
    @patch("app.services.packing_list.policy_engine")
    def test_generate_basic_trip(self, mock_policy, mock_weather):
        """Should generate packing list for a basic leisure trip."""
        mock_policy.get_carry_on_limit.return_value = {"weight_kg": None, "dimensions_cm": [56, 36, 23]}
        mock_policy.get_checked_limit.return_value = {"weight_kg": 23, "dimensions_cm": [158]}
        mock_weather.get_forecast_for_city.return_value = {"daily": {}}
        mock_weather.get_clothing_recommendation.return_value = ["Pack versatile layers for variable conditions"]

        gen = PackingListGenerator()
        result = gen.generate(
            airline_iata="AA",
            destination="Tokyo",
            trip_duration_days=5,
            cabin_class="economy",
            activity_type="leisure",
        )

        assert len(result.items) > 0
        assert result.total_weight_grams > 0
        assert result.weight_limit_grams == 23000

    @patch("app.services.packing_list.weather_service")
    @patch("app.services.packing_list.policy_engine")
    def test_essentials_always_included(self, mock_policy, mock_weather):
        """Essential items should always be in the packing list."""
        mock_policy.get_carry_on_limit.return_value = {"weight_kg": None, "dimensions_cm": [56, 36, 23]}
        mock_policy.get_checked_limit.return_value = {"weight_kg": 23, "dimensions_cm": [158]}
        mock_weather.get_forecast_for_city.return_value = {"daily": {}}
        mock_weather.get_clothing_recommendation.return_value = []

        gen = PackingListGenerator()
        result = gen.generate(
            airline_iata="BA",
            destination="London",
            trip_duration_days=3,
        )

        essential_names = {item.name for item in result.items if item.is_essential}
        assert "passport" in essential_names
        assert "phone_charger" in essential_names
        assert "toothbrush" in essential_names

    @patch("app.services.packing_list.weather_service")
    @patch("app.services.packing_list.policy_engine")
    def test_longer_trip_more_clothes(self, mock_policy, mock_weather):
        """Longer trips should generate more clothing items."""
        mock_policy.get_carry_on_limit.return_value = {"weight_kg": None, "dimensions_cm": [56, 36, 23]}
        mock_policy.get_checked_limit.return_value = {"weight_kg": 23, "dimensions_cm": [158]}
        mock_weather.get_forecast_for_city.return_value = {"daily": {}}
        mock_weather.get_clothing_recommendation.return_value = []

        gen = PackingListGenerator()
        short = gen.generate("AA", "NYC", 3)
        long = gen.generate("AA", "NYC", 14)

        short_clothing = [i for i in short.items if i.category == ItemCategory.clothing]
        long_clothing = [i for i in long.items if i.category == ItemCategory.clothing]
        assert sum(i.quantity for i in long_clothing) > sum(i.quantity for i in short_clothing)

    @patch("app.services.packing_list.weather_service")
    @patch("app.services.packing_list.policy_engine")
    def test_airline_not_found_uses_defaults(self, mock_policy, mock_weather):
        """Should use default weight limit if airline not found."""
        mock_policy.get_carry_on_limit.side_effect = FileNotFoundError
        mock_weather.get_forecast_for_city.return_value = {"daily": {}}
        mock_weather.get_clothing_recommendation.return_value = []

        gen = PackingListGenerator()
        result = gen.generate("ZZ", "Paris", 5)
        assert result.weight_limit_grams == 23000  # default fallback
