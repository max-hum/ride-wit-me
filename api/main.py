from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from domain.models import GeocodeResult, RideRequest, ScoredRoute
from services.routing_provider import OpenRouteServiceProvider, RoutingProviderError
from services.route_service import generate_routes

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ride Wit Me API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ride-wit-me.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_ors_api_key(x_ors_api_key: str | None) -> str | None:
    if x_ors_api_key is None:
        return None

    trimmed = x_ors_api_key.strip()
    return trimmed or None

class GenerateRouteResponse(BaseModel):
    routes: list[dict]


class GeocodeSearchResponse(BaseModel):
    results: list[GeocodeResult]


def scored_route_to_dict(route: ScoredRoute) -> dict:
    candidate = route.enriched.candidate
    fit = route.fit
    enriched = route.enriched

    return {
        "route_id": candidate.route_id,
        "provider": candidate.provider,
        "distance_km": candidate.distance_km,
        "elevation_m": candidate.elevation_m,
        "estimated_duration_min": candidate.estimated_duration_min,
        "geometry": [
            {"lat": lat, "lng": lng, "ele": ele}
            for lat, lng, ele in candidate.geometry
        ],
        "fit": fit.model_dump(),
        "reason_summary": route.reason_summary,
        "enriched": {
            "paved_ratio": enriched.paved_ratio,
            "minor_road_ratio": enriched.minor_road_ratio,
            "scenic_score": enriched.scenic_score,
            "climbing_score": enriched.climbing_score,
            "ride_feel_score": enriched.ride_feel_score,
            "novelty_score": enriched.novelty_score,
            "urban_ratio": enriched.urban_ratio,
            "busy_road_ratio": enriched.busy_road_ratio,
            "unpaved_ratio": enriched.unpaved_ratio,
            "repeated_segment_ratio": enriched.repeated_segment_ratio,
            "longest_repeated_block_km": enriched.longest_repeated_block_km,
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/geocode/search", response_model=GeocodeSearchResponse)
def geocode_search(
    text: str,
    x_ors_api_key: str | None = Header(default=None, alias="X-ORS-API-Key"),
) -> GeocodeSearchResponse:
    query = text.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required.")

    try:
        provider = OpenRouteServiceProvider(api_key=resolve_ors_api_key(x_ors_api_key))
        results = provider.geocode_search(query)
    except RoutingProviderError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {err}") from err

    return GeocodeSearchResponse(results=results)


@app.post("/generate-route", response_model=GenerateRouteResponse)
def generate_route(
    request: RideRequest,
    x_ors_api_key: str | None = Header(default=None, alias="X-ORS-API-Key"),
) -> GenerateRouteResponse:
    ranked_routes = generate_routes(
        request,
        api_key=resolve_ors_api_key(x_ors_api_key),
    )
    return GenerateRouteResponse(
        routes=[scored_route_to_dict(route) for route in ranked_routes]
    )
