"""Tests for airline policy engine."""

from pathlib import Path

import pytest

from app.services.airline_policy import AirlinePolicyEngine

POLICIES_DIR = Path(__file__).resolve().parent.parent / "airline_policies"


class TestAirlinePolicyEngine:
    """Test suite for AirlinePolicyEngine."""

    def test_list_available_airlines(self):
        """Should list all YAML files in airline_policies/."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        airlines = engine.list_available_airlines()
        assert len(airlines) >= 10
        assert "AA" in airlines
        assert "BA" in airlines

    def test_get_policy_aa(self):
        """Should load American Airlines policy."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        policy = engine.get_policy("AA")
        assert policy.iata_code == "AA"
        assert policy.airline_name == "American Airlines"
        assert policy.carry_on.dimensions_cm is not None

    def test_get_policy_case_insensitive(self):
        """Should handle lowercase IATA codes."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        policy = engine.get_policy("ba")
        assert policy.iata_code == "BA"

    def test_get_policy_not_found(self):
        """Should raise FileNotFoundError for unknown airline."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        with pytest.raises(FileNotFoundError):
            engine.get_policy("ZZ")

    def test_get_carry_on_limit(self):
        """Should return carry-on weight and dimensions."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        result = engine.get_carry_on_limit("AA")
        assert "dimensions_cm" in result
        assert "weight_kg" in result

    def test_get_checked_limit(self):
        """Should return checked bag weight by cabin class."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        result = engine.get_checked_limit("AA", "economy")
        assert "weight_kg" in result

    def test_caching(self):
        """Should cache loaded policies."""
        engine = AirlinePolicyEngine(POLICIES_DIR)
        policy1 = engine.get_policy("AA")
        policy2 = engine.get_policy("AA")
        assert policy1 is policy2  # same object reference
