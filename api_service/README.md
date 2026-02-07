# API Service (FastAPI)

Minimal REST API scaffold for properties. It reads from the JSON store by default and can attempt PostgreSQL if configured.

## Quick start
1. Create and activate a virtual env
2. Install deps from `api_service/requirements.txt`
3. Copy `.env.example` from repo root to `.env` and set DB_* values if needed
4. Optional: set `API_USE_DB=true` to query PostgreSQL instead of JSON
5. Run:
   - `uvicorn app.main:app --reload`

## Endpoints
- `GET /health`
- `GET /properties` (filters: zone, price_min, price_max, type, bedrooms, amenities)
- `GET /properties/{id}`
