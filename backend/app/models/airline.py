"""Pydantic models for airline policy data."""

from pydantic import BaseModel, Field


class CarryOnPolicy(BaseModel):
    """Carry-on baggage policy."""

    weight_kg: float | None = None
    dimensions_cm: list[float] = Field(default_factory=list, description="[H, W, D]")
    personal_item: bool = True
    personal_item_dimensions_cm: list[float] | None = None


class CheckedBagPolicy(BaseModel):
    """Checked baggage policy."""

    weight_kg_economy: float | None = None
    weight_kg_business: float | None = None
    weight_kg_first: float | None = None
    dimensions_cm: list[float] | None = None
    fee_first_bag_economy_domestic_usd: float | None = None
    fee_first_bag_economy_international_usd: float | None = None
    fee_second_bag_economy_domestic_usd: float | None = None
    fee_second_bag_economy_international_usd: float | None = None


class AirlinePolicy(BaseModel):
    """Complete airline baggage policy."""

    iata_code: str
    airline_name: str
    region: str
    last_verified: str
    source_url: str
    carry_on: CarryOnPolicy
    checked: CheckedBagPolicy
    overweight_fees: dict | None = None
    special_items: dict | None = None
    elite_benefits: dict | None = None


class AirlinePolicyQuery(BaseModel):
    """Query for airline policy lookup."""

    iata_code: str = Field(..., min_length=2, max_length=3)
    cabin_class: str = "economy"
    route_type: str = "domestic"


class AirlinePolicySummary(BaseModel):
    """Brief airline policy for list views."""

    iata_code: str
    airline_name: str
    region: str
    carry_on_weight_kg: float | None
    checked_weight_kg: float | None
