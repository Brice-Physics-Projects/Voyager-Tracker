# Backend Section 4 Readiness Audit

## 1. Executive Summary

**Readiness: READY WITH CONDITIONS.** Sections 1–4 are marked complete; section 5, the first spacecraft route, is next. The backend has a working health route, a fixture-backed Horizons service, a typed response contract, reproducible dependency configuration, and passing local quality checks.

The sample's scientific conventions and vector parsing have documented comparison with Horizons. Two important gaps remain: callers can change scientific query parameters while receiving Sun-relative, km-labeled states, and the current-state service does not check the returned report's conventions before applying its fixed labels. These should be corrected preferably before starting section 5, and **must be corrected before exposing the spacecraft response**. This does not imply the verified fixed sample is wrong.

The Dependabot configuration also does not select uv's lockfile ecosystem. No critical findings or findings that block beginning section 5 were identified.

## 2. Audit Scope and Methodology

- **Audit date:** 2026-11-26.
- **Branch and commit:** `dev`, `45f5cffdcd12ff165fe993b1847aab180582ca4a`. The supplied audit prompt was staged as a new file before the audit; it is not part of that commit. Findings refer to the working tree at audit start. This report is the only audit-created project file.
- **Reviewed:** backend source, tests, capture script, fixture metadata and values, `pyproject.toml`, selected `uv.lock` entries, Python pin, CI workflow, Dependabot configuration, `.gitignore`, README, project plan, architecture and data-source documentation, checklist, and diary entries. Section 4 was evaluated in detail; sections 1–3 and completed cross-cutting section 12 items were checked against available code, tests, configuration, and history. Later sections were considered only for timing and dependencies.
- **Methods:** source and call-path review, fixture and documented official-output comparison, local tests and quality checks, read-only synthetic failure probes, GitHub CI and Dependabot alert queries, and review of current GitHub and uv documentation.

### Executed verification

From `backend/`:

| Command | Result |
| --- | --- |
| `uv run --locked --no-sync pytest -q` | 31 passed |
| `uv run --locked --no-sync ruff check .` | Passed |
| `uv run --locked --no-sync ruff format --check .` | 14 files already formatted |
| `uv run --locked --no-sync pyright` | 0 errors, 0 warnings |
| `uv lock --check` | Passed; 49 packages resolved |
| `uv run --locked --no-sync python -c '...TestClient...'` | `/health` returned 200 and `{"status":"ok"}`; `/docs` returned 200; `/health` appeared in OpenAPI |

`gh run list --workflow backend.yml --limit 5 --json status,conclusion,headSha,headBranch,createdAt,url` returned successful runs, including [run 45764876453](https://github.com/Brice-Physics-Projects/Voyager-Tracker/actions/runs/45764876453) for `13c8244`, not the audited HEAD. `gh api .../dependabot/alerts` returned zero open alerts visible to the authenticated user. Synthetic in-memory Python probes exercised mismatched parameters and report headers, plus finite inputs whose calculated magnitude overflows; no project files were modified.

**Limitations:** No fresh live Horizons request or independent trajectory validation was performed for this audit; the documented November 26 text-output comparison is prior evidence, not a new audit run. No coverage percentage or comprehensive vulnerability scan was performed. No open Dependabot alerts is not proof of vulnerability absence or complete lockfile coverage. Dependabot update execution was not confirmed; listing its update endpoint returned 404 and no Dependabot PRs were returned. The local test-client check does not independently reproduce the historical Uvicorn startup or interactive browser execution of `/docs`. GitHub CI at the exact audited HEAD was not verified. The initial `python` documentation lookup failed because `python` was not on the system PATH, and a subsequent raw-document URL returned 404; the published uv guide was retrieved successfully instead.

## 3. Current Development Status

| Area | Assessment |
| --- | --- |
| Sections 1–2 | Foundation, `/health`, dependencies, CI and configured checks are present. Local checks pass; past successful CI runs provide corroboration, subject to the limitations above. |
| Section 3 | Fixed Voyager 1 query, timeout, HTTP/API error handling, report fixture and metadata exist. The fixture and source document the conventions. |
| Section 4 | Parsing, UTC normalization for accepted epochs, finite input checks, derived fields, current-hour selection, response model, retrieval timestamp and documented official comparison exist. Convention validation is incomplete as described in BE-AUD-001 and BE-AUD-002. |
| Section 5 | No spacecraft route exists; this is the next incomplete section, not a missing feature in the completed milestone. |
| Sections 6–13 | Earth-relative data, Voyager 2, caching, frontend integration, gallery, timeline and deployment remain planned. Cross-cutting tests are partly complete: fixture/error tests exist even though `docs/03_checklists/00_backend_checklist.md:180` remains unchecked. |

Rejecting future UT epochs is an intentional boundary, not a deficiency. Existing fixed-sample and current-time tests depend on the machine clock being after the 2026 fixture epochs.

## 4. Audit Findings Summary

| ID | Finding | Category | Priority | Resolution Timing | Effort |
| --- | --- | --- | --- | --- | --- |
| BE-AUD-001 | Request parameters can contradict state labels | Scientific correctness | High | Before Proceeding — Recommended | Small |
| BE-AUD-002 | Report conventions are not checked before fixed metadata is returned | Scientific correctness | High | Before Proceeding — Recommended | Medium |
| BE-AUD-003 | Dependabot does not select the uv lockfile ecosystem | Dependency management | Medium | Before Proceeding — Recommended | Small |
| BE-AUD-004 | Finite components can produce non-finite serialized magnitudes | Numerical integrity | Medium | Next Section | Small |
| BE-AUD-005 | README describes an unscaffolded backend and an incorrect startup module | Documentation | Low | Later Milestone | Small |
| BE-AUD-006 | Fixture capture can replace a valid fixture with an unusable response | Test reliability | Low | Later Milestone | Small |

## 5. Detailed Audit Findings

### BE-AUD-001 — Request parameters can contradict state labels

- **Category:** Scientific correctness. **Priority:** High. **Resolution timing:** Before Proceeding — Recommended. **Effort:** Small.
- **Affected files / evidence:** `backend/src/voyager_tracker/services/horizons.py:37-42,86-107,131-138`; `backend/src/voyager_tracker/schemas/spacecraft.py:7-31`; `docs/02_data_sources/00_data_sources.md:89-100`.
- **Relevant checklist requirement:** Section 4: Sun-relative distance and speed with explicit names and units; validated application model.
- **Description and impact:** `get_voyager_1_states` validates only `TIME_TYPE`, while accepting arbitrary target, center, frame, units and corrections. Parsed values always become `x_km` and Sun-relative computed fields. A synthetic probe passed Earth-centered, AU-D parameters and obtained `distance_from_sun_km=5.0` and `speed_relative_to_sun_km_s=10.0`. Incompatible values can therefore be mislabeled. The normal current-time call currently constructs the fixed intended query, so this is not evidence that the checked fixture is wrong.
- **Corrective action:** Restrict the state-returning workflow to its verified query-defining settings, allowing only supported time parameters to vary, or explicitly model and validate different conventions before labeling results.
- **Dependencies:** None.
- **Acceptance criteria:** Tests reject incompatible target, center, frame, units and correction settings; the fixed sample and current-time queries still succeed.
- **Deferral justification:** Section 5 development may begin, but do not expose this workflow through a route until its invariant is enforced.

### BE-AUD-002 — Report conventions are not checked before fixed metadata is returned

- **Category:** Scientific correctness. **Priority:** High. **Resolution timing:** Before Proceeding — Recommended. **Effort:** Medium.
- **Affected files / evidence:** `backend/src/voyager_tracker/services/horizons.py:46-68,111-128,158-182`; `docs/02_data_sources/00_data_sources.md:202-205`; `backend/tests/services/test_horizons.py:28-74`.
- **Relevant checklist requirement:** Section 4: include identity, origin, frame, time scale, units and source; section 5: return a trustworthy response.
- **Description and impact:** The service checks that a table exists and that the current rows have expected epochs, but applies fixed metadata without validating the report's target, origin, frame, units or correction. A synthetic fixture report with altered target, center, units and frame was accepted by `get_current_voyager_1_state` and labeled Voyager 1, Sun, ICRF and km. The actual recorded and previously compared report had the correct conventions.
- **Corrective action:** Validate relevant report metadata against the requested conventions before constructing a public response; reject missing or inconsistent metadata with `HorizonsResponseError`. Account for the actual Horizons report format rather than matching unrelated narrative text.
- **Dependencies:** BE-AUD-001 establishes the request-side invariant.
- **Acceptance criteria:** Fixture-backed tests for wrong or missing target, origin, frame, units and geometric correction fail explicitly; the recorded response still succeeds and its returned metadata agrees with its validated report.
- **Deferral justification:** Work on route structure can begin, but the route must not expose unverified fixed scientific labels.

### BE-AUD-003 — Dependabot does not select the uv lockfile ecosystem

- **Category:** Dependency management. **Priority:** Medium. **Resolution timing:** Before Proceeding — Recommended. **Effort:** Small.
- **Affected files / evidence:** `.github/dependabot.yml:1-10`; `backend/pyproject.toml:1-23`; `backend/uv.lock:1-3`; `.github/workflows/backend.yml:37-38`. The [uv Dependabot guide](https://docs.astral.sh/uv/guides/integration/dependabot/) explicitly directs users to `package-ecosystem: uv` to update `uv.lock`.
- **Relevant checklist requirement:** Section 2: reproducible dependency management and CI from the lockfile.
- **Description and impact:** The configured Python ecosystem is `pip`, but this project commits a uv lockfile and CI installs with `uv sync --locked`. The configuration does not explicitly enable uv lockfile updates. An update that changes the manifest without a matching lockfile can fail locked CI; no actual Dependabot update run was observed, so its precise behavior here is not asserted.
- **Corrective action:** Configure the supported uv ecosystem for `/backend`, retaining the GitHub Actions entry; check the resulting update behavior and avoid duplicate Python updates.
- **Dependencies:** GitHub Dependabot must run against the updated configuration.
- **Acceptance criteria:** A Dependabot uv update or equivalent verified update workflow changes `uv.lock` consistently with the manifest, and `uv lock --check` and locked CI pass.
- **Deferral justification:** This does not affect current local development or the ability to begin the route; address it before relying on automated dependency updates.

### BE-AUD-004 — Finite components can produce non-finite serialized magnitudes

- **Category:** Numerical integrity. **Priority:** Medium. **Resolution timing:** Next Section. **Effort:** Small.
- **Affected files / evidence:** `backend/src/voyager_tracker/schemas/spacecraft.py:10-31`; `backend/src/voyager_tracker/services/horizons.py:97-107`; `backend/tests/services/test_horizons.py:194-213`.
- **Relevant checklist requirement:** Section 4: reject invalid data and serialize derived distance and speed; section 5: return a valid response model.
- **Description and impact:** `allow_inf_nan=False` rejects non-finite input components, but does not validate computed fields. A synthetic state with two finite `1.7e308` position components produces infinite distance; `model_dump_json()` emits `null` for that field despite its declared float type. Such values are not plausible for this fixture, but an invalid upstream row can pass input validation and produce a misleading or schema-inconsistent response.
- **Corrective action:** Reject non-finite computed magnitudes at the validation boundary, or establish justified numerical limits that also prevent overflow; surface malformed upstream data explicitly.
- **Dependencies:** None.
- **Acceptance criteria:** Tests using finite overflowing position and velocity components fail explicitly, while ordinary fixture states retain finite serialized magnitudes.
- **Deferral justification:** No spacecraft route exists yet; implement and test this alongside its response serialization in section 5.

### BE-AUD-005 — README gives an incorrect backend setup picture

- **Category:** Documentation. **Priority:** Low. **Resolution timing:** Later Milestone. **Effort:** Small.
- **Affected files / evidence:** `README.md:5-7,71-78,115-124`; `backend/src/voyager_tracker/main.py:1-11`; `docs/03_checklists/00_backend_checklist.md:20-25`.
- **Relevant checklist requirement:** Section 1: working backend; section 13: update actual setup commands.
- **Description and impact:** The README says the application is not scaffolded, names `httpx` rather than `httpx2`, and uses `uvicorn app.main:app`, although the backend package is `voyager_tracker`. A reader following that startup command cannot import the documented application.
- **Corrective action:** Distinguish implemented backend features from planned frontend features and use the actual package and HTTP client names.
- **Dependencies:** None.
- **Acceptance criteria:** README startup instructions run from `backend/` and its status and stack descriptions match the implementation.
- **Deferral justification:** The backend checklist already contains the correct command; documentation cleanup can accompany section 13 or the next relevant README update.

### BE-AUD-006 — Fixture capture can replace a valid fixture with an unusable response

- **Category:** Test reliability. **Priority:** Low. **Resolution timing:** Later Milestone. **Effort:** Small.
- **Affected files / evidence:** `backend/scripts/capture_horizons_fixture.py:29-55`; `backend/tests/services/test_horizons.py:20-38`.
- **Relevant checklist requirement:** Section 3: save a representative response with query metadata; section 12: repeatable fixture-based tests.
- **Description and impact:** The capture script checks HTTP status and an API `error` field but does not validate the expected `result` table before overwriting the fixture. A success-shaped JSON payload without usable ephemeris data can replace the existing fixture; later tests will fail, but the script itself reports success.
- **Corrective action:** Validate the candidate report and expected sample rows before writing the fixture, preserving the existing file on validation failure.
- **Dependencies:** Existing parser/response validation can be reused where appropriate.
- **Acceptance criteria:** A mocked successful HTTP response with missing or malformed ephemeris causes an explicit failure and leaves a pre-existing fixture unchanged; a valid response remains capturable.
- **Deferral justification:** Fixture refresh is a deliberate manual operation and the script instructs reviewers to inspect its diff. Address during the section 12 verification milestone.

## 6. Scientific and Numerical Verification Assessment

The recorded query requests Voyager 1 (`-31`), Sun center (`500@10`), geometric ICRF vectors in km and km/s, with UT epochs. The fixture test checks both Julian dates, epochs and all six vector components (`backend/tests/services/test_horizons.py:28-64`); the documented 2026-11-26 comparison reports a match with fresh official text output (`docs/02_data_sources/00_data_sources.md:158-164`). The comparison verifies interpretation of this report, not independent trajectory accuracy.

`math.hypot` implements vector magnitudes; known 3–4–0 and 6–8–0 examples check the derived fields and serialization. Current queries round down to the hour and retain separate retrieval timestamps. Historical fixture epochs are UTC-aware, future UT is rejected, and an exclusive upper trajectory boundary is enforced. Future leap seconds and trajectory predictions remain inherent limitations.

The fixed metadata is not verified against every report, and arbitrary accepted query settings can invalidate labels (BE-AUD-001/002). Extremely large finite inputs can overflow computed magnitudes (BE-AUD-004). No independent SPICE or physical-trajectory cross-check was performed or required for this milestone. Exact floating-point comparisons are appropriate for the fixed decimal fixture; future approximate or independently calculated comparisons should use justified tolerances.

## 7. Testing and Quality Assessment

Tests are grouped by API, schemas and services, with recorded responses under `tests/fixtures/`. They cover health, vector magnitudes, response serialization, sample parsing, a mocked workflow, current-hour boundaries, future epoch rejection, malformed rows and tables, API errors, invalid JSON, HTTP status, timeout and connection errors. Local checks all passed as recorded in section 2.

Tests are independent of live NASA/JPL access, but successful parsing of the 2026 fixture requires a machine clock after that epoch. Mismatch cases and magnitude overflow need tests in BE-AUD-001/002/004. Route validation, HTTP error mapping and `/docs` for a spacecraft route belong to section 5; cache and partial-failure tests belong to later milestones. No coverage percentage was measured.

## 8. Technical Debt Assessment

The monolithic Horizons module separates request and parsing functions adequately for the present size; extracting more layers is not yet necessary. The fixed sample, sync HTTP client, no caching, and no shared client are reasonable current-stage decisions. Source/report convention validation and derived-value overflow are unintended gaps, not just style issues. The uv Dependabot mismatch can undermine future lockfile update automation. The capture script's overwrite risk and stale README are lower-impact maintenance debt.

Deferring future UT, Earth-relative calculations, additional spacecraft, retries, stale-data handling, shared clients, and route-level error mapping is intentional and consistent with the checklist. Deferral must not be interpreted as approval to expose unchecked scientific labels or non-finite response values.

## 9. Development Readiness Assessment

**READY WITH CONDITIONS.** The verified fixed-sample workflow and local tooling provide a sound basis to start section 5. No finding requires stopping before beginning it. Prefer to resolve BE-AUD-001, BE-AUD-002 and BE-AUD-003 first; at minimum, BE-AUD-001, BE-AUD-002 and BE-AUD-004 must be resolved and tested before the route exposes spacecraft data. Section 5 must also map existing transport and response errors to controlled HTTP responses, as already specified by the checklist.

## 10. Recommended Development Sequence

1. Enforce the fixed query conventions and validate response metadata (BE-AUD-001 and BE-AUD-002).
2. Select the uv Dependabot ecosystem and verify a reproducible update (BE-AUD-003).
3. Implement section 5 with finite output validation and mocked route/error tests (BE-AUD-004).
4. Update the README during the next relevant documentation or deployment pass (BE-AUD-005), and harden fixture refresh during section 12 (BE-AUD-006).
5. Continue the planned later milestones; retain the explicit future-UT limitation until its uncertainty can be represented.

## 11. Summary of Recommendations — Action Checklist

### 11.1 Required Before Proceeding

No findings were identified that block beginning section 5.

### 11.2 Recommended Before Proceeding

- [ ] **[BE-AUD-001] [High]** Enforce the query conventions required by Sun-relative km-labeled states and test incompatible parameters.
- [ ] **[BE-AUD-002] [High]** Validate returned target, origin, frame, units and correction before applying fixed response metadata.
- [ ] **[BE-AUD-003] [Medium]** Configure and verify Dependabot uv lockfile updates.

### 11.3 Address During the Next Checklist Section

- [ ] **[BE-AUD-004] [Medium]** Reject non-finite derived magnitudes and test overflowing finite components before exposing the route.

### 11.4 Deferred to Later Development Milestones

- [ ] **[BE-AUD-005] [Low]** Correct backend status, dependency and startup instructions in the README — section 13 or the next related documentation update.
- [ ] **[BE-AUD-006] [Low]** Validate captured reports before replacing the fixture — section 12.

### 11.5 Optional Improvements and Backlog

No findings were identified.
