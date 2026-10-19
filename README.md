# Voyager Explorer

A public-facing web app for exploring Voyager 1 and Voyager 2 through calculated spacecraft positions, signal travel times, historic images, and mission milestones.

## Project Status

**Planning stage.** This README describes the intended implementation. Features, API routes, and directories below are proposed rather than existing functionality. External API behavior and deployment requirements must be verified during implementation.

## Purpose

Make the scale and history of the Voyager missions understandable through an accessible, interactive experience built around official NASA and JPL data sources, without scraping webpages.

The project also provides practical experience with Python backend development, API integration, caching, data normalization, and scientific visualization.

## Minimum Viable Product

- [ ] Display separate summary cards for Voyager 1 and Voyager 2.
- [ ] Retrieve calculated spacecraft positions from JPL Horizons.
- [ ] Show distance from Earth and from the Sun in clearly labeled units.
- [ ] Show velocity with its reference frame identified.
- [ ] Calculate approximate one-way and round-trip signal travel times.
- [ ] Display the position epoch and the time data was last retrieved.
- [ ] Provide a small historic image gallery using NASA image search results.
- [ ] Add a curated timeline of major mission milestones with source links.
- [ ] Cache upstream responses and handle temporary service failures.
- [ ] Support desktop and mobile layouts.
- [ ] Include source attribution and image-specific credits.

## Data Sources

| Source | Planned use | Starting point |
| --- | --- | --- |
| JPL Horizons | Calculated positions, distances, and velocities | <https://ssd.jpl.nasa.gov/horizons/> |
| NASA Image and Video Library | Historic images and descriptive metadata | <https://images.nasa.gov/> |
| NASA/JPL mission publications | Manually curated mission milestones and updates | <https://science.nasa.gov/mission/voyager/> |
| Planetary Data System | Optional archival science and image exploration | <https://pds.nasa.gov/> |

NASA image search endpoint to investigate: `https://images-api.nasa.gov/search?q=voyager&media_type=image`.

Planned Horizons target identifiers are `-31` for Voyager 1 and `-32` for Voyager 2. Confirm target selection, supported time ranges, reference frames, units, and response formats against the current Horizons documentation before integration.

Mission webpages are reference material, not an assumed machine-readable status feed. The MVP will use manually curated updates with citations rather than scraping.

## Data Interpretation

### Calculated Positions

Horizons-derived positions are ephemeris calculations, not a live telemetry stream. The interface must identify the calculation epoch and distinguish it from retrieval time. If the display interpolates between sampled positions, label that behavior.

### Reference Frames and Units

Distances and velocities must identify their reference origin and coordinate frame. Earth-relative and Sun-relative values should be requested or derived consistently; they must not be mixed without a defined transformation.

Keep source units in the ingestion layer and normalize values explicitly before display. Suggested display units are kilometers, astronomical units, and kilometers per second. Define whether Earth means its center or a surface observing location.

### Signal Travel Time

For an educational approximation:

```text
one_way_seconds = earth_distance_km / 299792.458
round_trip_seconds = 2 * one_way_seconds
```

This simple calculation ignores motion during transmission and processing or scheduling delays. If using Horizons-provided light-time quantities, document their conventions and avoid applying light-time corrections twice.

### Telemetry and Mission Health

Power, signal strength, and subsystem status are outside the MVP unless an appropriate public data source is verified. Curated health updates must include a publication date and source. Do not present estimated or historic values as current measurements.

## Proposed Technology Stack

| Layer | Initial choice | Purpose |
| --- | --- | --- |
| Frontend | Next.js, React, TypeScript | Responsive interface and interactive displays |
| Backend | Python and FastAPI | Upstream requests, normalization, validation, and caching |
| HTTP client | httpx | Requests with explicit timeouts and error handling |
| Python tooling | uv | Dependency management and reproducible environments |
| Initial cache | In-memory cache with expiration | Simple development and single-process deployment |
| Optional shared cache | Redis | Consistent caching across multiple backend workers |
| Visualization | Simple 2-D chart initially | Explain relative position and trajectories |
| Later visualization | Three.js or Plotly | Optional interactive 3-D exploration |

An in-memory cache is process-local and resets on restart. Introduce a shared cache only when deployment or usage requires it. Separate image storage is not required initially; use source-provided image URLs where permitted.

## Proposed Architecture

The browser requests normalized data from FastAPI. The backend queries official services, validates responses, caches results, and returns a stable application schema. The frontend displays values together with timestamps, units, and source information.

- Keep any required credentials on the server.
- Restrict upstream requests to known services and validated parameters.
- Configure CORS for the deployed frontend origin.
- Use bounded retries and explicit request timeouts.
- Retain the last successful response when appropriate and clearly label stale data.
- Treat gallery descriptions as untrusted text; do not render raw upstream HTML.

### Proposed Backend Routes

| Route | Purpose |
| --- | --- |
| `GET /health` | Backend health check |
| `GET /api/spacecraft` | Normalized summaries for both spacecraft |
| `GET /api/spacecraft/{spacecraft_id}` | Detailed position and travel-time information |
| `GET /api/images` | Filtered Voyager image results with credits |
| `GET /api/timeline` | Curated mission milestones and source links |

These routes are design targets and are not implemented yet. Position responses should include spacecraft ID, epoch, reference origin, frame, units, retrieval timestamp, source, and stale-data status.

## Proposed Repository Structure

For the proposed repository structure, refer to the `docs/01_architecture/00_structure.md` file, which outlines the organization of the frontend, backend, data, and documentation directories.

## Development Setup Plan

The application has not been scaffolded. The commands below describe the intended workflow **after** the corresponding projects and dependency files exist.

### Backend

From `backend/`:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Use `uv add` when introducing backend dependencies and commit both `pyproject.toml` and `uv.lock`. An activated virtual environment is not required when using `uv run`.

### Frontend

From `frontend/`, after creating the Next.js application:

```bash
npm install
npm run dev
```

### Planned Configuration

| Variable | Example | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Backend URL visible to the browser |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed browser origin for backend CORS |
| `CACHE_TTL_SECONDS` | `3600` | Initial position-cache lifetime |

These variable names are proposed application settings. Implement configuration parsing before relying on them. Commit an `.env.example` with placeholders and exclude local secret files from Git. Never place secrets in variables prefixed with `NEXT_PUBLIC_`.

## Build Phases

### Phase 1 — Verify the Data

- [ ] Confirm Horizons target IDs and supported ephemeris intervals.
- [ ] Retrieve and inspect one response for each spacecraft.
- [ ] Confirm origin, frame, time scale, units, and light-time conventions.
- [ ] Verify NASA image metadata, usable asset URLs, credits, and usage terms.
- [ ] Record representative response fixtures for development.

### Phase 2 — Build the Backend

- [ ] Scaffold FastAPI and configuration.
- [ ] Implement Horizons retrieval and response normalization.
- [ ] Add signal travel-time calculations.
- [ ] Implement expiration-based caching.
- [ ] Add image search and curated timeline loading.
- [ ] Handle upstream errors, missing data, and stale responses.

### Phase 3 — Build the Interface

- [ ] Create spacecraft cards with explicit units and timestamps.
- [ ] Add loading, unavailable, and stale-data states.
- [ ] Build the gallery and timeline.
- [ ] Add accessible navigation and responsive layouts.
- [ ] Add attribution and data interpretation notes.

### Phase 4 — Validate and Deploy

- [ ] Test unit conversions and signal travel-time calculations.
- [ ] Test upstream response parsing using recorded fixtures.
- [ ] Test cache expiration and upstream failure behavior.
- [ ] Compare selected values with the same Horizons query parameters.
- [ ] Check mobile layouts, keyboard access, and text contrast.
- [ ] Select hosting after checking current pricing and runtime constraints.
- [ ] Configure deployment origins, environment variables, and basic logging.

## Future Features

- [ ] “Send a Message” simulation showing approximate reply arrival time.
- [ ] Interactive 2-D trajectory plots.
- [ ] Optional 3-D viewer with clearly explained distance scaling.
- [ ] Historical date selection within supported ephemeris ranges.
- [ ] Comparisons with other spacecraft after verifying data availability.
- [ ] Curated links to archival science datasets.

## MVP Boundaries

The first release excludes live engineering telemetry, spacecraft control, a full solar-system simulator, and user accounts. A focused release should make distances, signal delay, mission history, and source provenance easy to understand.

## Attribution and Usage

This is an independent educational project and is not affiliated with or endorsed by NASA or JPL. Check applicable usage policies and individual image credits, including third-party material. Preserve asset-specific attribution rather than assuming every item has identical rights. Choose a software license separately before publishing the repository.

Suggested footer: “Independent educational project. Data and imagery sources: NASA, JPL, and credited contributors.”
