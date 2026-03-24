"use client";

import { MapContainer, TileLayer, Polyline } from "react-leaflet";

type Props = {
  routes: {
    geometry: [number, number][];
  }[];
};

export default function Map({ routes }: Props) {
  if (!routes.length) return null;

  const center = routes[0].geometry[0];

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
              weight: 4,
              opacity: 0.7,
            }}
          />
        ))}
      </MapContainer>
    </div>
  );
}