"""Pydantic models for packing list data."""

from enum import StrEnum

from pydantic import BaseModel


class ItemCategory(StrEnum):
    clothing = "clothing"
    electronics = "electronics"
    documents = "documents"
    toiletries = "toiletries"
    gear = "gear"
    other = "other"


class PackingItem(BaseModel):
    """A single item in a packing list."""

    id: str
    name: str
    category: ItemCategory
    quantity: int = 1
    weight_grams: int | None = None
    volume_ml: int | None = None
    is_essential: bool = False
    is_carry_on_compliant: bool = True
    packed: bool = False
    detected_by_vision: bool = False
    notes: str | None = None


class PackingItemUpdate(BaseModel):
    """Update payload for a single packing item."""

    packed: bool | None = None
    quantity: int | None = None
    notes: str | None = None


class PackingList(BaseModel):
    """Complete packing list for a trip."""

    trip_id: str
    items: list[PackingItem] = []
    total_weight_grams: int = 0
    weight_limit_grams: int | None = None
    weight_utilization_pct: float = 0.0


class PackingListOutput(BaseModel):
    """API response for packing list."""

    trip_id: str
    packing_list: PackingList
    llm_advice: str | None = None
    missing_items_alert: list[str] = []
    load_order_suggestion: list[str] | None = None


class VisionDetectionResult(BaseModel):
    """Result from YOLOv8n camera scan."""

    detected_items: list[str] = []
    confidence_scores: list[float] = []
    unmatched_items: list[str] = []
    frame_timestamp: float = 0.0


class CLIPClassificationRequest(BaseModel):
    """Request for server-side CLIP zero-shot classification."""

    image_base64: str
    candidate_labels: list[str]
    top_k: int = 5


class CLIPClassificationResult(BaseModel):
    """Result from CLIP zero-shot classification."""

    label: str
    score: float
