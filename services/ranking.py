from __future__ import annotations

from typing import List

from domain.models import EnrichedRoute, RideRequest, ScoredRoute
from domain.scoring import score_route


MAX_REPEATED_SEGMENT_RATIO = 0.12
MAX_LONGEST_REPEATED_BLOCK_KM = 2.0
MIN_PREFERRED_ROUTE_COUNT = 5
MIN_PREFERRED_TARGET_MATCH_SCORE = 0.45


def _is_acceptable_loop(route: EnrichedRoute) -> bool:
    if route.repeated_segment_ratio > MAX_REPEATED_SEGMENT_RATIO:
        return False

    if route.longest_repeated_block_km > MAX_LONGEST_REPEATED_BLOCK_KM:
        return False

    return True


def _target_match_score(route: ScoredRoute) -> float:
    return (
        route.fit.distance_fit_score + route.fit.elevation_fit_score
    ) / 2.0


def _is_preferred_candidate(route: ScoredRoute) -> bool:
    return _target_match_score(route) >= MIN_PREFERRED_TARGET_MATCH_SCORE


def count_preferred_routes(routes: List[ScoredRoute]) -> int:
    return sum(1 for route in routes if _is_preferred_candidate(route))


def rank_routes(routes: List[EnrichedRoute], request: RideRequest) -> List[ScoredRoute]:
    filtered_routes = [route for route in routes if _is_acceptable_loop(route)]

    if not filtered_routes:
        return []

    scored = [score_route(route, request) for route in filtered_routes]

    preferred_routes = [route for route in scored if _is_preferred_candidate(route)]
    fallback_routes = [route for route in scored if not _is_preferred_candidate(route)]

    preferred_routes.sort(key=lambda route: route.fit.overall_fit_score, reverse=True)
    fallback_routes.sort(key=lambda route: route.fit.overall_fit_score, reverse=True)

    return preferred_routes + fallback_routes
