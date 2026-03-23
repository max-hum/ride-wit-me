from __future__ import annotations

from typing import List

from domain.models import RideRequest, ScoredRoute
from services.candidate_generator import CandidateGenerator
from services.enrichment import enrich_route
from services.ranking import rank_routes


def generate_routes(request: RideRequest) -> List[ScoredRoute]:
    generator = CandidateGenerator()
    candidates = generator.generate(request)
    enriched_routes = [enrich_route(route) for route in candidates]
    ranked_routes = rank_routes(enriched_routes, request)
    return ranked_routes