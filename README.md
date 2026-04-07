# Ride Wit Me

Ride Wit Me is a route-generation project for road cycling. It combines a Python backend that generates, enriches, filters, ranks, and exports loop routes with a Next.js frontend that submits ride requests and visualizes the best candidates on a map.

## What It Does

- Accepts a ride request with a start point, target distance, target elevation, and ride style.
- Generates multiple loop-shaped route candidates through OpenRouteService.
- Enriches each candidate with heuristic quality signals such as scenic value, ride feel, climbing character, road quality, and repeated-segment penalties.
- Filters out poor loop shapes, ranks the remaining routes, and returns them through a FastAPI API.
- Lets the web app display the top routes and download individual GPX files client-side.

## Repository Structure

```text
.
├── api/                FastAPI application entrypoint
├── app/                CLI entrypoint and shared backend configuration
├── data/               Sample request data and placeholder profile/preset files
├── domain/             Core request, route, and scoring models
├── services/           Route generation, enrichment, ranking, export, debug output
├── web/                Next.js frontend
└── docs/               Project documentation
```

## Architecture At A Glance

1. The frontend sends a `POST /generate-route` request to the backend.
2. `services.route_service.generate_routes()` orchestrates the backend pipeline.
3. `services.candidate_generator.CandidateGenerator` asks OpenRouteService for multiple loop candidates.
4. `services.enrichment.enrich_route()` derives ride-quality heuristics from provider metadata and geometry.
5. `services.ranking.rank_routes()` filters and sorts routes using `domain.scoring.score_route()`.
6. The API returns scored routes as JSON.
7. The CLI additionally exports GPX files and a debug JSON artifact to `outputs/`.

More detail: [docs/architecture.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/architecture.md)

## Requirements

### Backend

- Python 3.11+ recommended
- An OpenRouteService API key

### Frontend

- Node.js 20+ recommended
- npm

## Environment Variables

### Backend

Create a root `.env` file:

```env
OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
```

### Frontend

Create `web/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Examples are also provided in:

- [/.env.example](/Users/maximehumbert/Documents/GitHub/ride-wit-me/.env.example)
- [web/.env.local.example](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/.env.local.example)

## Local Development

### 1. Install backend dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the backend API

```bash
uvicorn api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 3. Install frontend dependencies

```bash
cd web
npm install
```

### 4. Start the frontend

```bash
cd web
npm run dev
```

The frontend will be available at `http://127.0.0.1:3000`.

## CLI Usage

The repository also includes a CLI for generating and exporting routes without the frontend.

```bash
python -m app.main \
  --start-lat 49.3597 \
  --start-lng 6.1685 \
  --distance 65 \
  --elevation 700 \
  --ride-style endurance \
  --debug
```

CLI outputs:

- Top-ranked routes printed to stdout
- GPX files written to `outputs/routes/`
- A debug JSON artifact written to `outputs/debug_runs/`

## API Summary

### Health Check

`GET /health`

Response:

```json
{ "status": "ok" }
```

### Generate Routes

`POST /generate-route`

Example request:

```json
{
  "start_point": { "lat": 49.3597, "lng": 6.1685 },
  "distance_km": 65,
  "elevation_m": 700,
  "ride_style": "endurance",
  "avoid": {
    "busy_roads": true,
    "urban": true,
    "unpaved": true,
    "repeated_segments": true
  },
  "prefer": {
    "scenic": true,
    "rolling_roads": true,
    "novelty": false
  }
}
```

Full contract: [docs/api.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/api.md)

## Documentation Index

- [docs/architecture.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/architecture.md)
- [docs/backend.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/backend.md)
- [docs/frontend.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/frontend.md)
- [docs/api.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/api.md)
- [docs/development.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/development.md)

## Current Limitations

- Route generation currently depends on a single provider: OpenRouteService.
- Ranking is heuristic and does not use historical rider preferences or learned personalization.
- `data/rider_profile.json` and `data/presets.json` are currently empty placeholders.
- The frontend exposes only a subset of the backend request controls.
- There is no automated test suite in the repository yet.

## License / Ownership

No license file is currently present in the repository. Add one before distributing the project externally.
