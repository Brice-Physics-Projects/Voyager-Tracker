import csv
from datetime import UTC, datetime
from typing import Final, cast

import httpx2

from voyager_tracker.schemas.spacecraft import SpacecraftState

HORIZONS_URL: Final = "https://ssd.jpl.nasa.gov/api/horizons.api"

# Fixed sample query: Voyager 1, Sun-centered geometric ICRF state vectors.
VOYAGER_1_SAMPLE_PARAMS: Final[dict[str, str]] = {
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


def fetch_voyager_1() -> str:
    """Fetch a small sample of Voyager 1's Sun-relative state vectors."""
    with httpx2.Client(timeout=30.0) as client:
        response = client.get(HORIZONS_URL, params=VOYAGER_1_SAMPLE_PARAMS)
        response.raise_for_status()

    payload: object = response.json()

    if not isinstance(payload, dict):
        raise RuntimeError("Horizons returned an invalid response envelope.")

    envelope = cast("dict[str, object]", payload)
    if envelope.get("error"):
        raise RuntimeError(f"Horizons error: {envelope['error']}")

    result = envelope.get("result")

    if not isinstance(result, str) or "$$SOE" not in result:
        raise RuntimeError("Horizons did not return an ephemeris table.")

    return result


def extract_ephemeris_rows(report: str) -> list[str]:
    """Extract nonempty data rows between Horizons' table markers."""
    if "$$SOE" not in report or "$$EOE" not in report:
        raise ValueError("The report is missing ephemeris table markers.")

    table, end_marker, _ = report.split("$$SOE", 1)[1].partition("$$EOE")
    if not end_marker:
        raise ValueError("The ephemeris table markers are out of order.")

    rows = [line.strip() for line in table.splitlines() if line.strip()]
    if not rows:
        raise ValueError("The ephemeris table is empty.")
    return rows


def parse_ephemeris_row(row: str) -> SpacecraftState:
    """Convert a row from the fixed sample, whose UT epochs are known UTC."""
    fields = next(csv.reader([row], skipinitialspace=True), list[str]())

    # Horizons includes an empty field after the trailing comma.
    if fields and not fields[-1].strip():
        fields.pop()

    if len(fields) != 8:
        raise ValueError(f"Expected 8 ephemeris fields, received {len(fields)}.")

    return SpacecraftState(
        julian_date=float(fields[0]),
        epoch_utc=datetime.strptime(
            fields[1].strip(), "A.D. %Y-%b-%d %H:%M:%S.%f"
        ).replace(tzinfo=UTC),
        x_km=float(fields[2]),
        y_km=float(fields[3]),
        z_km=float(fields[4]),
        vx_km_s=float(fields[5]),
        vy_km_s=float(fields[6]),
        vz_km_s=float(fields[7]),
    )


def get_voyager_1_states() -> list[SpacecraftState]:
    """Fetch and parse the configured Voyager 1 sample."""
    report = fetch_voyager_1()
    rows = extract_ephemeris_rows(report)

    return [parse_ephemeris_row(row) for row in rows]


if __name__ == "__main__":
    for state in get_voyager_1_states():
        print(f"Epoch: {state.epoch_utc}")
        print(f"Distance from Sun: {state.distance_from_sun_km:,.0f} km")
        print(f"Speed relative to Sun: {state.speed_relative_to_sun_km_s:.3f} km/s")
        print()
