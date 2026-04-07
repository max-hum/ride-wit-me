# Architecture

## Overview

Ride Wit Me has two runtime surfaces:

- A Python backend for route generation and scoring
- A Next.js frontend for request entry, route visualization, and GPX download

The backend owns route computation. The frontend is a thin client over the API.

## High-Level Flow

```text
Next.js UI
   |
   | POST /generate-route
   v
FastAPI API
   |
   v
route_service.generate_routes
   |
   +--> candidate_generator
   |       |
   |       v
   |   OpenRouteService directions API
   |
   +--> enrichment
   |
   +--> ranking
   |
   v
JSON response to frontend
```

The CLI uses the same backend pipeline, then adds GPX and debug-run export steps.

## Backend Layers

### `domain/`

Contains the core data models and scoring logic:

- `domain.models`
  - Request models
  - Candidate, enriched, and scored route models
  - Ride style enum
- `domain.scoring`
  - Ride-style weight maps
  - Positive score and penalty calculations
  - Human-readable route reason summaries

### `services/`

Contains the operational pipeline:

- `route_service.py`
  - Orchestrates generation, enrichment, and ranking
- `candidate_generator.py`
  - Delegates candidate creation to a routing provider
- `routing_provider.py`
  - Implements OpenRouteService integration
- `enrichment.py`
  - Converts route metadata and geometry into heuristic quality signals
- `ranking.py`
  - Rejects unacceptable loop shapes, scores, and sorts routes
- `exporter.py`
  - Writes GPX files
- `debug_export.py`
  - Writes JSON artifacts for inspection

### `api/`

Exposes FastAPI routes:

- `GET /health`
- `POST /generate-route`

### `app/`

Contains:

- `app.main`
  - CLI entrypoint
- `app.config`
  - Environment loading and output path configuration

## Candidate Generation Strategy

The backend does not ask the provider for one route and accept it blindly. It constructs several waypoint families around the starting coordinate:

- Family A: 2-anchor loops
- Family B: 3-anchor loops
- Family C: tighter 2-anchor loops intended to reduce distance overshoot

Each waypoint family is rotated across several bearings. Every coordinate set is sent to OpenRouteService, and successful responses become `CandidateRoute` instances.

If all provider requests fail, the backend raises a `RoutingProviderError`.

## Enrichment Model

Each provider route is converted into an `EnrichedRoute` with heuristic signals:

- `paved_ratio`
- `minor_road_ratio`
- `scenic_score`
- `climbing_score`
- `ride_feel_score`
- `novelty_score`
- `urban_ratio`
- `busy_road_ratio`
- `unpaved_ratio`
- `repeated_segment_ratio`
- `longest_repeated_block_km`

The backend derives these from:

- OpenRouteService `extra_info` payloads for `surface` and `waytype`
- Route geometry analysis
- Distance and elevation characteristics

These signals are estimates, not guarantees. They are intentionally coarse and are documented as v0 heuristics in the code.

## Ranking Model

Ranking has two stages:

### 1. Loop-shape filtering

Routes are rejected if they exceed either of these thresholds:

- `repeated_segment_ratio > 0.12`
- `longest_repeated_block_km > 2.0`

If every route fails the filter, the backend falls back to scoring all routes instead of returning nothing.

### 2. Weighted scoring

`domain.scoring.score_route()` combines:

- Distance fit
- Elevation fit
- Road quality
- Ride feel
- Scenic quality
- Climbing character
- Novelty

It then subtracts penalties for:

- Busy roads
- Urban exposure
- Unpaved surfaces
- Repeated segments
- Long repeated branches

Ride style changes the weights applied to the positive score components.

## Frontend Architecture

The frontend is a client-rendered Next.js App Router application.

- `web/app/page.tsx`
  - Owns the request form, selected-route state, results list, shared map/profile area, and GPX download logic
- `web/components/Map.tsx`
  - Renders route polylines with Leaflet via `react-leaflet`
  - Visually emphasizes the selected route while still showing alternatives
- `web/components/ElevationProfile.tsx`
  - Renders the elevation chart for the active route

The map component is loaded dynamically with `ssr: false` because Leaflet depends on browser APIs.

## Outputs

When using the CLI:

- GPX routes are written to `outputs/routes/`
- JSON debug runs are written to `outputs/debug_runs/`

The API itself does not write GPX files; it only returns JSON.
