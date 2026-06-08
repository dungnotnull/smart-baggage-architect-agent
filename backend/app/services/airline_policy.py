"""Airline Policy Engine — loads YAML files and queries baggage policies."""

from pathlib import Path

import yaml

from app.config import settings
from app.models.airline import AirlinePolicy, AirlinePolicySummary, CarryOnPolicy, CheckedBagPolicy


class AirlinePolicyEngine:
    """Load and query airline baggage policies from YAML files."""

    def __init__(self, policies_dir: Path | None = None):
        self.policies_dir = policies_dir or Path(settings.airline_policies_dir)
        self._cache: dict[str, AirlinePolicy] = {}

    def _load_policy(self, iata_code: str) -> AirlinePolicy:
        """Load a single airline policy from YAML."""
        yaml_path = self.policies_dir / f"{iata_code.upper()}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"No policy YAML for airline {iata_code}")

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return AirlinePolicy(
            iata_code=data["iata_code"],
            airline_name=data["airline_name"],
            region=data["region"],
            last_verified=data["last_verified"],
            source_url=data["source_url"],
            carry_on=CarryOnPolicy(**data.get("carry_on", {})),
            checked=CheckedBagPolicy(**data.get("checked", {})),
            overweight_fees=data.get("overweight_fees"),
            special_items=data.get("special_items"),
            elite_benefits=data.get("elite_benefits"),
        )

    def get_policy(self, iata_code: str) -> AirlinePolicy:
        """Get airline policy, with caching."""
        code = iata_code.upper()
        if code not in self._cache:
            self._cache[code] = self._load_policy(code)
        return self._cache[code]

    def list_available_airlines(self) -> list[str]:
        """List all IATA codes with available YAML policies."""
        return sorted(p.stem for p in self.policies_dir.glob("*.yaml"))

    def list_airline_summaries(self) -> list[AirlinePolicySummary]:
        """List brief summaries of all airlines."""
        summaries = []
        for code in self.list_available_airlines():
            try:
                policy = self.get_policy(code)
                summaries.append(
                    AirlinePolicySummary(
                        iata_code=policy.iata_code,
                        airline_name=policy.airline_name,
                        region=policy.region,
                        carry_on_weight_kg=policy.carry_on.weight_kg,
                        checked_weight_kg=policy.checked.weight_kg_economy,
                    )
                )
            except Exception:
                continue
        return summaries

    def get_carry_on_limit(self, iata_code: str) -> dict:
        """Get carry-on weight and dimension limits."""
        policy = self.get_policy(iata_code)
        return {
            "weight_kg": policy.carry_on.weight_kg,
            "dimensions_cm": policy.carry_on.dimensions_cm,
            "personal_item": policy.carry_on.personal_item,
            "personal_item_dimensions_cm": policy.carry_on.personal_item_dimensions_cm,
        }

    def get_checked_limit(self, iata_code: str, cabin_class: str = "economy") -> dict:
        """Get checked bag weight limit by cabin class."""
        policy = self.get_policy(iata_code)
        checked = policy.checked
        weight_map = {
            "economy": checked.weight_kg_economy,
            "business": checked.weight_kg_business,
            "first": checked.weight_kg_first,
        }
        return {
            "weight_kg": weight_map.get(cabin_class, checked.weight_kg_economy),
            "dimensions_cm": checked.dimensions_cm,
            "fees": {
                "first_bag_domestic_usd": checked.fee_first_bag_economy_domestic_usd,
                "first_bag_international_usd": checked.fee_first_bag_economy_international_usd,
                "second_bag_domestic_usd": checked.fee_second_bag_economy_domestic_usd,
                "second_bag_international_usd": checked.fee_second_bag_economy_international_usd,
            },
            "overweight_fees": policy.overweight_fees,
        }

    def get_baggage_summary(self, iata_code: str, cabin_class: str = "economy") -> dict:
        """Get complete baggage summary for a flight."""
        carry_on = self.get_carry_on_limit(iata_code)
        checked = self.get_checked_limit(iata_code, cabin_class)
        policy = self.get_policy(iata_code)
        return {
            "airline": policy.airline_name,
            "iata_code": policy.iata_code,
            "cabin_class": cabin_class,
            "carry_on": carry_on,
            "checked": checked,
            "special_items": policy.special_items,
            "elite_benefits": policy.elite_benefits,
        }

    def invalidate_cache(self, iata_code: str | None = None) -> None:
        """Clear cached policies. If iata_code given, clear only that entry."""
        if iata_code:
            self._cache.pop(iata_code.upper(), None)
        else:
            self._cache.clear()


policy_engine = AirlinePolicyEngine()
