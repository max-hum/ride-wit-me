from __future__ import annotations

from typing import List

from domain.models import RideRequest, ScoredRoute
from services.candidate_generator import CandidateGenerator
from services.enrichment import enrich_route
from services.ranking import MIN_PREFERRED_ROUTE_COUNT, count_preferred_routes, rank_routes


def generate_routes(request: RideRequest) -> List[ScoredRoute]:
    generator = CandidateGenerator()

    baseline_candidates = generator.generate(request, strategy="baseline")
    enriched_routes = [enrich_route(route) for route in baseline_candidates]
    ranked_routes = rank_routes(enriched_routes, request)

    if count_preferred_routes(ranked_routes) < MIN_PREFERRED_ROUTE_COUNT:
        expanded_candidates = generator.generate(request, strategy="expanded")
        enriched_routes.extend(enrich_route(route) for route in expanded_candidates)
        ranked_routes = rank_routes(enriched_routes, request)

    return ranked_routes
