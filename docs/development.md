# Development

## Local Setup

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the repository root:

```env
OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
```

Start the server:

```bash
uvicorn api.main:app --reload
```

### Frontend

```bash
cd web
npm install
```

Create `web/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Start the app:

```bash
cd web
npm run dev
```

## Manual Smoke Test

### API health

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Route generation

```bash
curl -X POST http://127.0.0.1:8000/generate-route \
  -H "Content-Type: application/json" \
  -d '{
    "start_point": { "lat": 49.3597, "lng": 6.1685 },
    "distance_km": 65,
    "elevation_m": 700,
    "ride_style": "endurance"
  }'
```

### CLI smoke test

```bash
python -m app.main \
  --start-lat 49.3597 \
  --start-lng 6.1685 \
  --distance 65 \
  --elevation 700 \
  --ride-style endurance
```

## Linting

Frontend lint command:

```bash
cd web
npm run lint
```

There is currently no dedicated Python lint or test command defined in the repository.

## Working On The Backend

Most backend changes will affect one of these layers:

- `domain/` for model or scoring changes
- `services/` for generation and enrichment behavior
- `api/` for HTTP contract changes
- `app/` for CLI or config changes

When changing scoring behavior, inspect both:

- [domain/scoring.py](/Users/maximehumbert/Documents/GitHub/ride-wit-me/domain/scoring.py)
- [services/enrichment.py](/Users/maximehumbert/Documents/GitHub/ride-wit-me/services/enrichment.py)

The ranking outcome depends on both files together.

## Working On The Frontend

The frontend is compact and centered around:

- [web/app/page.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/page.tsx)
- [web/components/Map.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/components/Map.tsx)

If you extend the request form, keep the backend request model in sync with the UI controls.

## Output Artifacts

The CLI writes:

- GPX files to `outputs/routes/`
- Debug JSON files to `outputs/debug_runs/`

These directories are generated at runtime and do not need to be committed.

## Known Technical Debt

- No automated tests
- No typed shared API contract between frontend and backend
- No provider abstraction beyond the current OpenRouteService implementation
- Empty placeholder files in `data/` for future rider profiles and presets
- Default metadata still present in the frontend layout
