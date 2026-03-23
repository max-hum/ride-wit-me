from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


LatLng = Tuple[float, float, float]


class RideStyle(str, Enum):
    ENDURANCE = "endurance"
    HILLY = "hilly"
    SCENIC = "scenic"
    EXPLORATION = "exploration"


class StartPoint(BaseModel):
    lat: float
    lng: float


class AvoidPreferences(BaseModel):
    busy_roads: bool = True
    urban: bool = True
    unpaved: bool = True
    repeated_segments: bool = True


class PreferPreferences(BaseModel):
    scenic: bool = True
    rolling_roads: bool = True
    novelty: bool = False


class RideRequest(BaseModel):
    start_point: StartPoint
    distance_km: float = Field(..., gt=0)
    elevation_m: float = Field(..., ge=0)
    ride_style: RideStyle = RideStyle.ENDURANCE
    avoid: AvoidPreferences = Field(default_factory=AvoidPreferences)
    prefer: PreferPreferences = Field(default_factory=PreferPreferences)


class CandidateRoute(BaseModel):
    route_id: str
    provider: str
    geometry: List[LatLng]

    distance_km: float
    elevation_m: float
    estimated_duration_min: float

    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnrichedRoute(BaseModel):
    candidate: CandidateRoute

    # positive scores / ratios
    paved_ratio: float = 1.0
    minor_road_ratio: float = 0.5
    scenic_score: float = 0.5
    climbing_score: float = 0.5
    ride_feel_score: float = 0.5
    novelty_score: float = 0.5

    # penalties / negative characteristics
    urban_ratio: float = 0.0
    busy_road_ratio: float = 0.0
    unpaved_ratio: float = 0.0
    repeated_segment_ratio: float = 0.0
    longest_repeated_block_km: float = 0.0

    enrichment_notes: Dict[str, Any] = Field(default_factory=dict)


class FitBreakdown(BaseModel):
    overall_fit_score: float

    distance_fit_score: float
    elevation_fit_score: float

    road_quality_score: float
    ride_feel_score: float
    scenic_score: float
    climbing_score: float
    novelty_score: float

    busy_road_penalty: float
    urban_penalty: float
    unpaved_penalty: float
    repeat_penalty: float
    branch_penalty: float


class ScoredRoute(BaseModel):
    enriched: EnrichedRoute
    fit: FitBreakdown
    reason_summary: str