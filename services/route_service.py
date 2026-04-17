from __future__ import annotations

from typing import List, Optional

from domain.models import RideRequest, ScoredRoute
from services.candidate_generator import CandidateGenerator
from services.enrichment import enrich_route
from services.ranking import MIN_PREFERRED_ROUTE_COUNT, count_preferred_routes, rank_routes


def generate_routes(
    request: RideRequest,
    api_key: Optional[str] = None,
) -> List[ScoredRoute]:
    generator = CandidateGenerator(api_key=api_key)

    baseline_candidates = generator.generate(request, strategy="baseline")
    enriched_routes = [enrich_route(route, request) for route in baseline_candidates]
    ranked_routes = rank_routes(enriched_routes, request)

    if count_preferred_routes(ranked_routes) < MIN_PREFERRED_ROUTE_COUNT:
        expanded_candidates = generator.generate(request, strategy="expanded")
        enriched_routes.extend(enrich_route(route, request) for route in expanded_candidates)
        ranked_routes = rank_routes(enriched_routes, request)

    return ranked_routes
