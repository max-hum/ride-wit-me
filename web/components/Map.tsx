"use client";

import { MapContainer, TileLayer, Polyline } from "react-leaflet";

type Props = {
  routes: {
    geometry: {
      lat: number;
      lng: number;
    }[];
  }[];
  selectedRouteIndex?: number;
};

export default function Map({ routes, selectedRouteIndex = 0 }: Props) {
  if (!routes.length) return null;

  const activeRoute = routes[selectedRouteIndex] ?? routes[0];
  const center = activeRoute.geometry[0];

  return (
    <div className="mt-8 h-[400px] w-full overflow-hidden rounded-2xl border">
      <MapContainer center={center} zoom={11} className="h-full w-full">
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {routes.map((route, idx) => (
          <Polyline
            key={idx}
            positions={route.geometry}
            pathOptions={{
              color: idx === selectedRouteIndex ? "#dc2626" : "#7dd3fc",
              weight: idx === selectedRouteIndex ? 6 : 4,
              opacity: idx === selectedRouteIndex ? 0.95 : 0.55,
            }}
          />
        ))}
      </MapContainer>
    </div>
  );
}
