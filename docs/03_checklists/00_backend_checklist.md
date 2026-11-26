# Voyager Tracker — Backend Checklist

Use this as the backend implementation roadmap. Check an item only after its completion criteria are met. Record troubleshooting, decisions, and session results separately in `docs/99_dev_diary/`.

Prioritize a minimal current-time Voyager 1 endpoint and its tests before expanding to both spacecraft, caching, images, and the timeline. A thin frontend can be tried against that endpoint without waiting for every backend phase.

## 1. Project Foundation

- [x] Initialize the backend project with uv.
- [x] Establish the repository structure basics.
- [x] Configure the `src/voyager_tracker/` Python package.
- [x] Configure Hatchling and the package location in `pyproject.toml`.
- [x] Install FastAPI and Uvicorn.
- [x] Verify that Python can import `voyager_tracker`.
- [x] Create the FastAPI application entry point in `main.py`.
- [x] Start the backend successfully with Uvicorn.
- [x] Confirm `GET /health` returns HTTP 200 and `{"status": "ok"}`.
- [x] Confirm the health route can be executed through `/docs`.
- [x] Confirm Git excludes `.venv/`, local secrets, and Python cache files.
- [x] Commit the dependency configuration and `uv.lock`.

Run development commands from `backend/`:

```bash
uv run uvicorn voyager_tracker.main:app --reload
```

**Completion:** The package imports, the server starts, and the health route responds.

## 2. Tooling and Continuous Integration

Set these up early so every later phase benefits from them.

- [x] Install pytest as a dev dependency (`uv add --dev pytest`).
- [x] Configure pytest in `pyproject.toml` (`testpaths = ["tests"]`).
- [x] Move development-only packages (e.g. `ipython`) from runtime dependencies to the dev group.
- [x] Add ruff for linting and formatting; configure rules in `pyproject.toml` (`[tool.ruff]`).
- [x] Add a type checker: pyright, strict on `src/`, standard on `tests/` (configured in `pyproject.toml`).
- [x] Add a CI workflow (`.github/workflows/backend.yml`) that runs `uv sync --locked`, ruff lint and format checks, pyright, and pytest.
- [x] Confirm the first CI run passes on GitHub.

**Completion:** Tests and lint run identically on a local machine and in CI from the lockfile.

## 3. Verify One Horizons Request

Start with Voyager 1 and a Sun-centered position request. Verify current official API documentation before choosing query parameters.

- [x] Install `httpx2` with `uv add httpx2` (replaced the original `httpx`).
- [x] Create `src/voyager_tracker/services/horizons.py`.
- [x] Confirm the spacecraft target identifier and supported ephemeris dates.
- [x] Choose the query type, reference origin, coordinate frame, time scale, and output units.
- [x] Request a small sample covering one or two epochs.
- [x] Set an explicit HTTP timeout and check the HTTP status.
- [x] Inspect the returned response, including any error reported inside a successful HTTP response.
- [x] Identify the actual ephemeris payload within the response envelope.
- [x] Record units, time conventions, query parameters, and parsing observations in `docs/02_data_sources/00_data_sources.md`.
- [x] Save a representative response as a test fixture (e.g. `backend/tests/fixtures/`) with its query metadata; exclude secrets if any.

**Completion:** A repeatable request returns understood data for Voyager 1. No public application route is required yet.

## 4. Parse and Normalize the Data

- [ ] Keep upstream request logic distinct from parsing and calculations; split files only if useful.
- [x] Parse the selected epoch and position values from the actual Horizons payload.
- [x] Define an internal Pydantic model for parsed states in `schemas/` (`SpacecraftState`).
- [x] Expose derived values (distance, speed) with `@computed_field` so they appear in serialized output.
- [ ] Define the public response contract; use a separate model when it needs to differ from the internal model.
- [ ] Include spacecraft identity, epoch, origin, frame, time scale, units, retrieval time, and source.
- [x] Normalize the fixed sample's Horizons calendar epoch (`A.D. 2026-Oct-19 00:00:00.0000`) into a timezone-aware UTC `datetime`.
- [ ] Preserve the time scale and uncertainty of future UT values when leap seconds are unknown before accepting future epochs.
- [x] Represent Sun-relative distance and speed with explicit names and units.
- [x] Choose a current-time query strategy (e.g. round to the hour for cacheability; stay within supported ephemeris dates) while preserving the fixed sample for tests.
- [x] Reject rows with an unexpected field count or unconvertible numeric values.
- [x] Reject non-finite numeric values and test malformed rows, invalid tables, and API-error responses.
- [ ] Handle upstream and parsing failures explicitly; introduce project exception types if needed to distinguish response behavior.
- [ ] Compare parsed results with the same query in the Horizons interface or official output.

**Completion:** The service returns a validated application model rather than an unprocessed upstream response.

## 5. Expose the First Spacecraft Route

- [ ] Create a spacecraft router in `api/`.
- [ ] Register the router in `main.py`; decide on a versioned prefix (e.g. `/api/v1`) before the frontend depends on URLs.
- [ ] Implement `GET /api/spacecraft/{spacecraft_id}` for Voyager 1.
- [ ] Constrain `spacecraft_id` with an `Enum` or `Literal` so invalid IDs return 422 and valid options appear in `/docs`.
- [ ] Keep request handling in the route and upstream logic in the service.
- [ ] Choose sync or async deliberately: a sync client is fine in a `def` route (FastAPI uses a threadpool); use `httpx2.AsyncClient` only in `async def` routes, and never block inside them.
- [ ] Consider a shared HTTP client in the app `lifespan` when connection reuse is useful, and close it on shutdown.
- [ ] Make upstream calls substitutable in tests; use `Depends` and `app.dependency_overrides` if appropriate.
- [ ] Map upstream and parsing failures to controlled responses (e.g. 502 upstream error, 503 unavailable, 504 timeout) with one consistent error schema; add exception handlers where useful.
- [ ] Return the defined response model via `response_model=`.
- [ ] Document the endpoint, its reference conventions, and its error responses in `/docs`.
- [ ] Verify the endpoint through `/docs`.

**Completion:** A browser request returns normalized Voyager 1 data with source and epoch information.

## 6. Add Earth Distance and Signal Travel Time

- [ ] Obtain Earth-relative distance using a documented, consistent origin and epoch.
- [ ] Keep Earth-relative and Sun-relative quantities clearly separated.
- [ ] Calculate approximate one-way light time using distance divided by the speed of light.
- [ ] Calculate the approximate round-trip delay as twice the one-way value.
- [ ] Label these calculations as approximations, excluding spacecraft motion during transmission and processing delays.
- [ ] If using Horizons light-time outputs, document their conventions and avoid double corrections.
- [ ] Preserve numeric values for the frontend rather than returning only formatted strings.

**Completion:** The response distinguishes Earth and Sun distances and provides interpretable signal-delay values.

## 7. Add Voyager 2 and Combined Summaries

- [ ] Extend spacecraft configuration to include Voyager 2.
- [ ] Reuse request and parsing logic without duplicating the service.
- [ ] Verify Voyager 2 values using the same query conventions.
- [ ] Implement `GET /api/spacecraft` for both summaries.
- [ ] Define how the combined endpoint reports a partial failure when one spacecraft is unavailable.

**Completion:** Both spacecraft are available individually and through a documented summary route.

## 8. Add Caching and Failure Handling

- [ ] Add a configurable expiration time for the initial in-memory cache.
- [ ] Include query-defining parameters in cache keys so different origins and epochs cannot collide.
- [ ] Distinguish the position epoch, original retrieval time, and cache expiration.
- [ ] Cache successful, validated results rather than error payloads.
- [ ] Add single-flight locking if concurrent refreshes become a concern.
- [ ] If stale-data fallback is needed, define a maximum acceptable age, preserve only eligible successful data, and label stale responses explicitly.
- [ ] Return controlled errors when no usable cached data exists.
- [ ] Handle upstream timeouts, HTTP errors, API-level errors, and parsing failures.
- [ ] Add bounded retries for suitable transient failures only if needed.
- [ ] Optionally set `Cache-Control` headers consistent with the server-side cache.
- [ ] Keep `/health` independent of upstream services; add a separate readiness/upstream-status check only if needed.
- [ ] Add useful logs without credentials or excessive response dumps.

**Completion:** Repeated requests use the cache, and upstream failures produce predictable results. Redis is optional and should wait until a shared cache is needed.

## 9. Prepare the Frontend Connection

- [ ] Centralize backend configuration when needed; use `pydantic-settings` only if its features are useful.
- [ ] Configure CORS for the specific local frontend origin if browser requests go directly to FastAPI.
- [ ] Document environment variables and defaults.
- [ ] Add a safe `.env.example` without credentials.
- [ ] Keep the HTTP response schema consistent and document any changes.
- [ ] Verify the chosen frontend request path can read the spacecraft endpoint.

**Completion:** The frontend can request spacecraft data using the intended local architecture.

## 10. Add the Image Gallery Service

- [ ] Verify the current NASA Image and Video Library API contract and asset usage requirements.
- [ ] Implement curated or constrained Voyager image search in a separate service.
- [ ] Resolve usable asset URLs according to the actual API response structure.
- [ ] Normalize titles, descriptions, dates, image URLs, source links, and credits.
- [ ] Return bounded results with pagination if needed.
- [ ] Cache results independently of spacecraft positions.
- [ ] Handle absent images and metadata fields.
- [ ] Expose `GET /api/images` with a response model.

**Completion:** The gallery route returns relevant images with attribution and usable URLs. Separate image storage is not required initially.

## 11. Add the Mission Timeline

- [ ] Define a milestone schema with spacecraft, date, title, description, and source URL.
- [ ] Curate and verify the initial milestones.
- [ ] Package timeline data inside `src/voyager_tracker/` so Hatchling includes it in the build.
- [ ] Load data with `importlib.resources`, not paths relative to the terminal's working directory.
- [ ] Validate records and chronological ordering.
- [ ] Expose `GET /api/timeline`.

**Completion:** The timeline endpoint returns validated, sourced milestones locally and in the deployment layout.

## 12. Verify Behavior as Features Are Added

Do these checks alongside the relevant phases; do not defer all validation until the end.

- [x] Test the health route (status, body, content type, method).
- [x] Test derived distance and speed values and their serialization.
- [ ] Test unit conversions and signal-delay calculations with known inputs.
- [ ] Test Horizons parsing against representative fixtures, including malformed and API-error responses.
- [ ] Test route validation and response schemas with upstream calls mocked (e.g. `app.dependency_overrides` or `httpx2.MockTransport`).
- [ ] Test that upstream failures return the documented status codes and error schema.
- [ ] Test cache hits, expiration, and upstream failure behavior; test stale limits if fallback is implemented.
- [ ] Test partial failures for the combined spacecraft endpoint.
- [ ] Test gallery normalization and timeline validation.
- [ ] Keep routine tests independent of live NASA/JPL availability.
- [ ] Document a separate manual live-data verification procedure.
- [ ] Run the relevant checks before each completed feature is committed.

**Completion:** Core calculations, parsing, and failure behavior have repeatable checks.

## 13. Prepare Deployment

- [ ] Select hosting after verifying current pricing and Python runtime support.
- [ ] Configure deployment to use `backend/` as its project directory.
- [ ] Install reproducibly from the lockfile without dev dependencies (`uv sync --locked --no-dev`).
- [ ] Configure the production start command without `--reload`.
- [ ] Bind to the host and port required by the hosting platform.
- [ ] If behind a proxy, configure Uvicorn `--proxy-headers` and `--forwarded-allow-ips`.
- [ ] Set production origins and configuration values.
- [ ] Decide whether `/docs` and `/openapi.json` are public in production.
- [ ] Confirm curated data and required package files are included in the built package.
- [ ] Understand that an in-memory cache is separate for each worker and resets on restart.
- [ ] Verify public health, spacecraft, image, and timeline routes.
- [ ] Confirm logs and error responses are useful without exposing internals.
- [ ] Update the project documentation with actual setup and deployment commands.

**Completion:** The deployed backend supports the frontend and handles unavailable upstream services predictably.

## Ongoing Documentation

- [ ] Add a dated diary entry in `docs/99_dev_diary/` after each substantive work session.
- [ ] Update `docs/01_architecture/00_structure.md` when the current design changes.
- [ ] Update `docs/02_data_sources/00_data_sources.md` when API conventions or source assumptions are verified.
- [ ] Update this checklist as work is completed or scope changes.

## Immediate Next Action

Continue **Phase 4** by defining the response metadata and handling upstream failures. Future UT epochs remain unsupported until their time-scale uncertainty can be represented. Then expose a minimal, tested Voyager 1 route before expanding the backend.
