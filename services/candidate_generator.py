from __future__ import annotations

from typing import List

from domain.models import CandidateRoute, RideRequest
from services.routing_provider import OpenRouteServiceProvider


class CandidateGenerator:
    def __init__(self) -> None:
        self.provider = OpenRouteServiceProvider()

    def generate(
        self,
        request: RideRequest,
        strategy: str = "baseline",
    ) -> List[CandidateRoute]:
        return self.provider.generate_candidate_routes(request, strategy=strategy)
