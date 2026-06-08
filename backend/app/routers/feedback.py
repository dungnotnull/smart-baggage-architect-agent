"""Feedback API endpoints — post-trip feedback loop."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.database import db_service
from app.services.feedback import feedback_service

router = APIRouter()


class FeedbackInput(BaseModel):
    """Input for submitting item feedback."""

    trip_id: str
    item_name: str
    item_id: str | None = None
    was_used: bool = True
    rating: int | None = None


class MissingEssentialInput(BaseModel):
    """Input for submitting a missing essential item."""

    trip_id: str
    item_name: str
    category: str | None = None
    destination: str | None = None
    activity_type: str | None = None


@router.post("/item")
async def submit_feedback(input_data: FeedbackInput) -> dict:
    """Submit feedback for a single item after a trip."""
    db_service.initialize_schema()
    result = feedback_service.submit_feedback(
        trip_id=input_data.trip_id,
        item_name=input_data.item_name,
        item_id=input_data.item_id,
        was_used=input_data.was_used,
        rating=input_data.rating,
    )
    return result


@router.post("/missing")
async def submit_missing_essential(input_data: MissingEssentialInput) -> dict:
    """Submit an item the user wished they had packed."""
    db_service.initialize_schema()
    result = feedback_service.submit_missing_essential(
        trip_id=input_data.trip_id,
        item_name=input_data.item_name,
        category=input_data.category,
        destination=input_data.destination,
        activity_type=input_data.activity_type,
    )
    return result


@router.get("/trip/{trip_id}")
async def get_trip_feedback(trip_id: str) -> dict:
    """Get all feedback and missing essentials for a trip."""
    db_service.initialize_schema()
    feedback = feedback_service.get_trip_feedback(trip_id)
    missing = feedback_service.get_trip_missing_essentials(trip_id)
    return {"feedback": feedback, "missing_essentials": missing}


@router.get("/adaptive/{destination}")
async def get_adaptive_profile(destination: str, activity_type: str = "leisure") -> dict:
    """Get adaptive packing profile based on historical feedback for a destination."""
    db_service.initialize_schema()
    profile = feedback_service.get_packing_profile(activity_type, destination)
    return profile


@router.post("/batch")
async def submit_batch_feedback(trip_id: str, items: list[FeedbackInput]) -> dict:
    """Submit feedback for multiple items at once."""
    db_service.initialize_schema()
    results = []
    for item in items:
        result = feedback_service.submit_feedback(
            trip_id=item.trip_id,
            item_name=item.item_name,
            item_id=item.item_id,
            was_used=item.was_used,
            rating=item.rating,
        )
        results.append(result)
    return {"submitted": len(results), "results": results}
