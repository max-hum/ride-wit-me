from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Optional, Tuple

from domain.models import CandidateRoute, RideRequest


AIR_DENSITY_KG_PER_M3 = 1.226
ROAD_BIKE_CDA_M2 = 0.32
DRIVETRAIN_EFFICIENCY = 0.975
BASE_CRR = 0.0042
UNPAVED_CRR_BONUS = 0.0065
MIN_SPEED_MPS = 2.2
MAX_SPEED_MPS = 16.7


def estimate_ride_duration(
    candidate: CandidateRoute,
    request: RideRequest,
    *,
    paved_ratio: float,
    unpaved_ratio: float,
    busy_road_ratio: float,
    urban_ratio: float,
    repeated_segment_ratio: float,
) -> Tuple[float, Dict[str, Any]]:
    if len(candidate.geometry) < 2 or candidate.distance_km <= 0:
        return candidate.estimated_duration_min, {
            "source": "provider_fallback",
            "reason": "insufficient_geometry",
        }

    provider_duration_min = _read_provider_duration(candidate)
    route_crr = BASE_CRR + UNPAVED_CRR_BONUS * unpaved_ratio
    duration_guess_min = provider_duration_min or candidate.distance_km / 25.0 * 60.0

    target_power_watts = request.ftp_watts * _ftp_fraction_for_duration(duration_guess_min)
    moving_time_sec = 0.0

    for _ in range(3):
        target_power_watts = request.ftp_watts * _ftp_fraction_for_duration(
            duration_guess_min
        )
        moving_time_sec = _estimate_moving_time_sec(
            geometry=candidate.geometry,
            target_power_watts=target_power_watts,
            system_weight_kg=request.system_weight_kg,
            crr=route_crr,
        )
        duration_guess_min = moving_time_sec / 60.0 * _context_multiplier(
            urban_ratio=urban_ratio,
            busy_road_ratio=busy_road_ratio,
            repeated_segment_ratio=repeated_segment_ratio,
            paved_ratio=paved_ratio,
            unpaved_ratio=unpaved_ratio,
        )

    final_duration_min = round(duration_guess_min)

    return final_duration_min, {
        "source": "ftp_physics_v1",
        "provider_duration_min": provider_duration_min,
        "target_power_watts": round(target_power_watts, 1),
        "ftp_fraction": round(_ftp_fraction_for_duration(duration_guess_min), 3),
        "system_weight_kg": request.system_weight_kg,
        "route_crr": round(route_crr, 5),
        "moving_time_min": round(moving_time_sec / 60.0, 1),
        "context_multiplier": round(
            _context_multiplier(
                urban_ratio=urban_ratio,
                busy_road_ratio=busy_road_ratio,
                repeated_segment_ratio=repeated_segment_ratio,
                paved_ratio=paved_ratio,
                unpaved_ratio=unpaved_ratio,
            ),
            3,
        ),
    }


def _estimate_moving_time_sec(
    *,
    geometry: Iterable[Tuple[float, float, float]],
    target_power_watts: float,
    system_weight_kg: float,
    crr: float,
) -> float:
    moving_time_sec = 0.0
    points = list(geometry)

    for idx in range(1, len(points)):
        lat1, lng1, ele1 = points[idx - 1]
        lat2, lng2, ele2 = points[idx]

        segment_length_m = _haversine_m(lat1, lng1, lat2, lng2)
        if segment_length_m <= 0:
            continue

        raw_grade = (ele2 - ele1) / segment_length_m
        grade = _clamp(raw_grade, -0.12, 0.12)
        speed_mps = _solve_speed_mps(
            target_power_watts=target_power_watts,
            system_weight_kg=system_weight_kg,
            crr=crr,
            grade=grade,
        )
        moving_time_sec += segment_length_m / speed_mps

    return moving_time_sec


def _solve_speed_mps(
    *,
    target_power_watts: float,
    system_weight_kg: float,
    crr: float,
    grade: float,
) -> float:
    low = MIN_SPEED_MPS
    high = MAX_SPEED_MPS if grade >= -0.03 else 14.0

    if _required_power_watts(high, system_weight_kg, crr, grade) <= target_power_watts:
        return high

    if _required_power_watts(low, system_weight_kg, crr, grade) >= target_power_watts:
        return low

    for _ in range(28):
        mid = (low + high) / 2.0
        if _required_power_watts(mid, system_weight_kg, crr, grade) > target_power_watts:
            high = mid
        else:
            low = mid

    return (low + high) / 2.0


def _required_power_watts(
    speed_mps: float,
    system_weight_kg: float,
    crr: float,
    grade: float,
) -> float:
    aero_power = 0.5 * AIR_DENSITY_KG_PER_M3 * ROAD_BIKE_CDA_M2 * speed_mps ** 3
    rolling_power = system_weight_kg * 9.81 * crr * speed_mps
    gravity_power = system_weight_kg * 9.81 * grade * speed_mps
    wheel_power = aero_power + rolling_power + gravity_power
    return max(0.0, wheel_power / DRIVETRAIN_EFFICIENCY)


def _ftp_fraction_for_duration(duration_min: float) -> float:
    if duration_min <= 90:
        return 0.83
    if duration_min <= 180:
        return 0.78
    if duration_min <= 300:
        return 0.73
    return 0.68


def _context_multiplier(
    *,
    urban_ratio: float,
    busy_road_ratio: float,
    repeated_segment_ratio: float,
    paved_ratio: float,
    unpaved_ratio: float,
) -> float:
    multiplier = 1.0
    multiplier += 0.08 * urban_ratio
    multiplier += 0.05 * busy_road_ratio
    multiplier += 0.03 * repeated_segment_ratio
    multiplier += 0.04 * unpaved_ratio
    multiplier += 0.02 * max(0.0, 0.85 - paved_ratio)
    return multiplier


def _read_provider_duration(candidate: CandidateRoute) -> Optional[float]:
    metadata = candidate.metadata or {}
    value = metadata.get("provider_duration_min")
    if value is None:
        summary = metadata.get("summary", {})
        raw_duration_seconds = summary.get("duration")
        if raw_duration_seconds is None:
            return None
        value = raw_duration_seconds / 60.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_m * c


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
