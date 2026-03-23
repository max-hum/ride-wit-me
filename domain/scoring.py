from __future__ import annotations

from typing import Dict

from domain.models import EnrichedRoute, FitBreakdown, RideRequest, RideStyle, ScoredRoute


STYLE_WEIGHTS: Dict[RideStyle, Dict[str, float]] = {
    RideStyle.ENDURANCE: {
        "distance_fit": 0.40,
        "elevation_fit": 0.40,
        "road_quality": 0.16,
        "ride_feel": 0.00,
        "scenic": 0.00,
        "climbing": 0.00,
        "novelty": 0.04,
    },
    RideStyle.HILLY: {
        "distance_fit": 0.12,
        "elevation_fit": 0.20,
        "road_quality": 0.16,
        "ride_feel": 0.12,
        "scenic": 0.08,
        "climbing": 0.24,
        "novelty": 0.08,
    },
    RideStyle.SCENIC: {
        "distance_fit": 0.12,
        "elevation_fit": 0.10,
        "road_quality": 0.20,
        "ride_feel": 0.15,
        "scenic": 0.25,
        "climbing": 0.08,
        "novelty": 0.10,
    },
    RideStyle.EXPLORATION: {
        "distance_fit": 0.10,
        "elevation_fit": 0.10,
        "road_quality": 0.16,
        "ride_feel": 0.16,
        "scenic": 0.10,
        "climbing": 0.08,
        "novelty": 0.30,
    },
}

PENALTY_WEIGHTS = {
    "busy_roads": 0.18,
    "urban": 0.14,
    "unpaved": 0.60,
    "repeated_segments": 0.60,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _target_fit_score(actual: float, target: float, tolerance_ratio: float) -> float:
    """
    Returns:
    - 1.0 when exact match
    - 0.0 when outside tolerance band
    - linear interpolation in between
    """
    if target <= 0:
        return 0.0

    error_ratio = abs(actual - target) / target
    if error_ratio >= tolerance_ratio:
        return 0.0

    return _clamp01(1.0 - (error_ratio / tolerance_ratio))


def _road_quality_score(route: EnrichedRoute) -> float:
    return _clamp01(
        0.40 * route.paved_ratio
        + 0.35 * route.minor_road_ratio
        + 0.25 * (1.0 - route.busy_road_ratio)
    )


def _toggle_multiplier(enabled: bool, when_true: float = 1.15, when_false: float = 1.0) -> float:
    return when_true if enabled else when_false


def score_route(route: EnrichedRoute, request: RideRequest) -> ScoredRoute:
    style_weights = STYLE_WEIGHTS[request.ride_style]

    distance_fit_score = _target_fit_score(
        actual=route.candidate.distance_km,
        target=request.distance_km,
        tolerance_ratio=0.30,
    )

    elevation_fit_score = _target_fit_score(
        actual=route.candidate.elevation_m,
        target=request.elevation_m,
        tolerance_ratio=0.30,
    )

    road_quality_score = _road_quality_score(route)
    ride_feel_score = _clamp01(route.ride_feel_score)

    scenic_score = _clamp01(
        route.scenic_score * _toggle_multiplier(request.prefer.scenic)
    )

    climbing_score = _clamp01(
        route.climbing_score * _toggle_multiplier(request.prefer.rolling_roads, when_true=1.10)
    )

    novelty_score = _clamp01(
        route.novelty_score * _toggle_multiplier(request.prefer.novelty, when_true=1.25)
    )

    positive_score = (
        style_weights["distance_fit"] * distance_fit_score
        + style_weights["elevation_fit"] * elevation_fit_score
        + style_weights["road_quality"] * road_quality_score
        + style_weights["ride_feel"] * ride_feel_score
        + style_weights["scenic"] * scenic_score
        + style_weights["climbing"] * climbing_score
        + style_weights["novelty"] * novelty_score
    )

    busy_road_penalty = (
        PENALTY_WEIGHTS["busy_roads"] * route.busy_road_ratio
        if request.avoid.busy_roads
        else 0.0
    )
    urban_penalty = (
        PENALTY_WEIGHTS["urban"] * route.urban_ratio
        if request.avoid.urban
        else 0.0
    )
    unpaved_penalty = (
        PENALTY_WEIGHTS["unpaved"] * route.unpaved_ratio
        if request.avoid.unpaved
        else 0.0
    )
    repeat_penalty = (
        PENALTY_WEIGHTS["repeated_segments"] * route.repeated_segment_ratio
        if request.avoid.repeated_segments
        else 0.0
    )

    overall_fit_score = _clamp01(
        positive_score
        - busy_road_penalty
        - urban_penalty
        - unpaved_penalty
        - repeat_penalty
    )

    fit = FitBreakdown(
        overall_fit_score=round(overall_fit_score, 3),
        distance_fit_score=round(distance_fit_score, 3),
        elevation_fit_score=round(elevation_fit_score, 3),
        road_quality_score=round(road_quality_score, 3),
        ride_feel_score=round(ride_feel_score, 3),
        scenic_score=round(scenic_score, 3),
        climbing_score=round(climbing_score, 3),
        novelty_score=round(novelty_score, 3),
        busy_road_penalty=round(busy_road_penalty, 3),
        urban_penalty=round(urban_penalty, 3),
        unpaved_penalty=round(unpaved_penalty, 3),
        repeat_penalty=round(repeat_penalty, 3),
    )

    reasons = []

    if fit.distance_fit_score >= 0.85:
        reasons.append("very close to target distance")
    if fit.elevation_fit_score >= 0.85:
        reasons.append("very close to target elevation")
    if fit.road_quality_score >= 0.75:
        reasons.append("good road quality")
    if fit.scenic_score >= 0.75:
        reasons.append("pleasant road scenery")
    if fit.climbing_score >= 0.75:
        reasons.append("strong climbing character")
    if fit.novelty_score >= 0.75:
        reasons.append("good route variety")

    if fit.busy_road_penalty >= 0.10:
        reasons.append("too much busy-road exposure")
    if fit.urban_penalty >= 0.10:
        reasons.append("too urban")
    if fit.unpaved_penalty >= 0.10:
        reasons.append("too much unpaved surface")
    if fit.repeat_penalty >= 0.08:
        reasons.append("too many repeated segments")

    reason_summary = ", ".join(reasons[:3]) if reasons else "balanced route candidate"

    return ScoredRoute(
        enriched=route,
        fit=fit,
        reason_summary=reason_summary,
    )