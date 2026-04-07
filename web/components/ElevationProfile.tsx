"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = {
  lat: number;
  lng: number;
  ele: number;
};

type Props = {
  geometry: Point[];
};

function haversineKm(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const R = 6371;

  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLng / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function buildProfileData(geometry: Point[]) {
  if (!geometry.length) return [];

  let cumulativeKm = 0;

  return geometry.map((point, index) => {
    if (index > 0) {
      const prev = geometry[index - 1];
      cumulativeKm += haversineKm(prev.lat, prev.lng, point.lat, point.lng);
    }

    return {
      distanceKm: Number(cumulativeKm.toFixed(2)),
      elevationM: Math.round(point.ele),
    };
  });
}

export default function ElevationProfile({ geometry }: Props) {
  const data = buildProfileData(geometry);

  if (!data.length) return null;

  const minElevation = Math.min(...data.map((d) => d.elevationM));
  const maxElevation = Math.max(...data.map((d) => d.elevationM));

  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3">
        <h3 className="text-lg font-semibold">Elevation profile</h3>
        <p className="text-sm text-slate-500">
          {data[data.length - 1]?.distanceKm ?? 0} km · {minElevation}–{maxElevation} m
        </p>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="distanceKm"
              tickFormatter={(value) => `${value} km`}
            />
            <YAxis
              domain={["dataMin - 20", "dataMax + 20"]}
              tickFormatter={(value) => `${value} m`}
            />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === "elevationM") return [`${value} m`, "Elevation"];
                return [value, name];
              }}
              labelFormatter={(label) => `${label} km`}
            />
            <Area
              type="monotone"
              dataKey="elevationM"
              strokeWidth={2}
              fillOpacity={0.25}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}