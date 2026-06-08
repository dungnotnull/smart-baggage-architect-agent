"""Tests for 3D bin-packing service."""

from app.services.bin_packing import BinPackingService


class TestBinPackingService:
    """Test suite for BinPackingService."""

    def test_basic_packing(self):
        """Should pack items into suitcase."""
        service = BinPackingService()
        items = [
            {"name": "book", "width": 15, "height": 2, "depth": 20, "weight": 300},
            {"name": "tshirt", "width": 25, "height": 2, "depth": 20, "weight": 180},
        ]
        result = service.suggest_load_order(items)
        assert "packed_items" in result
        assert "load_order" in result

    def test_empty_items(self):
        """Should handle empty item list."""
        service = BinPackingService()
        result = service.suggest_load_order([])
        assert result["total_packed"] == 0

    def test_custom_suitcase_size(self):
        """Should accept custom suitcase dimensions."""
        service = BinPackingService()
        items = [
            {"name": "item1", "width": 10, "height": 10, "depth": 10, "weight": 500},
        ]
        result = service.suggest_load_order(items, suitcase_dims_cm=(40, 30, 20))
        assert result["total_packed"] >= 1
