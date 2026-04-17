from __future__ import annotations

import argparse

from app.config import DEBUG_RUNS_DIR, OUTPUT_DIR
from services.debug_export import dump_debug_run
from domain.models import RideRequest, StartPoint
#from services.candidate_generator import CandidateGenerator
#from services.enrichment import enrich_route
from services.exporter import export_gpx
#from services.ranking import rank_routes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and rank road cycling routes.")
    parser.add_argument("--start-lat", type=float, required=True)
    parser.add_argument("--start-lng", type=float, required=True)
    parser.add_argument("--distance", type=float, required=True, help="Target distance in km")
    parser.add_argument("--elevation", type=float, required=True, help="Target elevation in m")
    parser.add_argument("--ftp", type=float, required=True, help="FTP in watts")
    parser.add_argument(
        "--system-weight",
        type=float,
        required=True,
        help="Total rider plus bike weight in kg",
    )
    parser.add_argument("--ride-style", type=str, default="endurance")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    request = RideRequest(
        start_point=StartPoint(
            lat=args.start_lat,
            lng=args.start_lng,
        ),
        distance_km=args.distance,
        elevation_m=args.elevation,
        ftp_watts=args.ftp,
        system_weight_kg=args.system_weight,
        ride_style=args.ride_style,
    )

    from services.route_service import generate_routes
    ranked_routes = generate_routes(request)


#    print("\nGenerating candidate routes...")
#    generator = CandidateGenerator()
#    candidates = generator.generate(request)
#    print(f"Generated {len(candidates)} candidate route(s).")

#    print("\nEnriching routes...")
#    enriched_routes = [enrich_route(route) for route in candidates]

#    print("\nRanking routes...")
#    ranked_routes = rank_routes(enriched_routes, request)

    debug_json_path = dump_debug_run(request, ranked_routes, DEBUG_RUNS_DIR)

    if args.debug:
        print("\nAll ranked routes:\n")
        for idx, scored_route in enumerate(ranked_routes, start=1):
            candidate = scored_route.enriched.candidate
            fit = scored_route.fit
            enriched = scored_route.enriched

            print(f"#{idx} | {candidate.route_id}")
            print(f"  Distance:              {candidate.distance_km} km")
            print(f"  Elevation:             {candidate.elevation_m} m")
            print(f"  Est. duration:         {candidate.estimated_duration_min} min")
            print(f"  Overall fit:           {fit.overall_fit_score}")
            print(f"  Distance fit:          {fit.distance_fit_score}")
            print(f"  Elevation fit:         {fit.elevation_fit_score}")
            print(f"  Road quality:          {fit.road_quality_score}")
            print(f"  Ride feel:             {fit.ride_feel_score}")
            print(f"  Scenic:                {fit.scenic_score}")
            print(f"  Climbing:              {fit.climbing_score}")
            print(f"  Novelty:               {fit.novelty_score}")
            print(f"  Busy road penalty:     {fit.busy_road_penalty}")
            print(f"  Urban penalty:         {fit.urban_penalty}")
            print(f"  Unpaved penalty:       {fit.unpaved_penalty}")
            print(f"  Repeat penalty:        {fit.repeat_penalty}")
            print(f"  Longest repeated blk:  {enriched.longest_repeated_block_km} km")
            print(f"  Branch penalty:        {fit.branch_penalty}")
            print(f"  Urban ratio:           {enriched.urban_ratio}")
            print(f"  Busy road ratio:       {enriched.busy_road_ratio}")
            print(f"  Unpaved ratio:         {enriched.unpaved_ratio}")
            print(f"  Repeated seg ratio:    {enriched.repeated_segment_ratio}")
            print(f"  Minor road ratio:      {enriched.minor_road_ratio}")
            print(f"  Paved ratio:           {enriched.paved_ratio}")
            print(f"  Why:                   {scored_route.reason_summary}")
            print("")

    print("\nTop 3 routes:\n")
    for idx, scored_route in enumerate(ranked_routes[:3], start=1):
        candidate = scored_route.enriched.candidate
        fit = scored_route.fit

        print(f"#{idx} | {candidate.route_id}")
        print(f"  Overall fit:      {fit.overall_fit_score}")
        print(f"  Distance:         {candidate.distance_km} km")
        print(f"  Elevation:        {candidate.elevation_m} m")
        print(f"  Est. duration:    {candidate.estimated_duration_min} min")
        print(f"  Distance fit:     {fit.distance_fit_score}")
        print(f"  Elevation fit:    {fit.elevation_fit_score}")
        print(f"  Road quality:     {fit.road_quality_score}")
        print(f"  Ride feel:        {fit.ride_feel_score}")
        print(f"  Scenic:           {fit.scenic_score}")
        print(f"  Climbing:         {fit.climbing_score}")
        print(f"  Novelty:          {fit.novelty_score}")
        print(f"  Why:              {scored_route.reason_summary}")
        print("")

    exported_paths = []

    for scored_route in ranked_routes[:3]:
        gpx_path = export_gpx(scored_route.enriched.candidate, OUTPUT_DIR)
        exported_paths.append(gpx_path)

    print("Top 3 GPX files exported:")
    for path in exported_paths:
        print(f"  - {path}")

    print(f"Debug run JSON exported to: {debug_json_path}")
    
    print("\nDone.")


if __name__ == "__main__":
    main()
