"""Pydantic models for trip data."""

from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field


def generate_id() -> str:
    return uuid4().hex[:12]


class TripInput(BaseModel):
    """User input for creating a new trip."""

    airline_iata: str = Field(..., min_length=2, max_length=3, description="IATA airline code")
    flight_number: str | None = Field(None, description="Flight number, e.g. 'AA123'")
    origin: str = Field(..., min_length=2, description="Origin city or airport code")
    destination: str = Field(..., min_length=2, description="Destination city or airport code")
    departure_date: date = Field(..., description="Departure date")
    return_date: date = Field(..., description="Return date")
    passenger_count: int = Field(1, ge=1, le=10, description="Number of travelers")
    cabin_class: str = Field("economy", description="economy | business | first")
    activity_type: str = Field("leisure", description="leisure | business | adventure | family")


class TripOutput(BaseModel):
    """Response after creating a trip."""

    trip_id: str
    airline_iata: str
    origin: str
    destination: str
    departure_date: date
    return_date: date
    trip_duration_days: int
    passenger_count: int
    cabin_class: str
    baggage_allowance: dict
    weather_forecast: dict | None = None
    packing_list_id: str | None = None


class TripSummary(BaseModel):
    """Summary of a trip for list views."""

    trip_id: str
    destination: str
    departure_date: date
    return_date: date
    airline_iata: str
    cabin_class: str
    item_count: int
    packed_count: int
    total_weight_grams: int
    weight_limit_grams: int
