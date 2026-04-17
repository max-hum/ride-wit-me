from __future__ import annotations

import unittest
from typing import Optional

from domain.models import CandidateRoute, RideRequest, StartPoint
from services.duration_estimator import estimate_ride_duration
from services.enrichment import enrich_route


def build_request(*, ftp_watts: float, system_weight_kg: float) -> RideRequest:
    return RideRequest(
        start_point=StartPoint(lat=49.0, lng=6.0),
        distance_km=60.0,
        elevation_m=600.0,
        ftp_watts=ftp_watts,
        system_weight_kg=system_weight_kg,
        ride_style="endurance",
    )


def build_geometry(
    *,
    total_distance_km: int,
    uphill_gain_per_km_m: float,
) -> list[tuple[float, float, float]]:
    lat = 49.0
    lng = 6.0
    ele = 200.0
    lat_step = 1.0 / 111.0

    points = [(lat, lng, ele)]
    half = total_distance_km // 2

    for idx in range(total_distance_km):
        lat += lat_step
        if idx < half:
            ele += uphill_gain_per_km_m
        else:
            ele -= uphill_gain_per_km_m
        points.append((lat, lng, ele))

    return points


def build_candidate(
    *,
    distance_km: float,
    elevation_m: float,
    provider_duration_min: float,
    geometry: list[tuple[float, float, float]],
    surface_summary: Optional[list[dict]] = None,
    waytype_summary: Optional[list[dict]] = None,
) -> CandidateRoute:
    return CandidateRoute(
        route_id="test-route",
        provider="openrouteservice",
        geometry=geometry,
        distance_km=distance_km,
        elevation_m=elevation_m,
        estimated_duration_min=provider_duration_min,
        metadata={
            "provider_duration_min": provider_duration_min,
            "summary": {
                "distance": distance_km * 1000.0,
                "duration": provider_duration_min * 60.0,
            },
            "extras": {
                "surface": {"summary": surface_summary or []},
                "waytype": {"summary": waytype_summary or []},
            },
        },
    )


class DurationEstimatorTests(unittest.TestCase):
    def test_higher_ftp_shortens_duration(self) -> None:
        geometry = build_geometry(total_distance_km=60, uphill_gain_per_km_m=20.0)
        candidate = build_candidate(
            distance_km=60.0,
            elevation_m=600.0,
            provider_duration_min=165.0,
            geometry=geometry,
        )

        slower, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=240.0, system_weight_kg=83.0),
            paved_ratio=0.95,
            unpaved_ratio=0.05,
            busy_road_ratio=0.2,
            urban_ratio=0.15,
            repeated_segment_ratio=0.0,
        )
        faster, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=320.0, system_weight_kg=83.0),
            paved_ratio=0.95,
            unpaved_ratio=0.05,
            busy_road_ratio=0.2,
            urban_ratio=0.15,
            repeated_segment_ratio=0.0,
        )

        self.assertGreater(slower, faster)
        self.assertGreater(slower - faster, 10.0)

    def test_higher_weight_slows_hilly_route(self) -> None:
        geometry = build_geometry(total_distance_km=50, uphill_gain_per_km_m=24.0)
        candidate = build_candidate(
            distance_km=50.0,
            elevation_m=600.0,
            provider_duration_min=150.0,
            geometry=geometry,
        )

        lighter, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=260.0, system_weight_kg=75.0),
            paved_ratio=0.96,
            unpaved_ratio=0.04,
            busy_road_ratio=0.2,
            urban_ratio=0.1,
            repeated_segment_ratio=0.0,
        )
        heavier, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=260.0, system_weight_kg=95.0),
            paved_ratio=0.96,
            unpaved_ratio=0.04,
            busy_road_ratio=0.2,
            urban_ratio=0.1,
            repeated_segment_ratio=0.0,
        )

        self.assertGreater(heavier, lighter)
        self.assertGreater(heavier - lighter, 5.0)

    def test_urban_and_unpaved_context_adds_time(self) -> None:
        geometry = build_geometry(total_distance_km=40, uphill_gain_per_km_m=5.0)
        candidate = build_candidate(
            distance_km=40.0,
            elevation_m=100.0,
            provider_duration_min=100.0,
            geometry=geometry,
        )

        smooth, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=250.0, system_weight_kg=83.0),
            paved_ratio=0.98,
            unpaved_ratio=0.02,
            busy_road_ratio=0.1,
            urban_ratio=0.05,
            repeated_segment_ratio=0.0,
        )
        rough, _ = estimate_ride_duration(
            candidate,
            build_request(ftp_watts=250.0, system_weight_kg=83.0),
            paved_ratio=0.55,
            unpaved_ratio=0.45,
            busy_road_ratio=0.6,
            urban_ratio=0.7,
            repeated_segment_ratio=0.2,
        )

        self.assertGreater(rough, smooth)
        self.assertGreater(rough - smooth, 10.0)

    def test_enrichment_writes_duration_breakdown_to_metadata(self) -> None:
        candidate = build_candidate(
            distance_km=45.0,
            elevation_m=450.0,
            provider_duration_min=120.0,
            geometry=build_geometry(total_distance_km=45, uphill_gain_per_km_m=20.0),
            surface_summary=[
                {"value": 2, "amount": 0.92},
                {"value": 9, "amount": 0.08},
            ],
            waytype_summary=[
                {"value": 1, "amount": 0.2},
                {"value": 3, "amount": 0.3},
                {"value": 6, "amount": 0.25},
                {"value": 8, "amount": 0.25},
            ],
        )

        enriched = enrich_route(
            candidate,
            build_request(ftp_watts=255.0, system_weight_kg=84.0),
        )

        self.assertEqual(enriched.candidate.metadata["provider_duration_min"], 120.0)
        self.assertEqual(
            enriched.candidate.metadata["duration_estimate"]["source"],
            "ftp_physics_v1",
        )
        self.assertNotEqual(enriched.candidate.estimated_duration_min, 120.0)


if __name__ == "__main__":
    unittest.main()
