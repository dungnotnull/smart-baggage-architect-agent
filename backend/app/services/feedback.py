"""Post-trip feedback service — adaptive packing profile engine."""

from datetime import datetime
from uuid import uuid4

from app.services.database import db_service


class FeedbackService:
    """Handle post-trip feedback and adaptive packing profiles."""

    def submit_feedback(
        self,
        trip_id: str,
        item_name: str,
        item_id: str | None = None,
        was_used: bool = True,
        rating: int | None = None,
    ) -> dict:
        """Submit feedback for a single item after a trip."""
        feedback_id = uuid4().hex[:12]
        db_service.execute(
            """INSERT INTO feedback (id, trip_id, item_id, item_name, was_used, rating, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (feedback_id, trip_id, item_id, item_name, 1 if was_used else 0, rating, datetime.utcnow().isoformat()),
        )
        db_service.commit()
        return {"feedback_id": feedback_id, "item_name": item_name, "was_used": was_used}

    def submit_missing_essential(
        self,
        trip_id: str,
        item_name: str,
        category: str | None = None,
        destination: str | None = None,
        activity_type: str | None = None,
    ) -> dict:
        """Submit an item the user wished they had packed."""
        missing_id = uuid4().hex[:12]
        db_service.execute(
            """INSERT INTO missing_essentials (id, trip_id, item_name, category, destination, activity_type, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (missing_id, trip_id, item_name, category, destination, activity_type, datetime.utcnow().isoformat()),
        )
        db_service.commit()
        return {"missing_id": missing_id, "item_name": item_name}

    def get_trip_feedback(self, trip_id: str) -> list[dict]:
        """Get all feedback for a trip."""
        rows = db_service.fetch_all(
            "SELECT * FROM feedback WHERE trip_id = ? ORDER BY created_at",
            (trip_id,),
        )
        return [dict(row) for row in rows]

    def get_trip_missing_essentials(self, trip_id: str) -> list[dict]:
        """Get all missing essentials reported for a trip."""
        rows = db_service.fetch_all(
            "SELECT * FROM missing_essentials WHERE trip_id = ? ORDER BY created_at",
            (trip_id,),
        )
        return [dict(row) for row in rows]

    def get_unused_items_for_destination(self, destination: str) -> list[dict]:
        """Get items frequently marked as unused for a destination."""
        rows = db_service.fetch_all(
            """SELECT item_name, COUNT(*) as count, AVG(rating) as avg_rating
               FROM feedback f
               JOIN trips t ON f.trip_id = t.id
               WHERE t.destination LIKE ? AND f.was_used = 0
               GROUP BY item_name
               ORDER BY count DESC
               LIMIT 20""",
            (f"%{destination}%",),
        )
        return [dict(row) for row in rows]

    def get_frequently_missing_for_destination(self, destination: str) -> list[dict]:
        """Get items frequently reported as missing for a destination."""
        rows = db_service.fetch_all(
            """SELECT item_name, COUNT(*) as count
               FROM missing_essentials
               WHERE destination LIKE ?
               GROUP BY item_name
               ORDER BY count DESC
               LIMIT 20""",
            (f"%{destination}%",),
        )
        return [dict(row) for row in rows]

    def get_adaptive_weight_adjustment(self, item_name: str, destination: str) -> float:
        """Calculate weight adjustment for an item based on feedback history.

        Returns a multiplier: <1.0 means item should be deprioritized,
        >1.0 means item should be prioritized.
        """
        rows = db_service.fetch_all(
            """SELECT was_used, COUNT(*) as count
               FROM feedback f
               JOIN trips t ON f.trip_id = t.id
               WHERE f.item_name = ? AND t.destination LIKE ?
               GROUP BY was_used""",
            (item_name, f"%{destination}%"),
        )

        if not rows:
            return 1.0

        used_count = sum(r["count"] for r in rows if r["was_used"])
        unused_count = sum(r["count"] for r in rows if not r["was_used"])
        total = used_count + unused_count

        if total == 0:
            return 1.0

        usage_rate = used_count / total
        return 0.5 + (usage_rate * 0.5)

    def get_packing_profile(self, activity_type: str, destination: str | None = None) -> dict:
        """Generate an adaptive packing profile based on historical feedback."""
        profile = {
            "activity_type": activity_type,
            "destination": destination,
            "suggested_additions": [],
            "suggested_removals": [],
            "weight_adjustments": {},
        }

        if destination:
            missing = self.get_frequently_missing_for_destination(destination)
            profile["suggested_additions"] = [
                {"item_name": m["item_name"], "frequency": m["count"]}
                for m in missing[:5]
            ]

            unused = self.get_unused_items_for_destination(destination)
            profile["suggested_removals"] = [
                {"item_name": u["item_name"], "frequency": u["count"]}
                for u in unused[:5]
            ]

        return profile


feedback_service = FeedbackService()
