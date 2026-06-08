# PROJECT-detail.md — smart-baggage-architect

## Executive Summary
Smart Baggage Architect is an AI-powered travel packing assistant that combines airline baggage policy intelligence, destination weather forecasting, and real-time computer vision to eliminate both over-packing and under-packing. Users input their flight details; the system generates a precisely calibrated packing list. As the user physically packs, they sweep their phone camera over the suitcase and the agent identifies what is already inside, checks it off the list, and alerts the user to still-missing items (passport, power bank, medications, etc.). A Knapsack-based optimizer also suggests the optimal load order to maximize space utilization.

---

## Problem Statement
### Research Context
- According to a 2023 Bounce survey, **62% of travelers** report overpacking on at least half of their trips, leading to unexpected checked-bag fees averaging $35–$75 per flight.
- **23% of travelers** forget at least one essential item per trip (IATA Consumer Research 2022), causing stress and unplanned purchases at the destination.
- Airline baggage policies differ across 900+ IATA carriers by cabin class, route, fare type, and frequent-flyer status — making manual compliance error-prone.
- Weight distribution matters: improperly packed luggage can cause back strain and damage fragile items. Research in ergonomics (Bhattacharya et al., 2020) recommends heaviest items closest to the suitcase's back panel.

### Gap in Existing Solutions
Existing packing apps (PackPoint, TripList) provide generic lists with no vision verification, no real-time airline policy lookup, and no spatial optimization. Smart Baggage Architect uniquely combines all three layers.

---

## Target Users & Use Cases
| User Type | Use Case |
|-----------|---------|
| Frequent business traveler | Tight carry-on compliance for multiple airlines per month |
| Family vacation planner | Coordinate packing lists for 4+ people across multiple bags |
| Budget traveler | Avoid all checked-bag fees by maximizing carry-on efficiency |
| Adventure / outdoor traveler | Ensure specialized gear fits weight limits for remote destinations |
| First-time international traveler | Guided experience with customs-sensitive items flagged |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MOBILE APP (React Native)                    │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Trip Setup │  │ Packing List │  │  Camera Scan UI (AR)     │ │
│  │ (flight,   │  │ Generator    │  │  YOLOv8n ONNX on-device  │ │
│  │  dates)    │  │              │  │  + CLIP fallback         │ │
│  └────────────┘  └──────────────┘  └──────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST / Local IPC
┌────────────────────────────▼────────────────────────────────────┐
│                    PYTHON BACKEND (FastAPI)                       │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────┐   ┌─────────────┐  │
│  │ Airline Policy  │   │  Weather Module  │   │  Packing    │  │
│  │ Engine          │   │  (Open-Meteo)    │   │  Optimizer  │  │
│  │ (YAML DB +      │   │  7-day forecast  │   │  (Knapsack  │  │
│  │  web scraper)   │   │  → clothing recs │   │  + 3D bin)  │  │
│  └─────────────────┘   └──────────────────┘   └─────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LLM Orchestration Layer                      │   │
│  │  Claude API (primary) → GPT-4o → Phi-3-mini (offline)    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Local Storage: SQLite + AES-256                  │   │
│  │  trip_profiles | packing_history | user_prefs | items_db  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack
| Component | Technology | Source |
|-----------|-----------|--------|
| Mobile Frontend | React Native 0.74 + Expo | Open source |
| Camera / AR Overlay | React Native Vision Camera + Skia | Open source |
| Backend API | FastAPI 0.111 (Python 3.11) | Open source |
| Object Detection | YOLOv8n (Ultralytics) → ONNX Runtime Mobile | Open source |
| Zero-shot Fallback | CLIP ViT-B/32 via HuggingFace Transformers | Open source |
| Local SLM | Phi-3-mini-4k-instruct (4-bit GGUF) via llama.cpp | Open source |
| Packing Optimizer | Custom Python: PuLP (Knapsack) + py3dbp (3D bin) | Open source |
| Weather API | Open-Meteo REST API | Free/open |
| Airline DB | Custom YAML + Selenium scraper | Custom |
| Local Database | SQLite 3 + SQLCipher (AES-256) | Open source |
| Primary LLM | Claude claude-sonnet-4-6 via Anthropic SDK | Anthropic API |
| Fallback LLM | GPT-4o via OpenAI SDK | OpenAI API |

---

## ML/DL Models Section

### Primary Detection Model
| Field | Value |
|-------|-------|
| Base Model | YOLOv8n (nano, 3.2M params) |
| HuggingFace ID | `Ultralytics/YOLOv8` |
| Fine-tune Target | Travel-items detection: ~250 classes (clothing, electronics, documents, toiletries, gear) |
| Training Data | Custom dataset: Open Images V7 subset + self-collected suitcase photos |
| Fine-tune Method | Transfer learning: freeze backbone, train detection head + neck |
| Deployment Format | ONNX (mobile) + TorchScript (server backup) |
| Target Inference Speed | <30ms per frame on iPhone 12 / mid-range Android |

### Zero-Shot Fallback
| Field | Value |
|-------|-------|
| Model | CLIP ViT-B/32 |
| HuggingFace ID | `openai/clip-vit-base-patch32` |
| Purpose | Classify items YOLO doesn't recognize using text prompts ("a folding travel umbrella") |
| Inference | Server-side only (too large for mobile) |

### Local SLM
| Field | Value |
|-------|-------|
| Model | Phi-3-mini-4k-instruct |
| HuggingFace ID | `microsoft/Phi-3-mini-4k-instruct` |
| Quantization | Q4_K_M GGUF |
| Purpose | Offline packing advice, item substitution suggestions, trip briefings |
| Runtime | llama.cpp Python bindings |

---

## External LLM API Integration (Pluggable Backend)
```python
# config.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")  # "claude" | "openai" | "local"

PROVIDERS = {
    "claude": {
        "model": "claude-sonnet-4-6",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY",
    },
    "local": {
        "model_path": "./models/phi3-mini-q4.gguf",
        "n_ctx": 4096,
    },
}
```

---

## Feature Specification

### MVP Features
- [x] Trip setup form: airline, flight number, travel dates, destination, passenger count
- [x] Airline policy lookup from YAML database (weight limits, size limits, fee structure)
- [x] 7-day weather forecast fetch for destination via Open-Meteo
- [x] Packing list generation: clothing types + quantities based on weather + trip duration
- [x] Essential items checklist (passport, charger, medications, adapters)
- [x] Camera scanning mode: point phone at suitcase → detect items → mark as packed
- [x] Missing items alert: list items not yet detected after scan
- [x] Weight budget tracker: user inputs item weights, system tracks total vs. allowance
- [x] Packing order suggestions: heavy/bulky items first (Knapsack-informed recommendations)
- [x] Trip history: save past packing lists for repeat destinations

### Advanced Features
- [ ] 3D suitcase visualization: show items placed in AR suitcase model
- [ ] Multi-bag coordination: distribute items across carry-on + checked + backpack optimally
- [ ] Airline fee calculator: show cost impact of different packing configurations
- [x] Smart substitution: "Replace bulky hair dryer with travel-size (saves 800g)"
- [x] Customs alert: flag items restricted at specific destination (e.g., no drones in Morocco)
- [ ] Collaborative packing: share packing list with travel companions
- [ ] Seasonal wardrobe profile: system learns user's preferred items per climate type
- [x] Post-trip feedback loop: "Did you use everything you packed?" → refine future lists
- [ ] Integration with travel booking APIs (Amadeus, Skyscanner) for auto-fill

---

## Full E2E Data Flow
1. User enters flight details (airline, flight number, travel dates, destination city, number of days).
2. Backend queries `airline_policies/{IATA_CODE}.yaml` → extracts carry-on dimensions/weight, checked-bag weight limit, fee schedule.
3. Backend calls Open-Meteo API with destination coordinates → retrieves 7-day min/max temperatures, precipitation probability, wind speed.
4. **Packing List Engine**: combines trip duration × weather data × airline limits → generates categorized list:
   - Clothing (type, quantity, weight estimate)
   - Electronics & chargers
   - Documents & travel essentials
   - Toiletries (size-compliant for carry-on: ≤100ml)
   - Optional/destination-specific items
5. LLM (Claude API) reviews the generated list, adds natural-language advice, flags potential issues (e.g., "Destination has formal dress code for temples").
6. User reviews and edits the list in the mobile app.
7. **Packing Phase**: User opens Camera Scan mode → React Native Vision Camera streams frames to on-device YOLOv8n ONNX model.
8. YOLOv8n outputs bounding boxes + class labels → matched against packing list items via fuzzy name matching.
9. Matched items are marked as "packed" with a green checkmark overlay. Unmatched list items appear as "still missing" in red.
10. Rare/unknown items are sent to server-side CLIP for zero-shot classification.
11. **Knapsack Optimizer**: after final item selection, runs 0/1 Knapsack to confirm total weight fits within airline limit, then 3D bin-packing to suggest load order.
12. Trip data saved to local SQLite (encrypted). User can retrieve packing profile for future similar trips.

---

## Privacy & Security
| Concern | Mitigation |
|---------|-----------|
| Camera frames | Processed on-device (YOLOv8n ONNX); frames never sent to server unless user explicitly requests CLIP fallback |
| Trip data | SQLite + SQLCipher AES-256; no cloud sync by default |
| Airline policy scraping | Scraped data cached locally; no user data sent to airline websites |
| API keys | Stored in OS keychain (Keytar on desktop, SecureStore on mobile) |
| Biometric lock | Optional PIN/FaceID to open app and decrypt local DB |

---

## Key Python/JS Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.111 | Backend REST API |
| `ultralytics` | 8.2 | YOLOv8 training + export |
| `onnxruntime` | 1.18 | Server-side ONNX inference |
| `transformers` | 4.41 | CLIP zero-shot fallback |
| `llama-cpp-python` | 0.2.77 | Phi-3-mini local inference |
| `anthropic` | 0.28 | Claude API SDK |
| `openai` | 1.35 | GPT-4o fallback SDK |
| `pulp` | 2.8 | Linear programming for Knapsack |
| `py3dbp` | 1.1 | 3D bin-packing heuristics |
| `requests` | 2.32 | Open-Meteo API calls |
| `pydantic` | 2.7 | Data validation |
| `sqlcipher3` | 0.5 | AES-256 encrypted SQLite |
| `cryptography` | 42 | AES key management |
| `crawl4ai` | 0.3 | Airline policy web scraping |
| `react-native` | 0.74 | Mobile frontend |
| `react-native-vision-camera` | 4.3 | Camera streaming |
| `@shopify/react-native-skia` | 1.3 | AR overlay rendering |

---

## Improvement Suggestions (Beyond Original Idea)
1. **Seasonal Wardrobe Learning**: Track which items user marked as "unused" after trips → progressively remove them from future lists for similar trips.
2. **Airline Fee Arbitrage**: If checked-bag fee > cost of shipping items, alert user to consider mail-forwarding services.
3. **Lost Luggage Recovery Aid**: After scanning, generate a timestamped photo report of suitcase contents for insurance claims.
4. **Carbon Footprint Mode**: Lighter luggage → lower fuel burn per passenger → estimate and display CO2 savings vs. average traveler.
5. **RFID / NFC Tag Integration**: Attach NFC tags to physical items; phone reads tags instead of using camera for faster check-in.
6. **Packing Template Marketplace**: Let users share and download packing templates for specific trip types (ski trip, beach week, business conference).
7. **Multi-Language Support**: Detect user locale; generate packing advice in local language via LLM translation.
8. **Smart Watch Companion**: Vibrate reminder alerts on Apple Watch / Wear OS when user is within 2 hours of departure with unchecked items.
