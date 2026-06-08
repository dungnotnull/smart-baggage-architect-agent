# CLAUDE.md -- smart-baggage-architect

## Project Identity
- **Name**: smart-baggage-architect
- **Tagline**: Pack smarter. Travel lighter. Never forget a thing.
- **Status**: All Phases Complete (0-5) -- Production Ready
- **Folder**: D:\smart-baggage-architect\

---

## Core Problem Being Solved
Travelers routinely over-pack or under-pack due to a lack of structured guidance that accounts for their specific flight's baggage rules, destination weather, and trip duration simultaneously. Airlines have widely varying baggage policies (carry-on size/weight, checked-bag allowance) and weather at the destination changes. The result is either checked-bag fees from overpacking or forgotten essentials that disrupt trips. Smart Baggage Architect solves this by combining airline policy data, real-time weather forecasting, and on-device computer vision (camera-based object detection) to generate a personalized packing list and verify packing completeness in real time as the user loads their suitcase.

---

## Architecture Summary
| Layer | Technology |
|-------|-----------|
| Platform | Python backend + React Native mobile app (iOS/Android) |
| Vision AI | YOLOv8-nano fine-tuned on travel-item dataset (on-device ONNX) |
| Packing Optimizer | Knapsack (0/1 & fractional variants) + bin-packing heuristics |
| Local SLM | Phi-3-mini (4-bit GGUF via llama.cpp) for natural-language packing advice |
| External Weather API | Open-Meteo (free, no key required) |
| Airline Policy DB | Custom-scraped SQLite + community-maintained YAML (50 carriers) |
| Optional LLM API | Claude claude-sonnet-4-6 (anthropic SDK) / GPT-4o fallback |
| Auth | Bearer token / X-API-Key middleware |
| Rate Limiting | slowapi (60 req/min default) |
| Logging | loguru (structured, file rotation) |

---

## Key Technical Decisions
1. **On-device YOLO inference**: Run YOLOv8-nano as ONNX on mobile via ONNX Runtime Mobile -- no image leaves the device, preserving privacy.
2. **Pluggable LLM backend**: Claude API -> GPT-4o -> local Phi-3-mini in fallback chain; config key LLM_PROVIDER.
3. **Airline policy as structured YAML**: Maintain irline_policies/ directory with per-airline YAML files (IATA code as filename); fallback to web scraping for unknown carriers.
4. **Knapsack + bin-packing hybrid**: Use 0/1 Knapsack for weight/volume budget allocation, then 3D bin-packing heuristics for load-order suggestions (heavy/dense items at bottom).
5. **Offline-first design**: All core features (packing list generation, object detection) work without internet; weather forecast and LLM API are enhancement layers.
6. **Local SQLite + AES-256**: User trip history, packing profiles, and camera snapshots stored locally with encryption.
7. **Auth + Rate Limiting**: Bearer token / X-API-Key middleware with slowapi rate limiting for production security.
8. **Structured Logging**: loguru with console + file rotation for observability.

---

## External LLM API Integrations
| Provider | Model | Config Key | Purpose |
|----------|-------|------------|---------|
| Anthropic | claude-sonnet-4-6 | ANTHROPIC_API_KEY | Primary: natural-language packing advice, airline policy parsing |
| OpenAI | gpt-4o | OPENAI_API_KEY | Fallback LLM |
| Open-Meteo | (REST, no key) | -- | 7-day weather forecast for destination |

---

## HuggingFace Models in Use
| Model ID | Purpose | Link |
|----------|---------|------|
| ultralytics/assets (YOLOv8n base) | Real-time travel-item detection via phone camera | https://huggingface.co/Ultralytics/YOLOv8 |
| microsoft/Phi-3-mini-4k-instruct | Local SLM for packing advice when offline | https://huggingface.co/microsoft/Phi-3-mini-4k-instruct |
| openai/clip-vit-base-patch32 | Zero-shot item classification for rare objects not in YOLO training set | https://huggingface.co/openai/clip-vit-base-patch32 |

---

## Current Project Status
- [x] Phase 0: Research & Environment Setup -- COMPLETE
- [x] Phase 1: MVP Core Loop -- COMPLETE
- [x] Phase 2: ML/AI Integration (Smart Vision) -- COMPLETE
- [x] Phase 3: External LLM API Integration -- COMPLETE
- [x] Phase 4: Self-Improving Knowledge Loop -- COMPLETE
- [x] Phase 5: Testing, Polish & Deployment -- COMPLETE

---

## Related Files
- [PROJECT-detail.md](PROJECT-detail.md) -- Full technical specification
- [PROJECT-DEVELOPMENT-PHASE-TRACKING.md](PROJECT-DEVELOPMENT-PHASE-TRACKING.md) -- Phase roadmap & milestones
- [SECOND-KNOWLEDGE-BRAIN.md](SECOND-KNOWLEDGE-BRAIN.md) -- Research papers, SOTA models, self-update protocol