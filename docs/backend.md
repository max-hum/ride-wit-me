# Backend

## Overview

The backend is a Python application with two entrypoints:

- `api/main.py`: FastAPI server
- `app/main.py`: CLI for local route generation and export

Both use the same underlying service pipeline.

## Backend Entry Points

### API

Start the HTTP server:

```bash
uvicorn api.main:app --reload
```

Primary endpoint details are in [api.md](/Users/maximehumbert/Documents/GitHub/ride-wit-me/docs/api.md).

### CLI

Run the CLI:

```bash
python -m app.main \
  --start-lat 49.3597 \
  --start-lng 6.1685 \
  --distance 65 \
  --elevation 700 \
  --ftp 250 \
  --system-weight 83 \
  --ride-style endurance
```

Add `--debug` to print the full ranked route breakdown.

## Configuration

The backend loads environment variables through `python-dotenv` in `app/config.py`.

Required variable:

```env
OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
```

Configured paths:

- `DATA_DIR = data/`
- `OUTPUT_DIR = outputs/routes/`
- `DEBUG_RUNS_DIR = outputs/debug_runs/`

`outputs/routes/` is created automatically at startup of the config module. `outputs/debug_runs/` is created when a debug export is written.

## Core Models

### Request models

- `StartPoint`
- `AvoidPreferences`
- `PreferPreferences`
- `RideRequest`

### Route models

- `CandidateRoute`
- `EnrichedRoute`
- `FitBreakdown`
- `ScoredRoute`

### Ride styles

Supported values:

- `endurance`
- `hilly`
- `scenic`
- `exploration`

## Service Pipeline

### 1. Candidate generation

`services.candidate_generator.CandidateGenerator` uses `OpenRouteServiceProvider` from `services.routing_provider`.

The provider:

- Builds several waypoint-pattern families around the starting point
- Starts with a baseline generation pass and adds an expanded-variety pass when there are too few strong target matches
- Requests routes from `https://api.openrouteservice.org/v2/directions/cycling-road/geojson`
- Requests extra metadata for `surface` and `waytype`
- Returns normalized `CandidateRoute` objects

Failure behavior:

- Individual candidate request failures are skipped
- If every candidate fails, the provider raises `RoutingProviderError`

### 2. Enrichment

`services.enrichment.enrich_route()` estimates route quality from provider metadata and geometry.

Notable heuristics:

- Surface estimates use ORS `surface` extra info
- Road-type quality uses ORS `waytype` distribution conservatively
- Ride duration is recalculated with `services.duration_estimator` from FTP, total system weight, route profile, and light surface/urban penalties
- Repeated-segment detection ignores the first and last 10% of segments so short home-exit overlap is tolerated
- Urbanity is estimated from route length and road composition
- Novelty is approximated from point uniqueness and repeated-segment ratio

### 3. Filtering and ranking

`services.ranking.rank_routes()`:

- Rejects routes with excessive repeat behavior
- Scores remaining routes with `domain.scoring.score_route()`
- Keeps stronger distance/elevation matches ahead of weaker-fit fallback routes
- Sorts descending by `overall_fit_score` within each bucket

### 4. Export

CLI-only export behavior:

- `services.exporter.export_gpx()` writes a GPX track for each of the top 3 routes
- `services.debug_export.dump_debug_run()` writes the request and score breakdowns to JSON

## CORS

The FastAPI app allows requests from:

- `http://localhost:3000`
- `http://127.0.0.1:3000`

If the frontend is served from a different origin, update the CORS list in [api/main.py](/Users/maximehumbert/Documents/GitHub/ride-wit-me/api/main.py).

## Data Files

### `data/test_requests.json`

Contains example ride requests that are useful for manual testing and smoke checks.

### `data/rider_profile.json`

Currently empty. This appears reserved for future personalization work.

### `data/presets.json`

Currently empty. This appears reserved for named ride templates or request presets.

## Operational Notes

- The backend currently depends on outbound network access to OpenRouteService.
- There is no caching layer.
- There is no provider retry or rate-limit management beyond the provider timeout.
- There is no persistence layer or database.
- Errors from provider failures will surface as backend failures if no candidates succeed.
