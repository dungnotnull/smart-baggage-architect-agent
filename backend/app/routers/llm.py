"""LLM API endpoints — generate advice, customs alerts, substitutions."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm_orchestrator import llm_orchestrator

router = APIRouter()


class AdviceRequest(BaseModel):
    """Request for LLM-generated packing advice."""

    destination: str
    trip_duration_days: int
    activity_type: str = "leisure"
    weather_summary: dict | None = None
    airline_summary: dict | None = None


class CustomsAlertRequest(BaseModel):
    """Request for customs restriction check."""

    destination: str
    origin: str = "US"


class SubstitutionRequest(BaseModel):
    """Request for smart substitution suggestions."""

    items: list[dict]


@router.post("/advice")
async def generate_packing_advice(request: AdviceRequest) -> dict:
    """Generate natural-language packing advice for a trip."""
    weather = request.weather_summary or {}
    airline = request.airline_summary or {}
    advice = llm_orchestrator.generate_packing_advice(
        destination=request.destination,
        trip_duration_days=request.trip_duration_days,
        activity_type=request.activity_type,
        weather_summary=weather,
        airline_summary=airline,
    )
    return {"destination": request.destination, "advice": advice}


@router.post("/customs-alert")
async def check_customs(request: CustomsAlertRequest) -> dict:
    """Check for customs-restricted items at a destination."""
    alert = llm_orchestrator.generate_customs_alert(
        destination=request.destination,
        origin=request.origin,
    )
    return {"destination": request.destination, "origin": request.origin, "customs_alert": alert}


@router.post("/substitutions")
async def suggest_substitutions(request: SubstitutionRequest) -> dict:
    """Suggest lighter alternatives for heavy items."""
    suggestions = llm_orchestrator.generate_smart_substitutions(request.items)
    return {"substitutions": suggestions}


@router.post("/generate")
async def generate_text(prompt: str, system: str = "") -> dict:
    """General-purpose LLM text generation endpoint."""
    result = llm_orchestrator.generate(prompt, system)
    return {"result": result}
