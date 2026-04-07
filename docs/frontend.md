# Frontend

## Overview

The frontend is a Next.js App Router application in [`web/`](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web). It is a thin client over the backend API and is responsible for:

- Collecting ride parameters
- Calling the backend
- Displaying the top route candidates
- Rendering route geometry on a map
- Downloading a selected route as GPX in the browser

## Stack

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- Leaflet
- React Leaflet

## Run Locally

```bash
cd web
npm install
npm run dev
```

Default local URL:

- `http://127.0.0.1:3000`

## Environment Variables

Create `web/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Without this variable, the frontend cannot call the backend route-generation endpoint.

## Key Files

- [web/app/page.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/page.tsx)
  - Main page
  - Form state
  - Backend fetch call
  - Error/loading state
  - Route cards
  - Selected-route state
  - Shared map and elevation-profile rendering
  - Client-side GPX generation
- [web/components/Map.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/components/Map.tsx)
  - Leaflet map
  - Polyline rendering for returned routes
  - Selected-route highlight styling
- [web/components/ElevationProfile.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/components/ElevationProfile.tsx)
  - Elevation chart for the active route
- [web/app/layout.tsx](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/layout.tsx)
  - Global layout
  - Font setup
  - Leaflet CSS import
- [web/app/globals.css](/Users/maximehumbert/Documents/GitHub/ride-wit-me/web/app/globals.css)
  - Global theme variables
  - Tailwind import

## Current UI Behavior

The main page exposes these request controls:

- Start latitude
- Start longitude
- Distance in kilometers
- Elevation in meters
- Ride style

The current implementation hardcodes preference toggles in the request body:

- Avoid:
  - busy roads
  - urban areas
  - unpaved roads
  - repeated segments
- Prefer:
  - scenic routes
  - rolling roads
  - novelty disabled

These are not yet user-configurable in the UI even though the backend supports them.

## API Interaction

The page sends:

- `POST ${NEXT_PUBLIC_API_BASE_URL}/generate-route`

Expected result:

- A JSON payload containing a `routes` array

The UI then:

- Stores the routes in local React state
- Renders summary metrics for the top 3
- Lets the user choose the active route by clicking a card
- Passes the top 3 route geometries to one shared map
- Shows an elevation profile for the selected route

## Map Behavior

The map is dynamically imported with server-side rendering disabled:

- Leaflet requires browser APIs and should not run during SSR

Current behavior:

- Centers on the first point of the selected route
- Draws each route as a polyline
- Renders non-selected routes in light blue
- Renders the selected route in red with stronger emphasis
- Uses the OpenStreetMap tile layer

## GPX Download

The frontend does not ask the backend for GPX files. Instead, it converts the returned geometry to GPX XML in the browser and downloads the file directly.

This means:

- API consumers still receive JSON only
- Frontend downloads do not depend on CLI export paths
- Downloaded filenames use the backend-generated `route_id`

## Known Gaps

- No input validation beyond basic browser field handling
- No empty-state messaging beyond omission of route cards
- No advanced filter controls in the UI
- No tests for the React components
- Metadata in `layout.tsx` still contains default create-next-app values
