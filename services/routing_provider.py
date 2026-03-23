from __future__ import annotations

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
        """
        v0 candidate generation strategy:
        - generate loop-like routes using waypoint anchors around the start point
        - vary bearings and waypoint distances to create diversity
        - ask ORS for a full route that returns to start
        """
        start_lat = request.start_point.lat
        start_lng = request.start_point.lng

        bearings = [0, 45, 90, 135, 180, 225, 270, 315]
        distance_factors = [0.85, 1.0, 1.1, 0.95, 1.05, 0.9, 1.15, 0.8]

        base_radius_km = max(8.0, request.distance_km / 4.0)
        routes: List[CandidateRoute] = []

        for idx, bearing in enumerate(bearings):
            radius_factor = distance_factors[idx % len(distance_factors)]
            radius_km = base_radius_km * radius_factor

            wp1 = self._offset_point(start_lat, start_lng, radius_km, bearing)
            wp2 = self._offset_point(
                start_lat,
                start_lng,
                radius_km * 0.9,
                (bearing + 70) % 360,
            )

            coords = [
                [start_lng, start_lat],
                [wp1[1], wp1[0]],
                [wp2[1], wp2[0]],
                [start_lng, start_lat],
            ]

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

        latlng_geometry = [(pt[1], pt[0]) for pt in geometry]
        elevation_gain = self._estimate_elevation_gain(geometry)

        return CandidateRoute(
            route_id=f"ors-{route_index}-{uuid.uuid4().hex[:8]}",
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

    @staticmethod
    def _estimate_elevation_gain(geometry: List[List[float]]) -> float:
        """
        Estimate ascent from geometry elevation, while filtering out tiny
        point-to-point noise that would otherwise inflate total climbing.
        """
        gain = 0.0
        prev_ele = None
        min_rise_threshold_m = 3.0

        for pt in geometry:
            if len(pt) < 3:
                continue

            ele = float(pt[2])

            if prev_ele is not None:
                delta = ele - prev_ele
                if delta >= min_rise_threshold_m:
                    gain += delta

            prev_ele = ele

        return gain