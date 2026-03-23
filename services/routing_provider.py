from __future__ import annotations

from datetime import datetime

import math
import uuid
from typing import List, Tuple

import requests

from app.config import OPENROUTESERVICE_API_KEY
from domain.models import CandidateRoute, RideRequest


class RoutingProviderError(Exception):
    pass


class OpenRouteServiceProvider:
    BASE_URL = "https://api.openrouteservice.org/v2/directions/cycling-road"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or OPENROUTESERVICE_API_KEY
        if not self.api_key:
            raise RoutingProviderError(
                "Missing OPENROUTESERVICE_API_KEY. Add it to your .env file."
            )

    def generate_candidate_routes(self, request: RideRequest) -> List[CandidateRoute]:
        start_lat = request.start_point.lat
        start_lng = request.start_point.lng

        base_radius_km = max(8.0, request.distance_km / 4.2)
        routes: List[CandidateRoute] = []

        candidate_coordinate_sets: List[List[List[float]]] = []

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
            wp2 = self._offset_point(start_lat, start_lng, r * 1.05, (bearing + 55) % 360)
            wp3 = self._offset_point(start_lat, start_lng, r * 0.95, (bearing + 110) % 360)

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

        for idx, coords in enumerate(candidate_coordinate_sets):
            try:
                route = self._request_route(coords, route_index=idx)
                routes.append(route)
            except Exception:
                continue

        if not routes:
            raise RoutingProviderError("No candidate routes were generated.")

        return routes
    

    def _request_route(
        self,
        coordinates: List[List[float]],
        route_index: int,
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

        latlng_geometry = [
            (pt[1], pt[0], float(pt[2]) if len(pt) >= 3 else 0.0)
            for pt in geometry
        ]        
        elevation_gain = props.get("ascent", 0.0)

        timestamp = datetime.now().strftime("%H%M%S")

        return CandidateRoute(
            route_id=f"ors-{timestamp}-{route_index:02d}-{uuid.uuid4().hex[:6]}",
            provider="openrouteservice",
            geometry=latlng_geometry,
            distance_km=round(summary["distance"] / 1000.0, 2),
            elevation_m=round(elevation_gain, 0),
            estimated_duration_min=round(summary["duration"] / 60.0, 1),
            metadata=props,
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
