# Ride Wit Me Web

This is the Next.js frontend for Ride Wit Me. It sends route-generation requests to the Python backend, renders returned routes on a Leaflet map, and lets the user download routes as GPX files directly from the browser.

## Responsibilities

- Collect ride inputs from the user
- Allow riders to provide their own OpenRouteService API key
- Resolve a start address or place into coordinates when needed
- Call the backend `POST /generate-route` endpoint
- Show top-ranked route summaries
- Plot the top 3 route geometries on a shared interactive map
- Highlight the selected route while keeping the alternatives visible
- Show an elevation profile for the selected route
- Export a selected route to GPX client-side

## Requirements

- Node.js 20+ recommended
- npm

## Setup

Install dependencies:

```bash
npm install
```

Create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

An example file is available at [web/.env.local.example](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/.env.local.example).

## Run

```bash
npm run dev
```

Open:

- `http://127.0.0.1:3000`

## Scripts

- `npm run dev`: start the development server
- `npm run build`: create a production build
- `npm run start`: run the production server
- `npm run lint`: run ESLint

## Important Files

- [web/app/page.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/page.tsx)
- [web/components/Map.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/components/Map.tsx)
- [web/components/ElevationProfile.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/components/ElevationProfile.tsx)
- [web/app/layout.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/layout.tsx)
- [web/app/globals.css](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/globals.css)

## Request Shape Sent By The UI

The frontend currently sends:

- `start_point`
- `distance_km`
- `elevation_m`
- `ride_style`
- hardcoded `avoid` preferences
- hardcoded `prefer` preferences

The UI does not yet expose the preference toggles individually.

The start location UI supports both:

- address or place lookup through the backend geocoding endpoint
- direct latitude and longitude entry

The API key UI supports both:

- a user-provided OpenRouteService key stored locally in the browser
- fallback to the backend's configured default key when left blank

## Notes

- The map uses `react-leaflet` and is loaded client-side only.
- The latest used OpenRouteService key is restored from browser local storage.
- The start-location form keeps address lookup and direct coordinates visible at the same time.
- The latest used location is restored from browser local storage; first-time visits start blank.
- The UI shows up to 3 route cards; clicking a card updates one shared map and elevation profile below the list.
- On the map, non-selected routes are light blue and the selected route is red.
- GPX download is generated in-browser from returned geometry rather than fetched from the backend.
- The backend must be running and reachable at `NEXT_PUBLIC_API_BASE_URL`.
