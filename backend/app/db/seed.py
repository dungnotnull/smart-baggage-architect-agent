"""Seed database with initial data."""

from app.services.database import db_service


def seed():
    """Insert initial seed data into the database."""
    db_service.initialize_schema()
    conn = db_service.get_connection()

    try:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, display_name, preferred_units) VALUES (?, ?, ?)",
            ("user_default", "Default User", "metric"),
        )
        conn.commit()
    except Exception as e:
        print(f"Seed warning: {e}")

    print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
