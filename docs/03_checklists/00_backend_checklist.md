# Voyager Tracker — Backend Checklist

Use this as the backend implementation roadmap. Check an item only after its completion criteria are met. Record troubleshooting, decisions, and session results separately in `docs/dev_diary/`.

## 1. Project Foundation

- [x] Initialize the backend project with uv.
- [x] Establish the repository structure basics.
- [x] Configure the `src/voyager_tracker/` Python package.
- [x] Configure Hatchling and the package location in `pyproject.toml`.
- [x] Install FastAPI and Uvicorn.
- [x] Verify that Python can import `voyager_tracker`.
- [x] Create the FastAPI application entry point in `main.py`.
- [x] Start the backend successfully with Uvicorn.
- [ ] Confirm `GET /health` returns HTTP 200 and `{"status": "ok"}`.
- [ ] Confirm the health route can be executed through `/docs`.
- [ ] Confirm Git excludes `.venv/`, local secrets, and Python cache files.
- [ ] Commit the dependency configuration and `uv.lock`.

Run development commands from `backend/`:

```bash
uv run uvicorn voyager_tracker.main:app --reload
```

**Completion:** The package imports, the server starts, and the health route responds.

## 2. Verify One Horizons Request

Start with Voyager 1 and a Sun-centered position request. Verify current official API documentation before choosing query parameters.

- [ ] Install `httpx` with `uv add httpx`.
- [ ] Create `src/voyager_tracker/services/horizons.py`.
- [ ] Confirm the spacecraft target identifier and supported ephemeris dates.
- [ ] Choose the query type, reference origin, coordinate frame, time scale, and output units.
- [ ] Request a small sample covering one or two epochs.
- [ ] Set an explicit HTTP timeout and check the HTTP status.
- [ ] Inspect the returned response, including any error reported inside a successful HTTP response.
- [ ] Identify the actual ephemeris payload within the response envelope.
- [ ] Record units, time conventions, query parameters, and parsing observations in `docs/data_sources.md`.
- [ ] Save a representative response as a test fixture with its query metadata; exclude secrets if any.

**Completion:** A repeatable request returns understood data for Voyager 1. No public application route is required yet.

## 3. Parse and Normalize the Data

- [ ] Separate upstream request logic from parsing and calculations.
- [ ] Parse the selected epoch and position values from the actual Horizons payload.
- [ ] Define a Pydantic response model in `schemas/`.
- [ ] Include spacecraft identity, epoch, origin, frame, time scale, units, retrieval time, and source.
- [ ] Represent Sun-relative distance and speed with explicit names and units.
- [ ] Reject incomplete or malformed payloads rather than returning fabricated values.
- [ ] Compare parsed results with the same query in the Horizons interface or official output.

**Completion:** The service returns a validated application model rather than an unprocessed upstream response.

## 4. Expose the First Spacecraft Route

- [ ] Create a spacecraft router in `api/`.
- [ ] Register the router in `main.py`.
- [ ] Implement `GET /api/spacecraft/{spacecraft_id}` for Voyager 1.
- [ ] Validate supported identifiers and return a clear error for unsupported spacecraft.
- [ ] Keep request handling in the route and upstream logic in the service.
- [ ] Use asynchronous HTTP requests if the route is asynchronous; avoid blocking network calls inside it.
- [ ] Return the defined response model.
- [ ] Document the endpoint and its reference conventions in `/docs`.
- [ ] Verify the endpoint through `/docs`.

**Completion:** A browser request returns normalized Voyager 1 data with source and epoch information.

## 5. Add Earth Distance and Signal Travel Time

- [ ] Obtain Earth-relative distance using a documented, consistent origin and epoch.
- [ ] Keep Earth-relative and Sun-relative quantities clearly separated.
- [ ] Calculate approximate one-way light time using distance divided by the speed of light.
- [ ] Calculate the approximate round-trip delay as twice the one-way value.
- [ ] Label these calculations as approximations, excluding spacecraft motion during transmission and processing delays.
- [ ] If using Horizons light-time outputs, document their conventions and avoid double corrections.
- [ ] Preserve numeric values for the frontend rather than returning only formatted strings.

**Completion:** The response distinguishes Earth and Sun distances and provides interpretable signal-delay values.

## 6. Add Voyager 2 and Combined Summaries

- [ ] Extend spacecraft configuration to include Voyager 2.
- [ ] Reuse request and parsing logic without duplicating the service.
- [ ] Verify Voyager 2 values using the same query conventions.
- [ ] Implement `GET /api/spacecraft` for both summaries.
- [ ] Define how the combined endpoint reports a partial failure when one spacecraft is unavailable.

**Completion:** Both spacecraft are available individually and through a documented summary route.

## 7. Add Caching and Failure Handling

- [ ] Add a configurable expiration time for the initial in-memory cache.
- [ ] Include query-defining parameters in cache keys so different origins and epochs cannot collide.
- [ ] Distinguish the position epoch, original retrieval time, and cache expiration.
- [ ] Cache successful, validated results rather than error payloads.
- [ ] Define a maximum acceptable stale-data age.
- [ ] Preserve last successful data during temporary failures only within that limit.
- [ ] Label stale responses explicitly.
- [ ] Return controlled errors when no usable cached data exists.
- [ ] Handle upstream timeouts, HTTP errors, API-level errors, and parsing failures.
- [ ] Add bounded retries only for suitable transient failures.
- [ ] Add useful logs without credentials or excessive response dumps.

**Completion:** Repeated requests use the cache, and upstream failures produce predictable results. Redis is optional and should wait until a shared cache is needed.

## 8. Prepare the Frontend Connection

- [ ] Centralize backend configuration in `core/`.
- [ ] Configure CORS for the specific local frontend origin if browser requests go directly to FastAPI.
- [ ] Document environment variables and defaults.
- [ ] Add a safe `.env.example` without credentials.
- [ ] Keep the HTTP response schema consistent and document any changes.
- [ ] Verify the chosen frontend request path can read the spacecraft endpoint.

**Completion:** The frontend can request spacecraft data using the intended local architecture.

## 9. Add the Image Gallery Service

- [ ] Verify the current NASA Image and Video Library API contract and asset usage requirements.
- [ ] Implement curated or constrained Voyager image search in a separate service.
- [ ] Resolve usable asset URLs according to the actual API response structure.
- [ ] Normalize titles, descriptions, dates, image URLs, source links, and credits.
- [ ] Return bounded results with pagination if needed.
- [ ] Cache results independently of spacecraft positions.
- [ ] Handle absent images and metadata fields.
- [ ] Expose `GET /api/images` with a response model.

**Completion:** The gallery route returns relevant images with attribution and usable URLs. Separate image storage is not required initially.

## 10. Add the Mission Timeline

- [ ] Define a milestone schema with spacecraft, date, title, description, and source URL.
- [ ] Curate and verify the initial milestones.
- [ ] Choose how timeline data is packaged or made available to the deployed backend.
- [ ] Load data without depending on the terminal's working directory.
- [ ] Validate records and chronological ordering.
- [ ] Expose `GET /api/timeline`.

**Completion:** The timeline endpoint returns validated, sourced milestones locally and in the deployment layout.

## 11. Verify Behavior as Features Are Added

Do these checks alongside the relevant phases; do not defer all validation until the end. Install test tooling when the first meaningful tests are introduced.

- [ ] Test unit conversions and signal-delay calculations with known inputs.
- [ ] Test Horizons parsing against representative fixtures, including malformed and API-error responses.
- [ ] Test route validation and response schemas with upstream calls mocked.
- [ ] Test cache hits, expiration, stale limits, and upstream failure behavior.
- [ ] Test partial failures for the combined spacecraft endpoint.
- [ ] Test gallery normalization and timeline validation.
- [ ] Keep routine tests independent of live NASA/JPL availability.
- [ ] Document a separate manual live-data verification procedure.
- [ ] Run the relevant checks before each completed feature is committed.

**Completion:** Core calculations, parsing, and failure behavior have repeatable checks.

## 12. Prepare Deployment

- [ ] Select hosting after verifying current pricing and Python runtime support.
- [ ] Configure deployment to use `backend/` as its project directory.
- [ ] Use reproducible dependency installation from the lockfile.
- [ ] Configure the production start command without `--reload`.
- [ ] Bind to the host and port required by the hosting platform.
- [ ] Set production origins and configuration values.
- [ ] Confirm curated data and required package files are included.
- [ ] Understand that an in-memory cache is separate for each worker and resets on restart.
- [ ] Verify public health, spacecraft, image, and timeline routes.
- [ ] Confirm logs and error responses are useful without exposing internals.
- [ ] Update the project documentation with actual setup and deployment commands.

**Completion:** The deployed backend supports the frontend and handles unavailable upstream services predictably.

## Ongoing Documentation

- [ ] Add a dated diary entry after each substantive work session.
- [ ] Update `docs/architecture.md` when the current design changes.
- [ ] Update `docs/data_sources.md` when API conventions or source assumptions are verified.
- [ ] Update this checklist as work is completed or scope changes.

## Immediate Next Action

Confirm the health endpoint and `/docs` responses, then begin **Phase 2: Verify One Horizons Request**. The first milestone is an understood Voyager 1 response—not a complete tracker.
