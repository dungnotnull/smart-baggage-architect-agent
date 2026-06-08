"""0/1 Knapsack optimizer via PuLP — weight allocation for packing list."""

import pulp

from app.models.packing import PackingItem


class KnapsackOptimizer:
    """Solve 0/1 Knapsack to confirm items fit within weight budget."""

    def optimize(
        self,
        items: list[PackingItem],
        capacity_grams: int,
        essentials_ids: set[str] | None = None,
    ) -> dict:
        """Run 0/1 Knapsack optimization.

        Essential items are forced into the solution (constraint).
        Returns dict with selected items, total weight, total value.
        """
        if not items:
            return {
                "selected_ids": [],
                "excluded_ids": [],
                "total_weight_grams": 0,
                "total_value": 0,
                "status": "optimal",
                "capacity_grams": capacity_grams,
            }

        prob = pulp.LpProblem("PackingKnapsack", pulp.LpMaximize)

        x = {item.id: pulp.LpVariable(f"x_{item.id}", cat="Binary") for item in items}

        values: dict[str, float] = {}
        for item in items:
            if essentials_ids and item.id in essentials_ids:
                values[item.id] = 1000
            else:
                values[item.id] = max(1, 1 / ((item.weight_grams or 1) / 1000))

        prob += pulp.lpSum(values[i.id] * x[i.id] for i in items)

        weight_expr = pulp.lpSum(
            (i.weight_grams or 0) * i.quantity * x[i.id] for i in items
        )
        prob += weight_expr <= capacity_grams

        if essentials_ids:
            for item in items:
                if item.id in essentials_ids:
                    prob += x[item.id] == 1

        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        selected_ids = [i.id for i in items if x[i.id].value() == 1]
        excluded_ids = [i.id for i in items if x[i.id].value() == 0]
        total_weight = sum(
            (i.weight_grams or 0) * i.quantity
            for i in items
            if i.id in selected_ids
        )

        return {
            "selected_ids": selected_ids,
            "excluded_ids": excluded_ids,
            "total_weight_grams": total_weight,
            "total_value": pulp.value(prob.objective) or 0,
            "status": pulp.LpStatus[prob.status].lower(),
            "capacity_grams": capacity_grams,
        }

    def check_weight_feasibility(
        self,
        items: list[PackingItem],
        capacity_grams: int,
    ) -> dict:
        """Quick check if all items fit within weight budget."""
        total = sum((i.weight_grams or 0) * i.quantity for i in items)
        essentials_weight = sum(
            (i.weight_grams or 0) * i.quantity for i in items if i.is_essential
        )
        essentials_count = sum(1 for i in items if i.is_essential)

        return {
            "total_weight_grams": total,
            "capacity_grams": capacity_grams,
            "utilization_pct": round((total / capacity_grams) * 100, 1) if capacity_grams else 0,
            "over_weight": total > capacity_grams,
            "over_by_grams": max(0, total - capacity_grams),
            "essentials_weight_grams": essentials_weight,
            "essentials_count": essentials_count,
            "non_essentials_can_remove": sum(1 for i in items if not i.is_essential),
        }


knapsack_optimizer = KnapsackOptimizer()
