# Voyager Tracker — Data Sources

This document records where application data comes from, how it is interpreted, and what has been verified. Update it when integrations or query conventions change. Use the development diary for chronological implementation history.

Last documented: October 19, 2026.

## Integration Status

| Source | Intended use | Status |
| --- | --- | --- |
| JPL Horizons | Calculated spacecraft positions and velocities | Voyager 1 fixed sample fetched and parsed successfully |
| NASA Image and Video Library | Historic mission images and metadata | Planned; response contract not yet verified in this project |
| NASA/JPL mission publications | Curated milestones and mission updates | Planned; no automated feed implemented |
| Planetary Data System (PDS) | Optional archival science data and images | Future exploration; no specific dataset selected |

## 1. JPL Horizons

### Purpose and Official References

Horizons supplies the calculated position and velocity data used by the initial backend workflow.

- [API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [System manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
- [Interactive interface](https://ssd.jpl.nasa.gov/horizons/app.html)
- Request endpoint: `https://ssd.jpl.nasa.gov/api/horizons.api`
- Request method used: `GET`

### Current Implementation

| Component | Location or function |
| --- | --- |
| Request and parsing service | `backend/src/voyager_tracker/services/horizons.py` |
| Parsed state model | `backend/src/voyager_tracker/schemas/spacecraft.py` |
| Fetch report | `fetch_voyager_1()` |
| Extract table | `extract_ephemeris_rows()` |
| Parse row | `parse_ephemeris_row()` |
| Combined workflow | `get_voyager_1_states()` |

The service currently uses fixed sample dates. It does not yet supply current-time positions through a spacecraft HTTP endpoint.

### Target Identifiers

| Spacecraft | Horizons identifier | Project verification |
| --- | --- | --- |
| Voyager 1 | `-31` | Confirmed by the returned report |
| Voyager 2 | `-32` | Planned; not yet queried in this project |

### Verified Sample Query

The following values match the successful Voyager 1 request. Quotes shown inside strings are part of the parameter values passed to Horizons; `httpx` handles URL encoding.

```python
params = {
    "format": "json",
    "COMMAND": "'-31'",
    "OBJ_DATA": "'YES'",
    "MAKE_EPHEM": "'YES'",
    "EPHEM_TYPE": "'VECTORS'",
    "CENTER": "'500@10'",
    "START_TIME": "'2026-10-19 00:00'",
    "STOP_TIME": "'2026-10-19 01:00'",
    "STEP_SIZE": "'1 h'",
    "TIME_TYPE": "'UT'",
    "REF_SYSTEM": "'ICRF'",
    "REF_PLANE": "'FRAME'",
    "OUT_UNITS": "'KM-S'",
    "VEC_CORR": "'NONE'",
    "VEC_TABLE": "'2'",
    "CSV_FORMAT": "'YES'",
}
```

| Setting | Interpretation |
| --- | --- |
| `CENTER='500@10'` | Origin at the center of the Sun |
| `EPHEM_TYPE='VECTORS'` | Cartesian state vectors |
| `REF_SYSTEM='ICRF'`, `REF_PLANE='FRAME'` | Components expressed along the ICRF frame axes |
| `OUT_UNITS='KM-S'` | Positions in km and velocity components in km/s |
| `VEC_CORR='NONE'` | Geometric states with no light-time or aberration correction applied |
| `VEC_TABLE='2'` | Position and velocity components |
| `TIME_TYPE='UT'` | Reported UT times; the returned report identifies dates after 1962 as UTC |
| Sample interval | Two output epochs, one hour apart |

Changing these settings changes the meaning of the values. Preserve the query configuration alongside any stored response fixtures.

### Response Structure

The HTTP response is a JSON envelope. Its `result` value contains a text report, including metadata, a CSV-style table, and explanatory notes. JSON output does not mean the vector rows are separate JSON objects.

The data table is bounded by:

```text
$$SOE
...data rows...
$$EOE
```

Each row in the current format contains:

| Index | Source column | Application field | Meaning / units |
| --- | --- | --- | --- |
| 0 | `JDUT` | `julian_date` | Julian day value on the requested UT time scale |
| 1 | Calendar Date (UT) | `epoch_utc` | Calendar epoch retained as source text |
| 2 | `X` | `x_km` | X position component, km |
| 3 | `Y` | `y_km` | Y position component, km |
| 4 | `Z` | `z_km` | Z position component, km |
| 5 | `VX` | `vx_km_s` | X velocity component, km/s |
| 6 | `VY` | `vy_km_s` | Y velocity component, km/s |
| 7 | `VZ` | `vz_km_s` | Z velocity component, km/s |

Rows end with a trailing comma. The parser removes the resulting final empty field before checking for eight fields. Numerical strings, including scientific notation, are converted to floats. The epoch remains a string such as `A.D. 2026-Oct-19 00:00:00.0000`; timestamp normalization is pending.

### Derived Quantities

Distance from the selected origin:

```python
distance_from_sun_km = hypot(x_km, y_km, z_km)
```

Speed relative to the selected origin:

```python
speed_relative_to_sun_km_s = hypot(vx_km_s, vy_km_s, vz_km_s)
```

These names are valid because the current query is Sun-centered. They must not be reused unchanged for a query with another origin.

Negative components indicate direction along an axis. Vector magnitudes are nonnegative. Total speed is different from radial recession speed, which measures only the velocity component along the position vector.

The model currently exposes these magnitudes as ordinary Python properties. They are not automatically included in Pydantic JSON serialization. A public response schema must explicitly expose the intended calculated values.

### Observed Sample Results

| Epoch (UTC) | Sun-relative distance (km, rounded) | Sun-relative speed (km/s, rounded) |
| --- | --- | --- |
| 2026-10-19 00:00 | 25,744,686,544 | 16.918 |
| 2026-10-19 01:00 | 25,744,747,318 | 16.918 |

These are recorded development outputs, not current-position values or an independent validation dataset. Keep full numerical precision internally and round only for display.

### Time and Provenance

Keep the following distinct:

- **Position epoch:** The instant represented by a state vector.
- **Retrieval time:** When the application obtained the report.
- **Trajectory revision:** The source model/version described in the report.
- **Cache age:** Time elapsed since the successful retrieval.

The report's `Revised: Aug 19, 2022` heading is not the position epoch. The verified report identifies the trajectory source as `Voyager_1_ST+refit2022_m` and describes a 2022 refit of historical tracking data followed by extrapolation. It explicitly distinguishes that tracking history from onboard telemetry.

The current parsed state model does not yet carry retrieval time, reference metadata, or trajectory provenance as fields. Add these to the service result/public response before presenting the application as a current tracker.

### Limitations

- Positions are calculated ephemerides, not direct live telemetry measurements.
- The sample query remains fixed even when the program is run later.
- Sun-relative distance is not distance from Earth.
- Geometric states do not include signal propagation corrections.
- Query success does not establish the accuracy of the underlying trajectory prediction.
- Future time conversions can be affected by unknown leap seconds; consult the report's time notes when selecting a long-range strategy.
- The report contains background mission notes; do not treat every historical statement there as a separately verified timeline entry.

### Error Handling and Verification

Currently implemented checks include an HTTP timeout, HTTP status checking, an API-level `error` check, table-marker checks, expected field count, and numerical/model conversion.

Before exposing the service publicly:

- [ ] Add controlled handling for timeouts, invalid JSON, API errors, missing or malformed rows, and unsupported targets.
- [ ] Verify the reported target, origin, frame, units, and dates against the requested configuration.
- [ ] Add parsing tests using recorded response fixtures.
- [ ] Add known-input checks for vector magnitudes.
- [ ] Define how empty results and partial failures are represented.
- [ ] Compare selected values with the same query parameters in the official interface.

## 2. Planned Earth-Relative Distance and Signal Delay

This integration has not been implemented. Define the Earth-centered origin, reference frame, epoch, and correction convention before requesting or deriving the values.

For an educational geometric approximation:

```python
one_way_seconds = earth_distance_km / 299_792.458
round_trip_seconds = 2 * one_way_seconds
```

Use Earth-relative distance, not the existing Sun-relative distance. Label the approximation: it ignores motion during signal travel and spacecraft/ground processing or scheduling delays. If Horizons-provided light time is used instead, document its convention and avoid applying corrections twice.

## 3. NASA Image and Video Library — Planned

- [Official library](https://images.nasa.gov/)
- Candidate API request: `https://images-api.nasa.gov/search?q=voyager&media_type=image`
- Purpose: Historic mission images with descriptive metadata and source attribution.

No image response or asset-resolution workflow has been verified in this project yet. The URL above is a starting point, not a completed integration contract.

Before implementation:

- [ ] Verify the current official API documentation and access requirements.
- [ ] Inspect search results, pagination, asset references, and available image sizes.
- [ ] Distinguish images taken by Voyager from images depicting the spacecraft or unrelated search matches.
- [ ] Define a curated selection or search-filtering strategy.
- [ ] Preserve source identifiers, titles, descriptions, dates, credits, and source links where available.
- [ ] Check individual asset rights and current usage policies.
- [ ] Decide how to handle absent metadata, broken URLs, and unavailable results.

Do not infer that a library asset's date is necessarily the original image-capture date without checking its metadata meaning. Render upstream descriptions as untrusted text rather than raw HTML.

## 4. NASA/JPL Mission Publications — Planned

- [NASA Voyager mission page](https://science.nasa.gov/mission/voyager/)
- Purpose: Manually curated milestones, mission context, and dated status updates.

The project will not scrape mission webpages. No automated status API has been verified. Curated entries should preserve:

| Field | Purpose |
| --- | --- |
| Spacecraft | Identify Voyager 1, Voyager 2, or both |
| Event date | When the milestone occurred |
| Publication date, when relevant | When a status statement was published |
| Title and summary | Explain the event in original wording |
| Source URL | Let readers verify the statement |
| Last reviewed date | Record the project's verification date |

Historical and current health statements must be dated. Do not imply that a curated update represents continuous monitoring. Power, signal strength, and subsystem telemetry remain outside the MVP without a verified appropriate source.

## 5. Planetary Data System — Future Exploration

- [Official PDS portal](https://pds.nasa.gov/)
- Intended use: Optional links to archival Voyager science and image products.

No dataset, collection, product format, or access endpoint has been selected. PDS is an archive ecosystem, not an assumed single application-ready Voyager API. Record the exact collection, identifiers, documentation, calibration level, units, and access method before integrating a product.

## 6. Shared Data-Handling Policy

### Caching

Caching is planned, not implemented. Begin with a configurable in-memory cache and define:

- Cache keys that include target, origin, epoch selection, frame, units, and correction settings.
- Separate expiration policies for position data, image metadata, and curated material.
- Original retrieval timestamps and a maximum acceptable stale age.
- Explicit stale-data flags and behavior when no valid cached result exists.

A cache hit must not replace the original retrieval timestamp with the current time. In-memory caches reset on restart and are not automatically shared between workers. Verify current service usage guidance before choosing request frequency; no specific rate limit is assumed here.

### Attribution and Rights

Identify NASA/JPL and the applicable data source without suggesting endorsement. Preserve asset-specific credits and verify usage conditions rather than applying a blanket public-domain label to every image or archive product.

### Public Response Metadata

The future spacecraft response should make these conventions explicit:

- Spacecraft identity and source.
- Position epoch with time scale.
- Retrieval timestamp.
- Reference origin and frame.
- Position and velocity units.
- Geometric versus corrected state convention.
- Whether results are stale or interpolated.
- Relevant trajectory provenance where practical.

### Documentation Maintenance

Update this file when a source is verified, query conventions change, metadata is added, or an integration is implemented. Record the reason and implementation details in the corresponding dated development diary entry. Source availability and API behavior should be checked against current official documentation during implementation.
