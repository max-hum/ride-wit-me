"use client";

import { useEffect, useState } from "react";

import dynamic from "next/dynamic";

import ElevationProfile from "@/components/ElevationProfile";

const Map = dynamic(() => import("@/components/Map"), {
  ssr: false,
});

type RouteResponse = {
  route_id: string;
  provider: string;
  distance_km: number;
  elevation_m: number;
  estimated_duration_min: number;
  geometry: {
    lat: number;
    lng: number;
    ele: number;
  }[];
  fit: {
    overall_fit_score: number;
    distance_fit_score: number;
    elevation_fit_score: number;
    road_quality_score: number;
    ride_feel_score: number;
    scenic_score: number;
    climbing_score: number;
    novelty_score: number;
    busy_road_penalty: number;
    urban_penalty: number;
    unpaved_penalty: number;
    repeat_penalty: number;
    elevation_overshoot_penalty?: number;
    branch_penalty?: number;
  };
  reason_summary: string;
  enriched: {
    repeated_segment_ratio: number;
    longest_repeated_block_km: number;
    urban_ratio: number;
    unpaved_ratio: number;
    busy_road_ratio: number;
  };
};

type ApiResponse = {
  routes: RouteResponse[];
};

type GeocodeSearchResponse = {
  results: {
    label: string;
    lat: number;
    lng: number;
  }[];
};

type StoredRideFormState = {
  orsApiKey: string;
  addressQuery: string;
  startLat: string;
  startLng: string;
  distanceKm: string;
  elevationM: string;
  rideStyle: string;
};

const RIDE_FORM_STORAGE_KEY = "ride-wit-me:ride-form";

function parseRequiredNumber(value: string, label: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${label} is required.`);
  }

  const parsed = Number(trimmed);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${label} must be a valid number.`);
  }

  return parsed;
}

function readStoredRideFormState(): StoredRideFormState | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(RIDE_FORM_STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<StoredRideFormState>;
    return {
      orsApiKey: parsed.orsApiKey ?? "",
      addressQuery: parsed.addressQuery ?? "",
      startLat: parsed.startLat ?? "",
      startLng: parsed.startLng ?? "",
      distanceKm: parsed.distanceKm ?? "65",
      elevationM: parsed.elevationM ?? "700",
      rideStyle: parsed.rideStyle ?? "endurance",
    };
  } catch {
    return null;
  }
}

function writeStoredRideFormState(state: StoredRideFormState) {
  if (typeof window === "undefined") return;

  try {
    window.localStorage.setItem(RIDE_FORM_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Ignore storage failures and keep the form usable.
  }
}

function downloadRouteAsGpx(route: RouteResponse) {
  const gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Ride Wit Me" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${route.route_id}</name>
    <trkseg>
${route.geometry
  .map(
    (pt) =>
      `      <trkpt lat="${pt.lat}" lon="${pt.lng}"><ele>${pt.ele}</ele></trkpt>`
  )
  .join("\n")}
    </trkseg>
  </trk>
</gpx>`;

  const blob = new Blob([gpx], { type: "application/gpx+xml" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `${route.route_id}.gpx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
}

export default function Home() {
  const [orsApiKey, setOrsApiKey] = useState("");
  const [addressQuery, setAddressQuery] = useState("");
  const [startLat, setStartLat] = useState("");
  const [startLng, setStartLng] = useState("");
  const [distanceKm, setDistanceKm] = useState("65");
  const [elevationM, setElevationM] = useState("700");
  const [rideStyle, setRideStyle] = useState("endurance");
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationMessage, setLocationMessage] = useState("");
  const [locationError, setLocationError] = useState("");

  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);

  const [routes, setRoutes] = useState<RouteResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const topRoutes = routes.slice(0, 3);
  const selectedRoute = topRoutes[selectedRouteIndex] ?? topRoutes[0];

  useEffect(() => {
    const savedState = readStoredRideFormState();
    if (!savedState) return;

    setAddressQuery(savedState.addressQuery);
    setOrsApiKey(savedState.orsApiKey);
    setStartLat(savedState.startLat);
    setStartLng(savedState.startLng);
    setDistanceKm(savedState.distanceKm);
    setElevationM(savedState.elevationM);
    setRideStyle(savedState.rideStyle);
  }, []);

  async function handleResolveAddress() {
    const trimmedAddress = addressQuery.trim();
    if (!trimmedAddress) {
      setLocationError("Enter an address or place to resolve.");
      setLocationMessage("");
      return;
    }

    setLocationLoading(true);
    setLocationError("");
    setLocationMessage("");

    try {
      const headers: HeadersInit = {};
      if (orsApiKey.trim()) {
        headers["X-ORS-API-Key"] = orsApiKey.trim();
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/geocode/search?text=${encodeURIComponent(
          trimmedAddress
        )}`,
        {
          headers,
        }
      );

      if (!response.ok) {
        throw new Error(`Geocoding error: ${response.status}`);
      }

      const data: GeocodeSearchResponse = await response.json();
      const topResult = data.results[0];

      if (!topResult) {
        setLocationError("No matching address found.");
        return;
      }

      const resolvedLat = String(topResult.lat);
      const resolvedLng = String(topResult.lng);

      setAddressQuery(topResult.label);
      setStartLat(resolvedLat);
      setStartLng(resolvedLng);
      setLocationMessage("Address resolved and coordinates updated.");
      writeStoredRideFormState({
        orsApiKey,
        addressQuery: topResult.label,
        startLat: resolvedLat,
        startLng: resolvedLng,
        distanceKm,
        elevationM,
        rideStyle,
      });
    } catch (err) {
      setLocationError(err instanceof Error ? err.message : "Failed to resolve address.");
    } finally {
      setLocationLoading(false);
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setRoutes([]);

    try {
      const parsedLat = parseRequiredNumber(startLat, "Start latitude");
      const parsedLng = parseRequiredNumber(startLng, "Start longitude");
      const parsedDistanceKm = parseRequiredNumber(distanceKm, "Distance");
      const parsedElevationM = parseRequiredNumber(elevationM, "Elevation");

      writeStoredRideFormState({
        orsApiKey,
        addressQuery: addressQuery.trim(),
        startLat: String(parsedLat),
        startLng: String(parsedLng),
        distanceKm,
        elevationM,
        rideStyle,
      });

      const headers: HeadersInit = {
        "Content-Type": "application/json",
      };
      if (orsApiKey.trim()) {
        headers["X-ORS-API-Key"] = orsApiKey.trim();
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/generate-route`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            start_point: {
              lat: parsedLat,
              lng: parsedLng,
            },
            distance_km: parsedDistanceKm,
            elevation_m: parsedElevationM,
            ride_style: rideStyle,
            avoid: {
              busy_roads: true,
              urban: true,
              unpaved: true,
              repeated_segments: true,
            },
            prefer: {
              scenic: true,
              rolling_roads: true,
              novelty: false,
            },
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data: ApiResponse = await response.json();
      setRoutes(data.routes);
      setSelectedRouteIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-3xl font-bold">Ride Wit Me</h1>
        <p className="mt-2 text-slate-600">
          Generate road cycling loops from your backend engine.
        </p>

        <form
          onSubmit={handleGenerate}
          className="mt-8 rounded-2xl bg-white p-6 shadow-sm border border-slate-200"
        >
          <div className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <label className="mb-1 block text-sm font-medium">OpenRouteService API key</label>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              type="password"
              placeholder="Optional: leave blank to use the server default key"
              value={orsApiKey}
              onChange={(e) => setOrsApiKey(e.target.value)}
            />
            <p className="mt-2 text-sm text-slate-600">
              The latest used key is restored locally in this browser. If left blank, the
              backend falls back to its configured server key.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex flex-col gap-2 lg:flex-row lg:items-end">
              <div className="flex-1">
                <label className="mb-1 block text-sm font-medium">Address or place</label>
                <input
                  className="w-full rounded-xl border border-slate-300 px-3 py-2"
                  placeholder="City, street, or place"
                  value={addressQuery}
                  onChange={(e) => {
                    setAddressQuery(e.target.value);
                    setLocationError("");
                    setLocationMessage("");
                  }}
                />
              </div>

              <button
                type="button"
                onClick={handleResolveAddress}
                disabled={locationLoading}
                className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-50"
              >
                {locationLoading ? "Resolving..." : "Resolve address"}
              </button>
            </div>

            <p className="mt-3 text-sm text-slate-600">
              Use either address lookup or direct coordinates. Route generation always uses
              the latitude and longitude fields below.
            </p>

            {locationMessage && (
              <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                {locationMessage}
              </div>
            )}

            {locationError && (
              <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {locationError}
              </div>
            )}
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            <div>
              <label className="mb-1 block text-sm font-medium">Start lat</label>
              <input
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
                placeholder="e.g. 49.3597"
                value={startLat}
                onChange={(e) => setStartLat(e.target.value)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Start lng</label>
              <input
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
                placeholder="e.g. 6.1685"
                value={startLng}
                onChange={(e) => setStartLng(e.target.value)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Distance (km)</label>
              <input
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
                value={distanceKm}
                onChange={(e) => setDistanceKm(e.target.value)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Elevation (m)</label>
              <input
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
                value={elevationM}
                onChange={(e) => setElevationM(e.target.value)}
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Ride style</label>
              <select
                className="w-full rounded-xl border border-slate-300 px-3 py-2"
                value={rideStyle}
                onChange={(e) => setRideStyle(e.target.value)}
              >
                <option value="endurance">endurance</option>
                <option value="hilly">hilly</option>
                <option value="scenic">scenic</option>
                <option value="exploration">exploration</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 rounded-2xl bg-slate-900 px-5 py-3 text-white disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate routes"}
          </button>
        </form>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-4">
          {topRoutes.map((route, index) => (
            <div
              key={route.route_id}
              onClick={() => setSelectedRouteIndex(index)}
              className={`cursor-pointer rounded-2xl bg-white p-6 shadow-sm border ${
                selectedRouteIndex === index
                  ? "border-slate-900 ring-2 ring-slate-200"
                  : "border-slate-200"
              }`}
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">Route #{index + 1}</h2>
                  <p className="text-sm text-slate-500">{route.route_id}</p>
                </div>
                <div className="rounded-xl bg-slate-100 px-3 py-2 text-sm font-medium">
                  Fit: {route.fit.overall_fit_score}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                <Metric label="Distance" value={`${route.distance_km} km`} />
                <Metric label="Elevation" value={`${route.elevation_m} m`} />
                <Metric label="Duration" value={`${route.estimated_duration_min} min`} />
                <Metric label="Longest repeat" value={`${route.enriched.longest_repeated_block_km} km`} />
              </div>

              <div className="mt-4 text-sm text-slate-700">
                <span className="font-medium">Why:</span> {route.reason_summary}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4 text-sm text-slate-600">
                <Metric label="Distance fit" value={String(route.fit.distance_fit_score)} />
                <Metric label="Elevation fit" value={String(route.fit.elevation_fit_score)} />
                <Metric label="Repeat penalty" value={String(route.fit.repeat_penalty)} />
                <Metric label="Branch penalty" value={String(route.fit.branch_penalty ?? 0)} />
              </div>

              <button
                type="button"
                onClick={() => downloadRouteAsGpx(route)}
                className="text-sm underline"
              >
                Download GPX
              </button>
            </div>
          ))}
        </div>

        {topRoutes.length > 0 && (
          <>
            <Map routes={topRoutes} selectedRouteIndex={selectedRouteIndex} />

            {selectedRoute && (
              <ElevationProfile geometry={selectedRoute.geometry} />
            )}
          </>
        )}
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 font-medium">{value}</div>
    </div>
  );
}
