from __future__ import annotations

from datetime import datetime

import math
import uuid
from typing import List, Optional, Tuple

import requests

from app.config import OPENROUTESERVICE_API_KEY
from domain.models import CandidateRoute, GeocodeResult, RideRequest


class RoutingProviderError(Exception):
    pass


class OpenRouteServiceProvider:
    BASE_URL = "https://api.openrouteservice.org/v2/directions/cycling-road"
    GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or OPENROUTESERVICE_API_KEY
        if not self.api_key:
            raise RoutingProviderError(
                "Missing OPENROUTESERVICE_API_KEY. Add it to your .env file."
            )

    def generate_candidate_routes(
        self,
        request: RideRequest,
        strategy: str = "baseline",
    ) -> List[CandidateRoute]:
        start_lat = request.start_point.lat
        start_lng = request.start_point.lng

        base_radius_km = max(8.0, request.distance_km / 4.2)
        routes: List[CandidateRoute] = []

        candidate_coordinate_sets = self._build_candidate_coordinate_sets(
            start_lat=start_lat,
            start_lng=start_lng,
            base_radius_km=base_radius_km,
            strategy=strategy,
        )

        for idx, coords in enumerate(candidate_coordinate_sets):
            try:
                route = self._request_route(
                    coords,
                    route_index=idx,
                    strategy=strategy,
                )
                routes.append(route)
            except Exception:
                continue

        if not routes:
            raise RoutingProviderError("No candidate routes were generated.")

        return routes

    def geocode_search(self, text: str, size: int = 5) -> List[GeocodeResult]:
        query = text.strip()
        if not query:
            return []

        response = requests.get(
            self.GEOCODE_URL,
            params={
                "api_key": self.api_key,
                "text": query,
                "size": size,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        results: List[GeocodeResult] = []
        for feature in data.get("features", []):
            coordinates = feature.get("geometry", {}).get("coordinates", [])
            if len(coordinates) < 2:
                continue

            label = (
                feature.get("properties", {}).get("label")
                or feature.get("properties", {}).get("name")
                or query
            )

            results.append(
                GeocodeResult(
                    label=label,
                    lat=float(coordinates[1]),
                    lng=float(coordinates[0]),
                )
            )

        return results

    def _build_candidate_coordinate_sets(
        self,
        start_lat: float,
        start_lng: float,
        base_radius_km: float,
        strategy: str,
    ) -> List[List[List[float]]]:
        candidate_coordinate_sets: List[List[List[float]]] = []

        if strategy == "baseline":
            # Family A: classic 2-anchor loops
            bearings_a = [0, 60, 120, 180, 240, 300]
            for bearing in bearings_a:
                r1 = base_radius_km * 1.00
                r2 = base_radius_km * 0.92

                wp1 = self._offset_point(start_lat, start_lng, r1, bearing)
                wp2 = self._offset_point(start_lat, start_lng, r2, (bearing + 75) % 360)

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            # Family B: rounder 3-anchor loops
            bearings_b = [30, 90, 150, 210, 270, 330]
            for bearing in bearings_b:
                r = base_radius_km * 0.95

                wp1 = self._offset_point(start_lat, start_lng, r, bearing)
                wp2 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 1.05,
                    (bearing + 55) % 360,
                )
                wp3 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 0.95,
                    (bearing + 110) % 360,
                )

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [wp3[1], wp3[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            # Family C: tighter loops to reduce overshoot
            bearings_c = [30, 90, 150, 210, 270, 330]
            for bearing in bearings_c:
                r1 = base_radius_km * 0.82
                r2 = base_radius_km * 0.75

                wp1 = self._offset_point(start_lat, start_lng, r1, bearing)
                wp2 = self._offset_point(start_lat, start_lng, r2, (bearing + 65) % 360)

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            return candidate_coordinate_sets

        if strategy == "expanded":
            # Family D: wider 3-anchor loops for more route variety
            bearings_d = [0, 45, 90, 135, 180, 225, 270, 315]
            for bearing in bearings_d:
                r = base_radius_km * 1.08

                wp1 = self._offset_point(start_lat, start_lng, r, bearing)
                wp2 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 0.88,
                    (bearing + 40) % 360,
                )
                wp3 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 1.02,
                    (bearing + 95) % 360,
                )

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [wp3[1], wp3[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            # Family E: compact 4-anchor loops that can land closer to targets
            bearings_e = [20, 80, 140, 200, 260, 320]
            for bearing in bearings_e:
                r = base_radius_km * 0.78

                wp1 = self._offset_point(start_lat, start_lng, r, bearing)
                wp2 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 0.92,
                    (bearing + 35) % 360,
                )
                wp3 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 0.98,
                    (bearing + 75) % 360,
                )
                wp4 = self._offset_point(
                    start_lat,
                    start_lng,
                    r * 0.85,
                    (bearing + 120) % 360,
                )

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [wp3[1], wp3[0]],
                    [wp4[1], wp4[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            # Family F: longer asymmetric loops to widen the pool when strict fits are scarce
            bearings_f = [15, 75, 135, 195, 255, 315]
            for bearing in bearings_f:
                r1 = base_radius_km * 1.15
                r2 = base_radius_km * 0.68

                wp1 = self._offset_point(start_lat, start_lng, r1, bearing)
                wp2 = self._offset_point(start_lat, start_lng, r2, (bearing + 85) % 360)

                coords = [
                    [start_lng, start_lat],
                    [wp1[1], wp1[0]],
                    [wp2[1], wp2[0]],
                    [start_lng, start_lat],
                ]
                candidate_coordinate_sets.append(coords)

            return candidate_coordinate_sets

        raise RoutingProviderError(f"Unknown generation strategy: {strategy}")

    def _request_route(
        self,
        coordinates: List[List[float]],
        route_index: int,
        strategy: str,
    ) -> CandidateRoute:
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        body = {
            "coordinates": coordinates,
            "instructions": False,
            "elevation": True,
            "extra_info": ["surface", "waytype"],
        }

        response = requests.post(
            self.BASE_URL + "/geojson",
            json=body,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        if not features:
            raise RoutingProviderError("Empty route response from provider.")

        feature = features[0]
        geometry = feature["geometry"]["coordinates"]
        props = feature["properties"]
        summary = props["summary"]
        provider_duration_min = round(summary["duration"] / 60.0, 1)

        latlng_geometry = [
            (pt[1], pt[0], float(pt[2]) if len(pt) >= 3 else 0.0)
            for pt in geometry
        ]
        elevation_gain = props.get("ascent", 0.0)
        metadata = {
            **props,
            "provider_duration_min": provider_duration_min,
            "provider_duration_source": "openrouteservice",
        }

        timestamp = datetime.now().strftime("%H%M%S")

        return CandidateRoute(
            route_id=(
                f"ors-{strategy[:3]}-{timestamp}-{route_index:02d}-{uuid.uuid4().hex[:6]}"
            ),
            provider="openrouteservice",
            geometry=latlng_geometry,
            distance_km=round(summary["distance"] / 1000.0, 2),
            elevation_m=round(elevation_gain, 0),
            estimated_duration_min=provider_duration_min,
            metadata=metadata,
        )

    @staticmethod
    def _offset_point(
        lat: float,
        lng: float,
        distance_km: float,
        bearing_deg: float,
    ) -> Tuple[float, float]:
        earth_radius_km = 6371.0
        bearing = math.radians(bearing_deg)

        lat1 = math.radians(lat)
        lon1 = math.radians(lng)
        angular_distance = distance_km / earth_radius_km

        lat2 = math.asin(
            math.sin(lat1) * math.cos(angular_distance)
            + math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )
        lon2 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
        )

        return (math.degrees(lat2), math.degrees(lon2))
