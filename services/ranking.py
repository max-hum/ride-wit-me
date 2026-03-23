from __future__ import annotations

from typing import List

from domain.models import EnrichedRoute, RideRequest, ScoredRoute
from domain.scoring import score_route


def rank_routes(routes: List[EnrichedRoute], request: RideRequest) -> List[ScoredRoute]:
    scored = [score_route(route, request) for route in routes]
    scored.sort(key=lambda route: route.fit.overall_fit_score, reverse=True)
    return scored