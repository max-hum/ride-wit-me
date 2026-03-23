from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from domain.models import RideRequest, ScoredRoute
from services.route_service import generate_routes


app = FastAPI(title="Ride Wit Me API")


class GenerateRouteResponse(BaseModel):
    routes: list[dict]


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


@app.post("/generate-route", response_model=GenerateRouteResponse)
def generate_route(request: RideRequest) -> GenerateRouteResponse:
    ranked_routes = generate_routes(request)
    return GenerateRouteResponse(
        routes=[scored_route_to_dict(route) for route in ranked_routes]
    )