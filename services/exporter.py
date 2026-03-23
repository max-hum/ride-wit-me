from __future__ import annotations

from pathlib import Path

import gpxpy
import gpxpy.gpx

from domain.models import CandidateRoute


def export_gpx(route: CandidateRoute, output_dir: Path) -> Path:
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    for lat, lng, ele in route.geometry:
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=lat,
                longitude=lng,
                elevation=ele,
            )
        )

    file_path = output_dir / f"{route.route_id}.gpx"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())

    return file_path