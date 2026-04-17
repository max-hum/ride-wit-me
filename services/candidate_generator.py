from __future__ import annotations

from typing import List, Optional

from domain.models import CandidateRoute, RideRequest
from services.routing_provider import OpenRouteServiceProvider


class CandidateGenerator:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.provider = OpenRouteServiceProvider(api_key=api_key)

    def generate(
        self,
        request: RideRequest,
        strategy: str = "baseline",
    ) -> List[CandidateRoute]:
        return self.provider.generate_candidate_routes(request, strategy=strategy)
