# Smart Baggage Architect

[![CI](https://github.com/smart-baggage-architect/smart-baggage-architect/actions/workflows/ci.yml/badge.svg)](https://github.com/smart-baggage-architect/smart-baggage-architect/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com/)

> **Pack smarter. Travel lighter. Never forget a thing.**

AI-powered travel packing assistant that combines airline baggage policy intelligence, destination weather forecasting, and real-time computer vision to eliminate both over-packing and under-packing.

## ✨ Features

- **50+ Airline Policies** — Real-time baggage allowance lookup with fee calculations
- **Weather-Aware Packing** — 7-day Open-Meteo forecast drives clothing recommendations
- **Camera Verification** — YOLOv8n on-device object detection scans your suitcase in real-time
- **LLM Advisor** — Claude → GPT-4o → Phi-3-mini provides natural-language packing advice
- **Weight Optimizer** — Knapsack + 3D bin-packing suggests optimal load order
- **Adaptive Learning** — Post-trip feedback improves future packing lists
- **Offline-First** — Core features work without internet
- **Customs Alerts** — LLM identifies restricted items at your destination

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20 LTS
- (Optional) Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs`

### Mobile

```bash
cd mobile
npm install
npx expo start
```

### Download ML Models

```bash
cd backend
python scripts/download_models.py --yolo    # YOLOv8n base model
python scripts/download_models.py --clip     # CLIP zero-shot model
python scripts/download_models.py --phi3     # Phi-3-mini GGUF (manual download)
```

### Docker

```bash
docker compose up --build
```

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
LLM_PROVIDER=claude           # claude | openai | local
ANTHROPIC_API_KEY=sk-ant-...   # Required for Claude
OPENAI_API_KEY=sk-...          # Required for GPT-4o
AUTH_API_KEY=your-secret-key   # API authentication
AUTH_DISABLED=true             # Disable auth in dev
```

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│              Mobile (React Native + Expo)         │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ Trip     │ │ Packing  │ │ Camera Scan       │ │
│  │ Setup    │ │ List     │ │ YOLOv8n ONNX      │ │
│  │          │ │          │ │ + CLIP fallback   │ │
│  └──────────┘ └──────────┘ └───────────────────┘ │
└──────────────────┬──────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────┐
│              Backend (FastAPI)                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ Airline  │ │ Weather  │ │ Packing List      │ │
│  │ Policy   │ │ (Meteo)  │ │ Generator         │ │
│  │ Engine   │ │          │ │                   │ │
│  └──────────┘ └──────────┘ └───────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ Knapsack │ │ 3D Bin   │ │ LLM Orchestrator │ │
│  │ Optimizer│ │ Packing  │ │ Claude→GPT→Phi3  │ │
│  └──────────┘ └──────────┘ └───────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐ │
│  │ Feedback │ │ Knowledge│ │ Airline Scraper   │ │
│  │ Service  │ │ Crawler  │ │ (crawl4ai)        │ │
│  └──────────┘ └──────────┘ └───────────────────┘ │
│                                                   │
│  SQLite + SQLCipher (AES-256) │ Auth │ Rate Limit │
└───────────────────────────────────────────────────┘
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trip/` | POST | Create trip + generate packing list |
| `/api/trip/{id}` | GET | Get trip details |
| `/api/trip/` | GET | List all trips |
| `/api/trip/{id}` | DELETE | Delete a trip |
| `/api/packing/{trip_id}` | GET | Get packing list |
| `/api/packing/{trip_id}/item/{item_id}` | PUT | Update packing item |
| `/api/packing/{trip_id}/optimize` | POST | Run weight + bin optimization |
| `/api/packing/regenerate/{trip_id}` | POST | Regenerate packing list |
| `/api/airline/` | GET | List all 50+ airlines |
| `/api/airline/{code}` | GET | Get airline baggage policy |
| `/api/airline/{code}/freshness` | GET | Check policy freshness |
| `/api/airline/refresh` | POST | Refresh stale policies |
| `/api/weather/summary` | GET | Weather summary + recommendations |
| `/api/weather/forecast` | GET | Raw forecast data |
| `/api/weather/geocode` | GET | City to coordinates |
| `/api/vision/detect` | POST | YOLO item detection from image |
| `/api/vision/train` | POST | Start YOLO training |
| `/api/vision/export-onnx` | POST | Export model to ONNX |
| `/api/llm/advice` | POST | Generate packing advice |
| `/api/llm/customs-alert` | POST | Check customs restrictions |
| `/api/llm/substitutions` | POST | Smart weight-saving alternatives |
| `/api/feedback/item` | POST | Submit item feedback |
| `/api/feedback/missing` | POST | Report missing essential |
| `/api/feedback/adaptive/{dest}` | GET | Get adaptive profile |
| `/api/knowledge/crawl` | POST | Run knowledge crawler |

Full interactive docs at `/docs` (Swagger UI).

## 🛡 Security

| Concern | Mitigation |
|---------|-----------|
| Camera frames | Processed on-device (YOLOv8n ONNX); never sent to server |
| Trip data | SQLite + SQLCipher AES-256; no cloud sync by default |
| API keys | OS keychain storage (Keytar/SecureStore) |
| API access | Bearer token or X-API-Key header authentication |
| Rate limiting | 60 req/min per IP (slowapi) |
| CORS | Configurable origins (default: all in dev) |

## 🧪 Testing

```bash
cd backend
pytest tests/ -v --cov=app
```

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Python 3.11 |
| Mobile | React Native + Expo 51 |
| Object Detection | YOLOv8n (ONNX Runtime Mobile) |
| Zero-Shot Fallback | CLIP ViT-B/32 |
| Local SLM | Phi-3-mini (llama.cpp) |
| Knapsack | PuLP (0/1 IP) |
| 3D Bin-Packing | py3dbp |
| Weather | Open-Meteo |
| Airline DB | YAML per carrier (50+ files) |
| Database | SQLite + SQLCipher (AES-256) |
| Auth | Bearer token / API key |
| Rate Limiting | slowapi |
| Logging | loguru |
| Primary LLM | Claude claude-sonnet-4-6 |
| Fallback LLM | GPT-4o |
| CI | GitHub Actions |

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR process.

## 📄 License

[MIT](LICENSE)