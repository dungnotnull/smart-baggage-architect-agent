# Contributing to Smart Baggage Architect

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

Run the development server:
```bash
uvicorn app.main:app --reload
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

### Download ML Models

```bash
cd backend
python scripts/download_models.py --all
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and ensure:
   - Backend: `ruff check app/` passes
   - Mobile: `npx tsc --noEmit` passes
4. **Commit** with conventional commits:
   - `feat: add airline policy scraper for LATAM carriers`
   - `fix: handle missing weather data gracefully`
   - `docs: update API documentation`
5. **Push** and open a Pull Request

## Code Style

### Python (Backend)
- **Formatter**: Black (120 char line length)
- **Linter**: Ruff (configured in `pyproject.toml`)
- **Type hints**: Required for all function signatures
- **Imports**: Sorted by ruff (isort-compatible)

```bash
ruff check app/ --fix
ruff format app/
```

### TypeScript (Mobile)
- **Linter**: ESLint with TypeScript plugin
- **Formatting**: Prettier (2-space indent, single quotes)

```bash
npx tsc --noEmit
npm run lint
```

## Project Structure

```
backend/
  app/
    config.py          — Settings & env vars
    main.py            — FastAPI app + middleware
    middleware/         — Auth, rate limiting
    models/            — Pydantic request/response schemas
    routers/           — API endpoint handlers
    services/          — Business logic (airline, weather, packing, etc.)
    db/                — Database schema & migrations
  airline_policies/    — 50+ YAML files per carrier
  scripts/            — Model download, DB seed
  tests/              — Unit & integration tests

mobile/
  app/                — Expo Router screens
  components/         — Reusable UI components
  services/           — API client, YOLO scanner
```

## Adding a New Airline

1. Create `backend/airline_policies/XX.yaml` following the schema:

```yaml
iata_code: XX
airline_name: Air Example
region: Region
last_verified: "YYYY-MM-DD"
source_url: "https://..."

carry_on:
  weight_kg: 7  # null if no limit
  dimensions_cm: [55, 40, 23]
  personal_item: true
  personal_item_dimensions_cm: [35, 25, 10]

checked:
  weight_kg_economy: 23
  weight_kg_business: 32
  weight_kg_first: 32
  dimensions_cm: [158]
  fee_first_bag_economy_domestic_usd: 0
  fee_first_bag_economy_international_usd: 0
  fee_second_bag_economy_domestic_usd: 80
  fee_second_bag_economy_international_usd: 80

overweight_fees:
  23_32kg_usd: 80
  32_46kg_usd: 160
  over_46kg: not_accepted

special_items:
  sports_equipment: standard_fee
  musical_instruments: cabin_seat_purchase_available
  strollers: free_check

elite_benefits: {}
```

2. Verify: `python -c "from app.services.airline_policy import policy_engine; p = policy_engine.get_policy('XX'); print(p.airline_name)"`

## Adding a New Packing Item Category

1. Add category to `ItemCategory` enum in `backend/app/models/packing.py`
2. Add base quantities to `CLOTHING_BASE` in `backend/app/services/packing_list.py`
3. Add weight estimates to `CLOTHING_WEIGHTS`
4. Update the `categoryIcons` map in mobile components

## Reporting Issues

- **Bug reports**: Include steps to reproduce, expected vs actual behavior, and server logs
- **Feature requests**: Describe the use case and expected behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.