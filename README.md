# Zephyr Weather Eyeball

Single-file, offline-capable aviation go/no-go weather tool for balloon and light fixed-wing flight planning. Open `zephyr-weather-eyeball.html` in any modern browser — no build step, no backend, no keys. Live data comes from CORS-open public APIs (Open-Meteo forecast/ensemble/archive, api.weather.gov, RainViewer, OurAirports); the paste path keeps it usable offline.

**Current build:** `ZEPHYR-EYEBALL-2026.06.01-b352`
**README stamped (UTC):** 2026-10-26T02:06:56Z

## What it does
- Hourly winds-aloft profile, transport-wind / gust / shear verdict against editable personal minimums (balloon and airplane sets)
- 14-model surface-wind consensus, ensemble best-windows, flight-category and ceiling logic shared across METAR / TAF / NWS / model paths
- NWS products: 12 h METAR history, TAFs, AFD, active alerts, forecaster grid cross-check, SIGMET / Convective SIGMET / CWA within a radius
- 15-minute HRRR surface wind for the launch window, pressure-field "bubbles" (local / synoptic / regional tiers) with geostrophic gradient caution
- Drift: 3D track over a topo ground plane, pinch-zoom map with distance arcs and altitude-coloured track, ensemble landing cone, soft-ground along the track, POI landing candidates
- Launch window scorer (best 30-min slot, why it loses either side) and a trend-aware verdict
- Sun / civil-twilight clocks (14 CFR 1.1, 91.209, 61.57(b)), icing (incl. SLD codes), density altitude, heat stress, tether verdict
- Live drag-and-drop dashboard reorder; visual-tile mode for phones

## Layout
- `zephyr-weather-eyeball.html` — the app (build id and ship timestamp in the header comment and footer)
- `docs/audit-2026-10-23.md` — full-file audit with per-build fix status
- `tools/selftest.sh` — syntax/structure check + smoke test + screenshots (run from the repo root)
- `tools/smoke.js` — headless-Chromium smoke test (Playwright)
- `tools/shots.js` + `tools/fixture.js` — synthetic-forecast screenshot harness for every panel

## Conventions
One atomic change per build; build id `ZEPHYR-EYEBALL-2026.06.01-bNNN`; a fresh `date -u` timestamp is stamped into the file at ship time; changelog lives in the file header.

Not a substitute for a briefing. Verify against official sources before flight.
