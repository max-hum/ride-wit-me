from __future__ import annotations

from typing import List

from domain.models import EnrichedRoute, RideRequest, ScoredRoute
from domain.scoring import score_route


MAX_REPEATED_SEGMENT_RATIO = 0.12
MAX_LONGEST_REPEATED_BLOCK_KM = 2.0


def _is_acceptable_loop(route: EnrichedRoute) -> bool:
    if route.repeated_segment_ratio > MAX_REPEATED_SEGMENT_RATIO:
        return False

    if route.longest_repeated_block_km > MAX_LONGEST_REPEATED_BLOCK_KM:
        return False

    return True


def rank_routes(routes: List[EnrichedRoute], request: RideRequest) -> List[ScoredRoute]:
    filtered_routes = [route for route in routes if _is_acceptable_loop(route)]

    # Fallback: if filter is too strict and removes everything,
    # keep all routes rather than returning nothing.
    if not filtered_routes:
        filtered_routes = routes

    scored = [score_route(route, request) for route in filtered_routes]
    scored.sort(key=lambda route: route.fit.overall_fit_score, reverse=True)
    return scored