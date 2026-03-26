# Ride Wit Me Web

This is the Next.js frontend for Ride Wit Me. It sends route-generation requests to the Python backend, renders returned routes on a Leaflet map, and lets the user download routes as GPX files directly from the browser.

## Responsibilities

- Collect ride inputs from the user
- Call the backend `POST /generate-route` endpoint
- Show top-ranked route summaries
- Plot route geometry on an interactive map
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

## Notes

- The map uses `react-leaflet` and is loaded client-side only.
- GPX download is generated in-browser from returned geometry rather than fetched from the backend.
- The backend must be running and reachable at `NEXT_PUBLIC_API_BASE_URL`.
