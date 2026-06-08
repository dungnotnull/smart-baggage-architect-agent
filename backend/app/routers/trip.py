"""Trip API endpoints -- full CRUD with packing list generation."""

from datetime import date

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.models.packing import PackingListOutput
from app.models.trip import TripInput, TripOutput, TripSummary
from app.services.database import db_service
from app.services.knapsack import knapsack_optimizer
from app.services.packing_list import packing_generator
from app.services.weather import weather_service

router = APIRouter()


class TripCreateResponse(BaseModel):
    """Response for trip creation with full data."""

    trip: TripOutput
    packing_list: PackingListOutput
    weather_summary: dict | None = None


@router.post("/", response_model=TripCreateResponse)
async def create_trip(trip: TripInput) -> TripCreateResponse:
    """Create a new trip, generate packing list, and fetch weather."""
    from app.services.airline_policy import policy_engine

    duration = (trip.return_date - trip.departure_date).days
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Return date must be after departure date")

    trip_id = f"trip_{trip.airline_iata.lower()}_{trip.departure_date.isoformat()}"

    try:
        baggage_allowance = policy_engine.get_baggage_summary(trip.airline_iata, trip.cabin_class)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Airline {trip.airline_iata} not in database")

    weather_summary = None
    try:
        weather_summary = weather_service.get_weather_summary(trip.destination, min(duration, 7))
    except Exception as exc:
        logger.warning("Weather fetch failed for dest={dest}: {err}", dest=trip.destination, err=str(exc))

    packing_list = packing_generator.generate(
        airline_iata=trip.airline_iata,
        destination=trip.destination,
        trip_duration_days=duration,
        cabin_class=trip.cabin_class,
        activity_type=trip.activity_type,
        passenger_count=trip.passenger_count,
    )
    packing_list.trip_id = trip_id

    knapsack_optimizer.check_weight_feasibility(
        packing_list.items, packing_list.weight_limit_grams or 23000
    )

    llm_advice = None
    try:
        from app.services.llm_orchestrator import llm_orchestrator
        if baggage_allowance and weather_summary:
            llm_advice = llm_orchestrator.generate_packing_advice(
                destination=trip.destination,
                trip_duration_days=duration,
                activity_type=trip.activity_type,
                weather_summary=weather_summary,
                airline_summary=baggage_allowance,
            )
    except Exception as exc:
        logger.warning("LLM advice generation failed: {err}", err=str(exc))

    missing_alert = [item.name for item in packing_list.items if not item.packed and item.is_essential]

    trip_output = TripOutput(
        trip_id=trip_id,
        airline_iata=trip.airline_iata,
        origin=trip.origin,
        destination=trip.destination,
        departure_date=trip.departure_date,
        return_date=trip.return_date,
        trip_duration_days=duration,
        passenger_count=trip.passenger_count,
        cabin_class=trip.cabin_class,
        baggage_allowance=baggage_allowance,
        weather_forecast=weather_summary,
        packing_list_id=trip_id,
    )

    packing_output = PackingListOutput(
        trip_id=trip_id,
        packing_list=packing_list,
        llm_advice=llm_advice,
        missing_items_alert=missing_alert,
        load_order_suggestion=[item.name for item in packing_list.items],
    )

    db_service.initialize_schema()
    db_service.execute(
        """INSERT OR REPLACE INTO trips
           (id, airline_iata, flight_number, origin, destination,
            departure_date, return_date, passenger_count, cabin_class, activity_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trip_id, trip.airline_iata, trip.flight_number, trip.origin,
         trip.destination, str(trip.departure_date), str(trip.return_date),
         trip.passenger_count, trip.cabin_class, trip.activity_type),
    )

    for item in packing_list.items:
        db_service.execute(
            """INSERT OR REPLACE INTO packing_items
               (id, trip_id, name, category, quantity, weight_grams,
                is_essential, is_carry_on_compliant, packed, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item.id, trip_id, item.name, item.category.value, item.quantity,
             item.weight_grams, int(item.is_essential), int(item.is_carry_on_compliant),
             int(item.packed), item.notes),
        )

    db_service.commit()
    logger.info("Trip created: {tid}", tid=trip_id)

    return TripCreateResponse(
        trip=trip_output,
        packing_list=packing_output,
        weather_summary=weather_summary,
    )


@router.get("/{trip_id}", response_model=TripOutput)
async def get_trip(trip_id: str) -> TripOutput:
    """Get trip details by ID."""
    row = db_service.fetch_one("SELECT * FROM trips WHERE id = ?", (trip_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")

    from app.services.airline_policy import policy_engine
    try:
        baggage = policy_engine.get_baggage_summary(row["airline_iata"], row["cabin_class"])
    except FileNotFoundError:
        logger.warning("Airline policy not found for {code}", code=row["airline_iata"])
        baggage = {}

    departure = date.fromisoformat(row["departure_date"])
    return_d = date.fromisoformat(row["return_date"])
    duration = (return_d - departure).days

    return TripOutput(
        trip_id=row["id"],
        airline_iata=row["airline_iata"],
        origin=row["origin"],
        destination=row["destination"],
        departure_date=departure,
        return_date=return_d,
        trip_duration_days=duration,
        passenger_count=row["passenger_count"],
        cabin_class=row["cabin_class"],
        baggage_allowance=baggage,
    )


@router.get("/", response_model=list[TripSummary])
async def list_trips() -> list[TripSummary]:
    """List all saved trips."""
    db_service.initialize_schema()
    rows = db_service.fetch_all("SELECT * FROM trips ORDER BY departure_date DESC")
    summaries = []
    for row in rows:
        items = db_service.fetch_all(
            "SELECT * FROM packing_items WHERE trip_id = ?", (row["id"],)
        )
        packed_count = sum(1 for i in items if i["packed"])
        total_weight = sum((i["weight_grams"] or 0) * i["quantity"] for i in items)

        try:
            from app.services.airline_policy import policy_engine
            checked = policy_engine.get_checked_limit(row["airline_iata"], row["cabin_class"])
            weight_limit = (checked.get("weight_kg") or 23) * 1000
        except FileNotFoundError:
            weight_limit = 23000

        departure = date.fromisoformat(row["departure_date"])
        return_d = date.fromisoformat(row["return_date"])

        summaries.append(TripSummary(
            trip_id=row["id"],
            destination=row["destination"],
            departure_date=departure,
            return_date=return_d,
            airline_iata=row["airline_iata"],
            cabin_class=row["cabin_class"],
            item_count=len(items),
            packed_count=packed_count,
            total_weight_grams=total_weight,
            weight_limit_grams=weight_limit,
        ))
    return summaries


@router.delete("/{trip_id}")
async def delete_trip(trip_id: str) -> dict:
    """Delete a trip and all its packing items."""
    row = db_service.fetch_one("SELECT id FROM trips WHERE id = ?", (trip_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")

    db_service.execute("DELETE FROM packing_items WHERE trip_id = ?", (trip_id,))
    db_service.execute("DELETE FROM feedback WHERE trip_id = ?", (trip_id,))
    db_service.execute("DELETE FROM missing_essentials WHERE trip_id = ?", (trip_id,))
    db_service.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    db_service.commit()
    logger.info("Trip deleted: {tid}", tid=trip_id)
    return {"deleted": trip_id}
