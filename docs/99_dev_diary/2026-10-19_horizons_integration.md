# October 19, 2026 — Voyager 1 Horizons Integration

## Goal

Connect the Python backend to JPL Horizons, inspect a real Voyager 1 ephemeris response, and turn the response into reusable, validated spacecraft data.

## Changes

### Request the Horizons Report

Added the HTTP request workflow in `backend/src/voyager_tracker/services/horizons.py`, using `httpx` with an explicit timeout and HTTP status checking.

The request uses a fixed sample interval rather than the current execution time:

| Setting | Value |
| --- | --- |
| Target | Voyager 1, `-31` |
| Origin | Sun center, `500@10` |
| Ephemeris type | `VECTORS` |
| Sample interval | October 19, 2026, 00:00–01:00 UT |
| Step | One hour |
| Time scale | UT; the returned report identifies modern dates as UTC |
| Reference system and plane | ICRF, `FRAME` |
| Units | Kilometers and kilometers per second |
| Vector correction | `NONE`, geometric states |
| Vector table | Position and velocity components |
| Table format | CSV embedded inside the report text |

The API returns a JSON envelope containing a `result` string. That string holds the full Horizons text report, not an already parsed JSON table. The request function checks for an API-level error and the presence of an ephemeris table before returning the report.

### Extract the Ephemeris Rows

Added `extract_ephemeris_rows()` to isolate nonempty rows between the `$$SOE` and `$$EOE` markers. The function checks for both markers and excludes the surrounding explanatory text.

Confirmed that the sample request produces two rows, one for each requested epoch.

### Parse Named Values

Added `parse_ephemeris_row()` using Python's `csv` module. Each row contains:

```text
Julian date, calendar date, X, Y, Z, VX, VY, VZ,
```

Converted the numerical fields from strings, including scientific notation, into floating-point values. Retained the calendar epoch as source text for now.

The parser was subsequently updated to remove the empty field produced by the trailing comma, validate the expected eight fields, and return a structured model.

### Define the State Model

Added `SpacecraftState` in `backend/src/voyager_tracker/schemas/spacecraft.py`, using Pydantic's `BaseModel`.

Fields:

- `epoch_utc` and `julian_date`
- `x_km`, `y_km`, and `z_km`
- `vx_km_s`, `vy_km_s`, and `vz_km_s`

The model represents the specific Sun-relative, ICRF geometric states requested by this workflow. These conventions are currently documented rather than stored as individual model fields. Before generalizing the service to other origins or frames, make that metadata explicit.

### Calculate Distance and Speed

Used `math.hypot()` to calculate vector magnitudes:

```python
distance_km = hypot(x_km, y_km, z_km)
speed_km_s = hypot(vx_km_s, vy_km_s, vz_km_s)
```

Moved these calculations from the terminal execution block into model properties:

- `distance_from_sun_km`
- `speed_relative_to_sun_km_s`

These properties are accessed like attributes, without parentheses. Ordinary Python properties are not automatically included in Pydantic JSON serialization; the public API response still needs an explicit design.

### Connect the Workflow

Added `get_voyager_1_states()` to fetch the report, extract rows, and return a list of `SpacecraftState` instances.

The module's execution block now calls the reusable workflow and prints the epoch, distance, and speed. It executes only when the module is run directly:

```bash
uv run python -m voyager_tracker.services.horizons
```

## Decisions

- Use a fixed time interval while developing so outputs can be compared between changes.
- Inspect the source report before deciding how to parse it.
- Separate fetching, table extraction, row parsing, and display responsibilities.
- Use the standard-library CSV reader for the table rows.
- Use a Pydantic model to make field names and numerical types explicit.
- Keep terminal output as the initial verification path before introducing a spacecraft API endpoint.
- Keep Earth-relative distance and signal-delay calculations for a later step.

## Problems and Solutions

### JSON Did Not Mean Structured State Data

The outer response is JSON, but its `result` field contains a text report. Extracted the table markers first, then parsed the individual CSV rows.

### Trailing CSV Delimiter

Each data row ends with a comma, creating an extra empty field. Removed that final empty field before validating the eight expected values.

### Broad Dictionary Types

The first parser returned a dictionary typed as `dict[str, float | str]`. Replaced it with `SpacecraftState` so numerical components and the text epoch have individually defined types.

## Verification

Successfully ran the module against the live Horizons API and inspected the returned target, origin, frame, units, correction setting, and epochs.

Observed calculated output before the model refactor:

| Epoch (UTC) | Distance from Sun (km, rounded) | Sun-relative speed (km/s, rounded) |
| --- | --- | --- |
| 2026-10-19 00:00 | 25,744,686,544 | 16.918 |
| 2026-10-19 01:00 | 25,744,747,318 | 16.918 |

The change in rounded distance over the hour gives an average outward rate of approximately `16.882 km/s`. This is slightly below the total velocity magnitude, consistent with velocity also having a component perpendicular to the radial direction. This is a consistency check, not independent validation of the trajectory.

After the structured-model refactor, the workflow was acknowledged as working; a separate terminal transcript of that final version was not included in the session.

No automated tests were run or reported during this session.

## Lessons Learned

- Negative Cartesian coordinates indicate direction, not negative distance.
- Position-vector magnitude gives distance from the selected origin.
- Velocity-vector magnitude gives speed relative to that origin; it is not identical to radial recession speed.
- The position epoch and the time the API request is made are different concepts.
- Horizons positions are calculated ephemerides, not live spacecraft telemetry.
- The returned spacecraft notes describe a trajectory refit and extrapolation based on historical tracking data, distinguishing that history from onboard telemetry.
- Moving calculations into reusable model properties simplifies the execution block.
- Typed models help clarify the contract between parsing code and the rest of the application.

## Related Commit

`28dcb89` — `feat(horizons): fetch and parse Voyager 1 state vectors from JPL Horizons`

A PR title and description were drafted for the backend foundation and Horizons integration. PR creation or merging was not confirmed in this session.

## Next Steps

- [ ] Design an explicit public response schema with source, reference conventions, epoch, retrieval time, and calculated values.
- [ ] Normalize the source calendar epoch into a timestamp suitable for the API.
- [ ] Add a FastAPI spacecraft route using the reusable service workflow.
- [ ] Handle upstream failures with controlled API errors.
- [ ] Add fixture-based parsing checks and known-input calculation tests.
- [ ] Replace fixed sample dates with a deliberate current-time query strategy after preserving the reproducible sample for testing.
- [ ] Add Earth-relative distance before calculating Earth-to-spacecraft signal delay.
- [ ] Extend the verified workflow to Voyager 2.

## References

- [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
