# API

## Base URL

Local development default:

```text
http://127.0.0.1:8000
```

## Endpoints

### `GET /health`

Returns a simple readiness response.

Example response:

```json
{
  "status": "ok"
}
```

### `GET /geocode/search`

Resolves an address or place string into candidate coordinates for the frontend.

Query parameters:

- `text`: required search string

Example response:

```json
{
  "results": [
    {
      "label": "Metz, Moselle, Grand Est, France",
      "lat": 49.1193,
      "lng": 6.1757
    }
  ]
}
```

### `POST /generate-route`

Generates, enriches, ranks, and returns route candidates.

## Request Schema

```json
{
  "start_point": {
    "lat": 49.3597,
    "lng": 6.1685
  },
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

## Request Fields

### `start_point`

- `lat`: number
- `lng`: number

### `distance_km`

- number
- must be greater than `0`

### `elevation_m`

- number
- must be greater than or equal to `0`

### `ride_style`

Allowed values:

- `endurance`
- `hilly`
- `scenic`
- `exploration`

### `avoid`

All fields are boolean and default to `true` if omitted:

- `busy_roads`
- `urban`
- `unpaved`
- `repeated_segments`

### `prefer`

Boolean fields:

- `scenic` defaults to `true`
- `rolling_roads` defaults to `true`
- `novelty` defaults to `false`

## Response Schema

Successful responses return:

```json
{
  "routes": [
    {
      "route_id": "ors-120305-00-abc123",
      "provider": "openrouteservice",
      "distance_km": 64.2,
      "elevation_m": 694,
      "estimated_duration_min": 154.6,
      "geometry": [
        { "lat": 49.3597, "lng": 6.1685, "ele": 220.1 }
      ],
      "fit": {
        "overall_fit_score": 0.812,
        "distance_fit_score": 0.941,
        "elevation_fit_score": 0.972,
        "road_quality_score": 0.735,
        "ride_feel_score": 0.681,
        "scenic_score": 0.744,
        "climbing_score": 0.65,
        "novelty_score": 0.831,
        "busy_road_penalty": 0.072,
        "urban_penalty": 0.049,
        "unpaved_penalty": 0.018,
        "repeat_penalty": 0.0,
        "branch_penalty": 0.0
      },
      "reason_summary": "very close to target distance, very close to target elevation, good road quality",
      "enriched": {
        "paved_ratio": 0.91,
        "minor_road_ratio": 0.6,
        "scenic_score": 0.744,
        "climbing_score": 0.65,
        "ride_feel_score": 0.681,
        "novelty_score": 0.831,
        "urban_ratio": 0.352,
        "busy_road_ratio": 0.4,
        "unpaved_ratio": 0.044,
        "repeated_segment_ratio": 0.0,
        "longest_repeated_block_km": 0.0
      }
    }
  ]
}
```

## Response Field Notes

### `geometry`

The API returns geometry as an array of objects:

- `lat`
- `lng`
- `ele`

This is a transformed representation of the provider route geometry.

### `fit`

`fit` is the ranking breakdown used to sort routes. `overall_fit_score` is the final score after positive weights and penalties are combined and clamped to the `0..1` range.

### `reason_summary`

This is a short human-readable explanation built from the score breakdown. It is intended for UI display, not for strict programmatic logic.

## Error Behavior

Possible failure cases include:

- Missing `OPENROUTESERVICE_API_KEY`
- Upstream OpenRouteService request failure
- No route candidates generated successfully
- Request validation errors from FastAPI/Pydantic

The API currently does not define custom error envelopes. FastAPI default error responses should be expected.

## CORS

Allowed local origins:

- `http://localhost:3000`
- `http://127.0.0.1:3000`
