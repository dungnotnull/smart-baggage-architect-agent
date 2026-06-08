-- Smart Baggage Architect — Database Schema (SQLite + SQLCipher)
-- Phase 0: Initial schema

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- User profiles
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    email TEXT UNIQUE,
    preferred_units TEXT DEFAULT 'metric' CHECK (preferred_units IN ('metric', 'imperial')),
    home_airport TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Trip records
CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    airline_iata TEXT NOT NULL,
    flight_number TEXT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    return_date TEXT NOT NULL,
    passenger_count INTEGER DEFAULT 1,
    cabin_class TEXT DEFAULT 'economy' CHECK (cabin_class IN ('economy', 'business', 'first')),
    activity_type TEXT DEFAULT 'leisure' CHECK (activity_type IN ('leisure', 'business', 'adventure', 'family')),
    trip_duration_days INTEGER GENERATED ALWAYS AS (julianday(return_date) - julianday(departure_date)) STORED,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Packing items per trip
CREATE TABLE IF NOT EXISTS packing_items (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('clothing', 'electronics', 'documents', 'toiletries', 'gear', 'other')),
    quantity INTEGER DEFAULT 1,
    weight_grams INTEGER,
    volume_ml INTEGER,
    is_essential INTEGER DEFAULT 0,
    is_carry_on_compliant INTEGER DEFAULT 1,
    packed INTEGER DEFAULT 0,
    detected_by_vision INTEGER DEFAULT 0,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Airline policy cache (avoids repeated YAML reads)
CREATE TABLE IF NOT EXISTS airline_policies_cache (
    iata_code TEXT PRIMARY KEY,
    airline_name TEXT NOT NULL,
    policy_data TEXT NOT NULL,  -- JSON blob
    source_url TEXT,
    last_verified TEXT NOT NULL,
    cached_at TEXT DEFAULT (datetime('now'))
);

-- Post-trip feedback (self-improving loop)
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    item_id TEXT REFERENCES packing_items(id),
    item_name TEXT NOT NULL,
    was_used INTEGER NOT NULL,  -- 1 = used, 0 = unused
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Missing essentials (items users wished they had)
CREATE TABLE IF NOT EXISTS missing_essentials (
    id TEXT PRIMARY KEY,
    trip_id TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    category TEXT,
    destination TEXT,
    activity_type TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- User preferences (adaptive packing profiles)
CREATE TABLE IF NOT EXISTS user_prefs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    pref_key TEXT NOT NULL,
    pref_value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, pref_key)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trips_user ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_airline ON trips(airline_iata);
CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(departure_date, return_date);
CREATE INDEX IF NOT EXISTS idx_packing_items_trip ON packing_items(trip_id);
CREATE INDEX IF NOT EXISTS idx_packing_items_category ON packing_items(category);
CREATE INDEX IF NOT EXISTS idx_feedback_trip ON feedback(trip_id);
CREATE INDEX IF NOT EXISTS idx_missing_essentials_trip ON missing_essentials(trip_id);
