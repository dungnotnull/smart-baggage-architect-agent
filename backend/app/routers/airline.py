"""Airline policy API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.airline import AirlinePolicy, AirlinePolicyQuery
from app.services.airline_policy import policy_engine
from app.services.airline_scraper import airline_scraper

router = APIRouter()


@router.get("/", response_model=dict)
async def list_airlines() -> dict:
    """List all airlines with available policies."""
    summaries = policy_engine.list_airline_summaries()
    return {
        "airlines": [s.model_dump() for s in summaries],
        "count": len(summaries),
    }


@router.get("/iata-codes")
async def list_iata_codes() -> dict:
    """List only IATA codes for quick lookup."""
    codes = policy_engine.list_available_airlines()
    return {"iata_codes": codes, "count": len(codes)}


@router.get("/{iata_code}", response_model=AirlinePolicy)
async def get_airline_policy(iata_code: str) -> AirlinePolicy:
    """Get baggage policy for a specific airline."""
    try:
        return policy_engine.get_policy(iata_code)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Airline {iata_code} not found")


@router.post("/query")
async def query_airline_policy(query: AirlinePolicyQuery) -> dict:
    """Query airline policy with specific parameters."""
    try:
        return policy_engine.get_baggage_summary(query.iata_code, query.cabin_class)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Airline {query.iata_code} not found")


@router.get("/{iata_code}/freshness")
async def check_policy_freshness(iata_code: str) -> dict:
    """Check if a policy YAML needs updating."""
    return airline_scraper.check_policy_freshness(iata_code)


@router.post("/refresh")
async def refresh_policies() -> dict:
    """Refresh all stale airline policies from web sources."""
    results = airline_scraper.scrape_all_configured()
    updated = 0
    for result in results:
        if "error" not in result:
            changed = airline_scraper.refresh_policy_from_scrape(result["iata_code"], result)
            if changed:
                updated += 1
    return {
        "scraped": len(results),
        "updated": updated,
        "results": results,
    }
