"""Rule-based packing list generator — combines airline policy + weather + trip duration."""


from app.models.packing import ItemCategory, PackingItem, PackingList
from app.services.airline_policy import policy_engine
from app.services.weather import weather_service

ESSENTIALS: dict[ItemCategory, list[tuple[str, int, int]]] = {
    ItemCategory.documents: [
        ("passport", 1, 50),
        ("boarding_pass", 1, 5),
        ("travel_insurance_card", 1, 5),
        ("driver_license", 1, 20),
        ("vaccination_card", 1, 10),
        ("emergency_contact_card", 1, 5),
        ("hotel_confirmation", 1, 5),
        ("itinerary_printout", 1, 5),
    ],
    ItemCategory.electronics: [
        ("phone_charger", 1, 85),
        ("power_bank", 1, 200),
        ("usb_cable", 1, 30),
        ("travel_adapter", 1, 150),
        ("earbuds", 1, 30),
    ],
    ItemCategory.toiletries: [
        ("toothbrush", 1, 20),
        ("toothpaste_travel", 1, 50),
        ("deodorant_travel", 1, 50),
        ("sunscreen_travel", 1, 100),
        ("lip_balm", 1, 15),
        ("hand_sanitizer", 1, 60),
        ("shampoo_travel", 1, 80),
        ("conditioner_travel", 1, 80),
        ("body_wash_travel", 1, 80),
        ("face_moisturizer_travel", 1, 40),
    ],
}

CLOTHING_BASE: dict[str, dict[str, float]] = {
    "leisure": {
        "tshirt": 1.0, "underwear": 1.0, "socks": 1.0, "pants": 0.5,
        "shorts": 0.3, "pajamas": 0.2, "swimwear": 0.1,
    },
    "business": {
        "dress_shirt": 1.0, "underwear": 1.0, "socks": 1.0, "dress_pants": 0.7,
        "blazer": 0.15, "tie": 0.15, "dress_shoes": 0.1, "pajamas": 0.2,
    },
    "adventure": {
        "tshirt": 1.0, "underwear": 1.0, "socks": 1.5, "hiking_pants": 0.5,
        "fleece": 0.2, "rain_jacket": 0.2, "hiking_boots": 0.1, "swimwear": 0.1,
    },
    "family": {
        "tshirt": 1.0, "underwear": 1.0, "socks": 1.0, "pants": 0.5,
        "shorts": 0.3, "pajamas": 0.2, "rain_jacket": 0.15, "swimwear": 0.1,
    },
}

CLOTHING_WEIGHTS: dict[str, int] = {
    "tshirt": 180, "dress_shirt": 200, "underwear": 50, "socks": 40,
    "pants": 400, "dress_pants": 350, "hiking_pants": 450, "shorts": 150,
    "blazer": 600, "fleece": 350, "rain_jacket": 300, "sweater": 350,
    "jacket": 800, "swimwear": 100, "pajamas": 300, "belt": 50, "tie": 30,
    "dress_shoes": 600, "hiking_boots": 700, "sun_hat": 80, "sunglasses": 30,
    "warm_hat": 60, "gloves": 80, "scarf": 100, "thermal_top": 150,
    "thermal_bottom": 180, "waterproof_shoes": 500,
}

WEATHER_ITEM_MAP: dict[str, tuple[str, ItemCategory, int]] = {
    "Lightweight breathable clothing": ("breathable_shirt", ItemCategory.clothing, 120),
    "Sun hat": ("sun_hat", ItemCategory.clothing, 80),
    "Sunglasses": ("sunglasses", ItemCategory.clothing, 30),
    "T-shirts and light layers": ("light_layer", ItemCategory.clothing, 150),
    "Light jacket for evenings": ("light_jacket", ItemCategory.clothing, 300),
    "Warm layers": ("warm_layer", ItemCategory.clothing, 250),
    "Sweaters": ("sweater", ItemCategory.clothing, 350),
    "Medium jacket": ("medium_jacket", ItemCategory.clothing, 600),
    "Heavy winter coat": ("winter_coat", ItemCategory.clothing, 900),
    "Thermal base layers": ("thermal_top", ItemCategory.clothing, 150),
    "Warm accessories": ("warm_accessories_set", ItemCategory.clothing, 120),
    "Rain jacket or umbrella": ("umbrella", ItemCategory.gear, 300),
    "Waterproof shoes": ("waterproof_shoes", ItemCategory.clothing, 500),
    "SPF 50+ sunscreen": ("sunscreen_spf50", ItemCategory.toiletries, 100),
    "UV-protective clothing": ("uv_shirt", ItemCategory.clothing, 200),
    "Warm pajamas": ("pajamas", ItemCategory.clothing, 300),
    "Thermal socks for sleeping": ("thermal_socks", ItemCategory.clothing, 60),
    "Humid-climate clothing: moisture-wicking fabrics": ("moisture_wicking_shirt", ItemCategory.clothing, 130),
}


class PackingListGenerator:
    """Generate a packing list based on trip parameters."""

    def generate(
        self,
        airline_iata: str,
        destination: str,
        trip_duration_days: int,
        cabin_class: str = "economy",
        activity_type: str = "leisure",
        passenger_count: int = 1,
    ) -> PackingList:
        """Generate a complete packing list."""
        try:
            checked = policy_engine.get_checked_limit(airline_iata, cabin_class)
            weight_limit_g = (checked.get("weight_kg") or 23) * 1000
        except FileNotFoundError:
            weight_limit_g = 23000

        weather_recs: list[str] = []
        try:
            forecast = weather_service.get_forecast_for_city(destination, min(trip_duration_days, 7))
            weather_recs = weather_service.get_clothing_recommendation(forecast)
        except Exception:
            weather_recs = ["Pack versatile layers for variable conditions"]

        items: list[PackingItem] = []
        item_counter = 0

        for category, essentials in ESSENTIALS.items():
            for name, qty, weight in essentials:
                item_counter += 1
                items.append(PackingItem(
                    id=f"item_{item_counter:03d}",
                    name=name,
                    category=category,
                    quantity=max(qty, 1) * passenger_count,
                    weight_grams=weight * passenger_count,
                    is_essential=True,
                ))

        base = CLOTHING_BASE.get(activity_type, CLOTHING_BASE["leisure"])
        for item_name, per_day in base.items():
            quantity = max(1, round(per_day * trip_duration_days))
            quantity = min(quantity, trip_duration_days + 3)
            weight = CLOTHING_WEIGHTS.get(item_name, 200)
            item_counter += 1
            items.append(PackingItem(
                id=f"item_{item_counter:03d}",
                name=item_name,
                category=ItemCategory.clothing,
                quantity=quantity,
                weight_grams=weight * quantity,
            ))

        for rec in weather_recs:
            if rec in WEATHER_ITEM_MAP:
                name, cat, weight = WEATHER_ITEM_MAP[rec]
                if not any(i.name == name for i in items):
                    item_counter += 1
                    items.append(PackingItem(
                        id=f"item_{item_counter:03d}",
                        name=name,
                        category=cat,
                        quantity=1,
                        weight_grams=weight,
                    ))

        if trip_duration_days > 7:
            item_counter += 1
            items.append(PackingItem(
                id=f"item_{item_counter:03d}",
                name="laundry_bag",
                category=ItemCategory.gear,
                quantity=1,
                weight_grams=30,
                notes="For longer trips, plan laundry midway",
            ))

        total_weight = sum(i.weight_grams * i.quantity for i in items if i.weight_grams)
        utilization = round((total_weight / weight_limit_g) * 100, 1) if weight_limit_g else 0

        return PackingList(
            trip_id="",
            items=items,
            total_weight_grams=total_weight,
            weight_limit_grams=int(weight_limit_g),
            weight_utilization_pct=utilization,
        )


packing_generator = PackingListGenerator()
