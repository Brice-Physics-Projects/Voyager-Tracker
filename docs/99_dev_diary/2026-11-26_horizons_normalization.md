# 2026-11-26 — Horizons Normalization and Verification

## Goal

Finish section 4 of the backend checklist: turn Horizons reports into validated Voyager 1 states with clear provenance and verify the results against official output.

## Changes

- Recorded a representative Horizons JSON response with its query metadata and added fixture-based parsing and mocked service tests.
- Normalized sample epochs to timezone-aware UTC datetimes and rejected malformed tables, invalid rows, non-finite numbers, and unsupported epochs.
- Added a current-time query that requests the latest whole hour and the previous hour, returning the latest state without interpolation.
- Defined and populated a response model with the spacecraft, source, origin, frame, time scale, units, geometric correction, state, and retrieval time.
- Added explicit Horizons response errors while retaining distinct HTTP, connection, and timeout errors.
- Grouped backend tests by application area and configured Dependabot for Python dependencies and GitHub Actions.

## Decisions

- Preserve the fixed sample query for repeatable tests; use a separate query for current data.
- Reject future UT epochs until their time-scale uncertainty can be represented. Keep the current query within the conservative supported trajectory interval.
- Capture retrieval time when the response arrives, separately from the position epoch.
- Keep failure-to-HTTP-status mapping for the spacecraft route rather than adding it to the service.

## Problems and Solutions

- Horizons returns vector rows inside a text report in its JSON envelope. Extracted the marked table and parsed its CSV rows.
- Future UT conversions can depend on unknown leap seconds, and a future table did not necessarily show `UT~`. The service rejects future epochs rather than labeling them definitive UTC.
- Malformed upstream responses and transport failures need to be distinguishable. Added `HorizonsResponseError` for invalid reports and preserved the HTTP client's error types.

## Verification

- Compared both parsed fixture rows with a fresh Horizons API text response using the same sample query, changing only the output format. Both epochs, Julian dates, and all six vector components matched; the report confirmed the target, Sun origin, ICRF frame, geometric correction, units, and UT.
- Ran the current-time query against Horizons and confirmed it returned the latest whole-hour state.
- Ran backend tests, Ruff lint and formatting checks, and Pyright after section 4: 31 tests passed, with no lint, formatting, or type-check errors.

## Lessons Learned

- Position epoch and retrieval time are different: one identifies the modeled state, the other records when its report was received.
- A comparison with official Horizons output verifies parsing, not the physical accuracy of the trajectory.
- Future UT values require care even when the report does not visibly label a table `UT~`.

## Next Steps

- [ ] Expose a minimal Voyager 1 spacecraft route with the response model and controlled error responses.
- [ ] Test route validation, response serialization, and upstream failures without live NASA/JPL requests.
- [ ] Preserve the source time scale and uncertainty before supporting future epochs.
