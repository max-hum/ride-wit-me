from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from domain.models import CandidateRoute, EnrichedRoute


# OpenRouteService extra_info mappings:
# https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/extra-info/
#
# We only use coarse groupings for v0.

PAVED_SURFACE_VALUES = {
    1,   # paved
    2,   # asphalt
    3,   # concrete
    4,   # cobblestone
    5,   # metal
    6,   # wood
    7,   # compacted gravel-ish / can be debated, keep out if too generous
}

UNPAVED_SURFACE_VALUES = {
    8,   # unpaved
    9,   # fine gravel
    10,  # gravel
    11,  # dirt
    12,  # ground
    13,  # ice
    14,  # sand
    15,  # woodchips
    16,  # grass
    17,  # grass pavers
}

MINOR_WAYTYPE_VALUES = {
    6,  # path
    7,  # track
    8,  # cycleway
    9,  # footway
    10, # steps
    11, # ferry
}

MAJOR_WAYTYPE_VALUES = {
    1,  # state road
    2,  # road
    3,  # street
    4,  # path? depends on API version
    5,  # track? depends on API version
}

# Because ORS enum values can vary by profile/version, v0 keeps these heuristics loose.


def enrich_route(candidate: CandidateRoute) -> EnrichedRoute:
    metadata = candidate.metadata or {}
    extras = metadata.get("extras", {})

    surface_distribution = _extract_distribution(extras.get("surface", {}))
    waytype_distribution = _extract_distribution(extras.get("waytype", {}))

    paved_ratio, unpaved_ratio = _estimate_surface_ratios(surface_distribution)
    minor_road_ratio, busy_road_ratio = _estimate_waytype_ratios(waytype_distribution)
    repeated_segment_ratio = _estimate_repeat_ratio(candidate.geometry)
    urban_ratio = _estimate_urban_ratio(candidate, minor_road_ratio)
    scenic_score = _estimate_scenic_score(urban_ratio, minor_road_ratio, repeated_segment_ratio)
    climbing_score = _estimate_climbing_score(candidate)
    ride_feel_score = _estimate_ride_feel_score(candidate, repeated_segment_ratio, busy_road_ratio)
    novelty_score = _estimate_novelty_score(repeated_segment_ratio, candidate.geometry)

    notes = {
        "surface_distribution": surface_distribution,
        "waytype_distribution": waytype_distribution,
    }

    return EnrichedRoute(
        candidate=candidate,
        paved_ratio=round(paved_ratio, 3),
        minor_road_ratio=round(minor_road_ratio, 3),
        scenic_score=round(scenic_score, 3),
        climbing_score=round(climbing_score, 3),
        ride_feel_score=round(ride_feel_score, 3),
        novelty_score=round(novelty_score, 3),
        urban_ratio=round(urban_ratio, 3),
        busy_road_ratio=round(busy_road_ratio, 3),
        unpaved_ratio=round(unpaved_ratio, 3),
        repeated_segment_ratio=round(repeated_segment_ratio, 3),
        enrichment_notes=notes,
    )


def _extract_distribution(extra_info: Dict) -> Dict[int, float]:
    """
    ORS extras can contain either:
    - "summary": list of {"value": X, "amount": Y}
    - "values": list of [from, to, value]

    We always normalize the result so returned shares sum to ~1.0.
    """
    summary = extra_info.get("summary")
    if summary:
        raw_distribution = {}
        total = 0.0

        for item in summary:
            value = int(item.get("value"))
            amount = float(item.get("amount", 0.0))
            raw_distribution[value] = raw_distribution.get(value, 0.0) + amount
            total += amount

        if total > 0:
            return {k: v / total for k, v in raw_distribution.items()}
        return {}

    values = extra_info.get("values", [])
    raw_distribution: Dict[int, float] = {}

    for item in values:
        if len(item) >= 3:
            start_idx, end_idx, value = item[0], item[1], item[2]
            span = max(1, end_idx - start_idx)
            value = int(value)
            raw_distribution[value] = raw_distribution.get(value, 0.0) + span

    total = sum(raw_distribution.values())
    if total > 0:
        return {k: v / total for k, v in raw_distribution.items()}

    return {}


def _estimate_surface_ratios(surface_distribution: Dict[int, float]) -> Tuple[float, float]:
    if not surface_distribution:
        return 0.85, 0.15

    paved = 0.0
    unpaved = 0.0

    for value, share in surface_distribution.items():
        if value in PAVED_SURFACE_VALUES:
            paved += share
        elif value in UNPAVED_SURFACE_VALUES:
            unpaved += share

    known = paved + unpaved
    unknown = max(0.0, 1.0 - known)

    # Unknown gets split conservatively.
    paved += unknown * 0.6
    unpaved += unknown * 0.4

    return _clamp01(paved), _clamp01(unpaved)


def _estimate_waytype_ratios(waytype_distribution: Dict[int, float]) -> Tuple[float, float]:
    """
    v0 simplified logic:
    - treat everything as "mixed" instead of trusting ORS enums
    - derive busy vs minor from a safer heuristic
    """

    if not waytype_distribution:
        return 0.5, 0.5

    # Instead of relying on broken enums,
    # assume:
    # - diversity of waytypes = better roads
    # - concentration = more "main road bias"

    diversity = len(waytype_distribution)

    if diversity >= 4:
        minor = 0.6
    elif diversity >= 2:
        minor = 0.45
    else:
        minor = 0.3

    busy = 1.0 - minor

    return minor, busy


def _estimate_repeat_ratio(geometry: List[Tuple[float, float]]) -> float:
    if not geometry:
        return 0.0

    rounded_points = [(round(lat, 4), round(lng, 4)) for lat, lng in geometry]
    unique_points = len(set(rounded_points))
    total_points = len(rounded_points)

    uniqueness_ratio = unique_points / total_points if total_points else 1.0
    repeat_ratio = 1.0 - uniqueness_ratio

    return _clamp01(repeat_ratio)


def _estimate_urban_ratio(candidate: CandidateRoute, minor_road_ratio: float) -> float:
    distance_component = max(0.0, min(1.0, (70.0 - candidate.distance_km) / 70.0))
    road_component = 1.0 - minor_road_ratio
    urban_ratio = 0.4 * distance_component + 0.6 * road_component
    return _clamp01(urban_ratio)


def _estimate_scenic_score(
    urban_ratio: float,
    minor_road_ratio: float,
    repeated_segment_ratio: float,
) -> float:
    value = (
        0.45 * (1.0 - urban_ratio)
        + 0.35 * minor_road_ratio
        + 0.20 * (1.0 - repeated_segment_ratio)
    )
    return _clamp01(value)


def _estimate_climbing_score(candidate: CandidateRoute) -> float:
    if candidate.distance_km <= 0:
        return 0.0

    elev_per_km = candidate.elevation_m / candidate.distance_km

    if elev_per_km <= 4:
        return 0.20
    if elev_per_km <= 7:
        return 0.45
    if elev_per_km <= 10:
        return 0.65
    if elev_per_km <= 13:
        return 0.80
    if elev_per_km <= 16:
        return 0.92
    return 1.0


def _estimate_ride_feel_score(
    candidate: CandidateRoute,
    repeated_segment_ratio: float,
    busy_road_ratio: float,
) -> float:
    geometry_points = len(candidate.geometry)

    if geometry_points < 80:
        flow_proxy = 0.45
    elif geometry_points < 180:
        flow_proxy = 0.62
    else:
        flow_proxy = 0.75

    value = (
        0.45 * flow_proxy
        + 0.30 * (1.0 - repeated_segment_ratio)
        + 0.25 * (1.0 - busy_road_ratio)
    )
    return _clamp01(value)


def _estimate_novelty_score(
    repeated_segment_ratio: float,
    geometry: List[Tuple[float, float]],
) -> float:
    if not geometry:
        return 0.0

    rounded_points = [(round(lat, 3), round(lng, 3)) for lat, lng in geometry]
    uniqueness = len(set(rounded_points)) / len(rounded_points)
    value = 0.7 * uniqueness + 0.3 * (1.0 - repeated_segment_ratio)
    return _clamp01(value)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))