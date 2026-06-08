"""Packing list API endpoints."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from app.models.packing import (
    CLIPClassificationRequest,
    CLIPClassificationResult,
    PackingItemUpdate,
    PackingList,
    PackingListOutput,
)
from app.services.bin_packing import bin_packing_service
from app.services.database import db_service
from app.services.knapsack import knapsack_optimizer
from app.services.packing_list import packing_generator

router = APIRouter()


@router.get("/{trip_id}", response_model=PackingListOutput)
async def get_packing_list(trip_id: str) -> PackingListOutput:
    """Get packing list for a trip."""
    rows = db_service.fetch_all("SELECT * FROM packing_items WHERE trip_id = ?", (trip_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="No packing list found for this trip")

    items = []
    for row in rows:
        from app.models.packing import ItemCategory, PackingItem
        items.append(PackingItem(
            id=row["id"],
            name=row["name"],
            category=ItemCategory(row["category"]),
            quantity=row["quantity"],
            weight_grams=row["weight_grams"],
            is_essential=bool(row["is_essential"]),
            is_carry_on_compliant=bool(row["is_carry_on_compliant"]),
            packed=bool(row["packed"]),
            detected_by_vision=bool(row.get("detected_by_vision", 0)),
            notes=row["notes"],
        ))

    total_weight = sum((i.weight_grams or 0) * i.quantity for i in items)

    trip_row = db_service.fetch_one("SELECT * FROM trips WHERE id = ?", (trip_id,))
    weight_limit = 23000
    if trip_row:
        try:
            from app.services.airline_policy import policy_engine
            checked = policy_engine.get_checked_limit(trip_row["airline_iata"], trip_row["cabin_class"])
            weight_limit = (checked.get("weight_kg") or 23) * 1000
        except FileNotFoundError:
            logger.warning('Airline policy not found, using default 23kg limit')

    packing_list = PackingList(
        trip_id=trip_id,
        items=items,
        total_weight_grams=total_weight,
        weight_limit_grams=weight_limit,
        weight_utilization_pct=round((total_weight / weight_limit) * 100, 1) if weight_limit else 0,
    )

    missing_alert = [item.name for item in items if not item.packed and item.is_essential]

    return PackingListOutput(
        trip_id=trip_id,
        packing_list=packing_list,
        missing_items_alert=missing_alert,
        load_order_suggestion=[item.name for item in items if not item.packed],
    )


@router.put("/{trip_id}/item/{item_id}")
async def update_packing_item(trip_id: str, item_id: str, update: PackingItemUpdate) -> dict:
    """Update a packing item (mark as packed, change quantity, add notes)."""
    row = db_service.fetch_one(
        "SELECT * FROM packing_items WHERE id = ? AND trip_id = ?",
        (item_id, trip_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    if update.packed is not None:
        db_service.execute(
            "UPDATE packing_items SET packed = ? WHERE id = ?",
            (int(update.packed), item_id),
        )
    if update.quantity is not None:
        db_service.execute(
            "UPDATE packing_items SET quantity = ? WHERE id = ?",
            (update.quantity, item_id),
        )
    if update.notes is not None:
        db_service.execute(
            "UPDATE packing_items SET notes = ? WHERE id = ?",
            (update.notes, item_id),
        )

    db_service.commit()
    return {"updated": item_id, "packed": update.packed, "quantity": update.quantity}


@router.post("/{trip_id}/item/{item_id}/detect")
async def mark_item_detected(trip_id: str, item_id: str) -> dict:
    """Mark an item as detected by camera vision scan."""
    row = db_service.fetch_one(
        "SELECT * FROM packing_items WHERE id = ? AND trip_id = ?",
        (item_id, trip_id),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    db_service.execute(
        "UPDATE packing_items SET packed = 1, detected_by_vision = 1 WHERE id = ?",
        (item_id,),
    )
    db_service.commit()
    return {"detected": item_id}


@router.post("/{trip_id}/optimize")
async def optimize_packing(trip_id: str) -> dict:
    """Run Knapsack optimization and bin-packing for a trip's items."""
    rows = db_service.fetch_all("SELECT * FROM packing_items WHERE trip_id = ?", (trip_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="No items found")

    from app.models.packing import ItemCategory, PackingItem
    items = [
        PackingItem(
            id=r["id"], name=r["name"], category=ItemCategory(r["category"]),
            quantity=r["quantity"], weight_grams=r["weight_grams"],
            is_essential=bool(r["is_essential"]),
        )
        for r in rows
    ]

    trip_row = db_service.fetch_one("SELECT * FROM trips WHERE id = ?", (trip_id,))
    weight_limit = 23000
    airline_iata = "AA"
    if trip_row:
        airline_iata = trip_row["airline_iata"]
        try:
            from app.services.airline_policy import policy_engine
            checked = policy_engine.get_checked_limit(airline_iata, trip_row["cabin_class"])
            weight_limit = (checked.get("weight_kg") or 23) * 1000
        except FileNotFoundError:
            logger.warning('Airline policy not found, using default 23kg limit')

    essential_ids = {item.id for item in items if item.is_essential}
    knapsack_result = knapsack_optimizer.optimize(items, weight_limit, essential_ids)
    weight_check = knapsack_optimizer.check_weight_feasibility(items, weight_limit)

    bin_items = [
        {
            "name": item.name,
            "width": 15,
            "height": 10,
            "depth": 5,
            "weight": item.weight_grams or 100,
        }
        for item in items
    ]
    suitcase_dims = bin_packing_service.get_default_suitcase_dims(airline_iata)
    bin_result = bin_packing_service.suggest_load_order(bin_items, suitcase_dims)

    return {
        "trip_id": trip_id,
        "weight_feasibility": weight_check,
        "knapsack_optimization": knapsack_result,
        "bin_packing": bin_result,
    }


@router.post("/{trip_id}/clip-classify", response_model=list[CLIPClassificationResult])
async def clip_classify_item(trip_id: str, request: CLIPClassificationRequest) -> list[CLIPClassificationResult]:
    """Classify an unknown item using server-side CLIP zero-shot."""
    from app.services.clip_fallback import clip_fallback_service
    return clip_fallback_service.classify(request)


@router.post("/regenerate/{trip_id}")
async def regenerate_packing_list(trip_id: str) -> PackingListOutput:
    """Regenerate packing list for an existing trip."""
    trip_row = db_service.fetch_one("SELECT * FROM trips WHERE id = ?", (trip_id,))
    if not trip_row:
        raise HTTPException(status_code=404, detail="Trip not found")

    from datetime import date as date_type
    departure = date_type.fromisoformat(trip_row["departure_date"])
    return_d = date_type.fromisoformat(trip_row["return_date"])
    duration = (return_d - departure).days

    new_list = packing_generator.generate(
        airline_iata=trip_row["airline_iata"],
        destination=trip_row["destination"],
        trip_duration_days=duration,
        cabin_class=trip_row["cabin_class"],
        activity_type=trip_row["activity_type"],
    )
    new_list.trip_id = trip_id

    db_service.execute("DELETE FROM packing_items WHERE trip_id = ?", (trip_id,))
    for item in new_list.items:
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

    missing_alert = [item.name for item in new_list.items if not item.packed and item.is_essential]
    return PackingListOutput(
        trip_id=trip_id,
        packing_list=new_list,
        missing_items_alert=missing_alert,
    )
