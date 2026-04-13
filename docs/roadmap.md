# Roadmap

This document captures the current short-to-medium term backlog for Ride Wit Me.

## Near-Term Priorities

- Improve the start-location flow in the UI.
  Done in v1: address/place lookup and direct coordinate entry now coexist, the frontend can resolve an address into coordinates through the backend geocoding endpoint, the latest used location is restored from local storage, and first-time visits start blank instead of using hardcoded coordinates.
  Remaining: richer address search and autocomplete, better geocoding result selection and error states, and map click selection as a phase-2 bonus.
- Support user-provided OpenRouteService API keys instead of relying only on one shared project key.
  Notes: this would let friends use the app without consuming a single owner-managed quota.
- Return a more reliable set of route choices per request.
  Goal: improve candidate generation so route requests empirically yield a healthier set of viable choices; in the current state, too many requests only return a single usable option.
- Revisit scoring weights for ride styles other than `endurance`.
  Notes: the current tuning has mainly been optimized around endurance rides, so `hilly`, `scenic`, and `exploration` need dedicated manual calibration first.

## Product And UX

- Expand the frontend beyond the current minimal request form.
  Notes: there is a large backlog of possible UI features, and the next step is to decide which features most improve route selection confidence and usability.
- Add explicit empty, loading, and result-comparison states that help users understand why one route was selected over another.
- Expose more ride preferences in the UI instead of keeping them hardcoded in the request body.
- Save the latest used start location, distance, elevation, and ride style as sensible defaults for the next session.
- Add one-click refinements after results such as `shorter`, `longer`, `flatter`, `more climbing`, and `more scenic`.
- Support side-by-side comparison for two candidate routes.
- Add route badges such as `best match`, `least urban`, `best climbing`, `least repeated`, or similar distinctions.
- Show richer preview summaries before deep inspection, including surface quality, urban exposure, repeated-segment ratio, and climb character.
- Show direction-of-travel arrows on the route path so the riding direction is obvious, for example every 5 to 10 km.
- Link the map path and elevation profile with a shared hover state so a moving marker highlights the corresponding position on both views.
- Let users save favorite routes and share them with a link.
- Add ready-made ride presets such as `after-work spin`, `Sunday endurance`, and `climbing day`.
- Build a more mobile-friendly flow since the product is well suited to on-the-go use.

## Platform And Deployment

- Deploy the app somewhere reachable on the web instead of running it only locally.
  Notes: this includes choosing hosting for the frontend and backend, deciding how secrets are managed, and defining a production-friendly deployment workflow.
- Decide how user-supplied API keys should be stored and scoped.
  Notes: options may include browser-session only usage, encrypted server-side storage, or no storage at all.
- Offer two product modes: a lightweight demo mode and a `use my own ORS key` mode.
- Add lightweight authentication if saved preferences, favorites, or personal API-key management become part of the product.
- Cache geocoding lookups and route requests where possible to reduce cost and improve response times.
- Add background job handling if route generation starts taking too long for a direct request/response flow.
- Create a simple landing page and friend-invite flow if the app becomes shareable beyond the immediate test circle.

## Product Direction

- The target shape is something in between a private tool and a public app: built for friends first, but shareable more widely.
- The "5 routes" goal is an empirical quality target rather than a strict product requirement; the immediate problem is that too many requests currently collapse to a single option.
- Address search should start with city/street lookup and reuse the latest location by default.
- Address search should coexist with direct coordinate entry rather than replacing it.
- The first version can use a simple address resolve action before richer autocomplete work.
- Map click selection is a useful follow-up, but not the first version of the address-input improvement.
- Ride-style tuning should start manually, with future evaluation tooling kept as a later enhancement.

## Routing Quality Ideas

- Add a retry strategy that progressively relaxes constraints when the engine finds only one weak option.
- Rank for route diversity as well as overall score so the top options are meaningfully different from each other.
- Add a route-level confidence or match-quality indicator.
- Introduce route flavors such as `closest match`, `safer`, `more scenic`, `harder`, and `wild card`.
- Keep a small pool of near-miss routes instead of dropping everything below one threshold immediately.
- Add "start somewhere else nearby" suggestions when a given location repeatedly produces poor route options.

## Learning And Tuning

- Add lightweight thumbs up/down feedback on generated routes.
- Track which route a rider actually chooses from a result set.
- Build a small manual test set for each ride style and reuse it whenever weights are retuned.
- Add clearer "why this route was not selected" explanations for lower-ranked options.

## Future Ideas

- Add a repeatable evaluation dataset or continuous scoring checks once manual ride-style tuning has stabilized.
- Add weather and wind context to help riders choose between otherwise similar routes.
- Support more export and handoff options beyond GPX, especially formats or flows that work well with tools such as Komoot or Strava.
