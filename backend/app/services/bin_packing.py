"""3D Bin-Packing via py3dbp — suggests load order for suitcase packing."""

from loguru import logger
from py3dbp import Bin, Item, Packer


class BinPackingService:
    """3D bin-packing to suggest optimal suitcase load order."""

    def suggest_load_order(
        self,
        items: list[dict],
        suitcase_dims_cm: tuple[float, float, float] = (55, 35, 25),
        max_weight_kg: float = 23.0,
    ) -> dict:
        """Suggest load order for items in a suitcase.

        Args:
            items: List of dicts with keys: name, width, height, depth, weight
            suitcase_dims_cm: (width, height, depth) of suitcase
            max_weight_kg: Maximum weight in kg

        Returns:
            Dict with packed items, unpacked items, and load order.
        """
        packer = Packer()
        w, h, d = suitcase_dims_cm
        packer.add_bin(Bin("suitcase", w, h, d, max_weight_kg * 1000))

        sorted_items = sorted(items, key=lambda x: x.get("weight", 0), reverse=True)

        for item_data in sorted_items:
            packer.add_item(Item(
                item_data["name"],
                item_data.get("width", 15),
                item_data.get("height", 10),
                item_data.get("depth", 5),
                item_data.get("weight", 100),
            ))

        packer.pack()

        packed: list[dict] = []
        for bin_result in packer.bins:
            for fitted_item in bin_result.items:
                packed.append({
                    "name": fitted_item.string(),
                    "position": list(fitted_item.position) if fitted_item.position else [0, 0, 0],
                    "rotation_type": fitted_item.rotation_type,
                    "width": fitted_item.width,
                    "height": fitted_item.height,
                    "depth": fitted_item.depth,
                })

        unpacked_names: list[str] = []
        for bin_result in packer.bins:
            for unfitted_item in bin_result.unfitted_items:
                unpacked_names.append(unfitted_item.string())

        return {
            "packed_items": packed,
            "unpacked_items": unpacked_names,
            "total_packed": len(packed),
            "total_unpacked": len(unpacked_names),
            "load_order": [p["name"] for p in packed],
            "suitcase_dims_cm": list(suitcase_dims_cm),
        }

    def get_default_suitcase_dims(self, airline_iata: str) -> tuple[float, float, float]:
        """Get suitcase dimensions from airline carry-on policy."""
        from app.services.airline_policy import policy_engine

        try:
            carry_on = policy_engine.get_carry_on_limit(airline_iata)
            dims = carry_on.get("dimensions_cm", [])
            if len(dims) >= 3:
                return (dims[0], dims[1], dims[2])
        except FileNotFoundError:
            logger.warning('Airline {} not found, using default suitcase dims', airline_iata)
        return (55, 35, 25)


bin_packing_service = BinPackingService()
