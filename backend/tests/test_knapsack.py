"""Tests for knapsack optimizer."""

from app.models.packing import ItemCategory, PackingItem
from app.services.knapsack import KnapsackOptimizer


class TestKnapsackOptimizer:
    """Test suite for KnapsackOptimizer."""

    def test_basic_optimization(self):
        """Should select items that fit within weight budget."""
        optimizer = KnapsackOptimizer()
        items = [
            PackingItem(id="1", name="shirt", category=ItemCategory.clothing, weight_grams=200),
            PackingItem(id="2", name="pants", category=ItemCategory.clothing, weight_grams=400),
            PackingItem(id="3", name="jacket", category=ItemCategory.clothing, weight_grams=800),
        ]
        result = optimizer.optimize(items, capacity_grams=1000)
        assert result["status"] == "optimal"
        assert result["total_weight_grams"] <= 1000

    def test_essentials_always_selected(self):
        """Essential items should always be in the solution."""
        optimizer = KnapsackOptimizer()
        items = [
            PackingItem(id="1", name="passport", category=ItemCategory.documents, weight_grams=50, is_essential=True),
            PackingItem(id="2", name="heavy_item", category=ItemCategory.gear, weight_grams=15000),
            PackingItem(id="3", name="light_item", category=ItemCategory.clothing, weight_grams=100),
        ]
        result = optimizer.optimize(items, capacity_grams=500, essentials_ids={"1"})
        assert "1" in result["selected_ids"]

    def test_empty_items(self):
        """Should handle empty item list."""
        optimizer = KnapsackOptimizer()
        result = optimizer.optimize([], capacity_grams=1000)
        assert result["selected_ids"] == []
        assert result["status"] == "optimal"

    def test_all_items_fit(self):
        """When all items fit, all should be selected."""
        optimizer = KnapsackOptimizer()
        items = [
            PackingItem(id="1", name="shirt", category=ItemCategory.clothing, weight_grams=200),
            PackingItem(id="2", name="pants", category=ItemCategory.clothing, weight_grams=300),
        ]
        result = optimizer.optimize(items, capacity_grams=10000)
        assert len(result["selected_ids"]) == 2
