from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from domain.models import RideRequest, ScoredRoute


def dump_debug_run(
    request: RideRequest,
    ranked_routes: List[ScoredRoute],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"run_{timestamp}.json"

    payload = {
        "request": request.model_dump(mode="json"),
        "routes": [
            {
                "route_id": route.enriched.candidate.route_id,
                "provider": route.enriched.candidate.provider,
                "distance_km": route.enriched.candidate.distance_km,
                "elevation_m": route.enriched.candidate.elevation_m,
                "estimated_duration_min": route.enriched.candidate.estimated_duration_min,
                "provider_duration_min": route.enriched.candidate.metadata.get(
                    "provider_duration_min"
                ),
                "duration_estimate": route.enriched.candidate.metadata.get(
                    "duration_estimate"
                ),
                "fit": route.fit.model_dump(),
                "reason_summary": route.reason_summary,
                "enriched": {
                    "paved_ratio": route.enriched.paved_ratio,
                    "minor_road_ratio": route.enriched.minor_road_ratio,
                    "scenic_score": route.enriched.scenic_score,
                    "climbing_score": route.enriched.climbing_score,
                    "ride_feel_score": route.enriched.ride_feel_score,
                    "novelty_score": route.enriched.novelty_score,
                    "urban_ratio": route.enriched.urban_ratio,
                    "busy_road_ratio": route.enriched.busy_road_ratio,
                    "unpaved_ratio": route.enriched.unpaved_ratio,
                    "repeated_segment_ratio": route.enriched.repeated_segment_ratio,
                },
            }
            for route in ranked_routes
        ],
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return file_path
