import csv
from datetime import UTC, datetime, timedelta
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


def fetch_voyager_1(params: dict[str, str] | None = None) -> str:
    """Fetch Voyager 1's Sun-relative state vectors."""
    with httpx2.Client(timeout=30.0) as client:
        response = client.get(
            HORIZONS_URL, params=VOYAGER_1_SAMPLE_PARAMS if params is None else params
        )
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

    if "UT~" in result.split("$$SOE", 1)[0]:
        raise RuntimeError("Horizons returned uncertain UT~ epochs, not confirmed UTC.")

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


def get_voyager_1_states(
    params: dict[str, str] | None = None,
) -> list[SpacecraftState]:
    """Fetch and parse Voyager 1 states, defaulting to the fixed sample."""
    if params is not None and params.get("TIME_TYPE") != "'UT'":
        raise ValueError("Voyager 1 state parsing requires UT epochs.")
    report = fetch_voyager_1(params)
    rows = extract_ephemeris_rows(report)
    states = [parse_ephemeris_row(row) for row in rows]
    now = datetime.now(UTC)
    if any(
        not datetime(1972, 1, 1, tzinfo=UTC) <= state.epoch_utc <= now
        for state in states
    ):
        raise ValueError(
            "UT epochs before 1972 or in the future cannot be assumed UTC."
        )
    return states


def current_voyager_1_params(now: datetime) -> dict[str, str]:
    """Request two hourly epochs ending at the most recent UTC hour."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Current time must be timezone-aware.")
    end = now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    if start < datetime(1981, 1, 1, tzinfo=UTC) or end >= datetime(
        2100, 1, 1, tzinfo=UTC
    ):
        raise ValueError("Current time is outside the supported Voyager 1 interval.")
    return {
        **VOYAGER_1_SAMPLE_PARAMS,
        "START_TIME": start.strftime("'%Y-%m-%d %H:%M'"),
        "STOP_TIME": end.strftime("'%Y-%m-%d %H:%M'"),
    }


def get_current_voyager_1_state() -> SpacecraftState:
    """Fetch the most recent whole-hour Voyager 1 state, without interpolation."""
    params = current_voyager_1_params(datetime.now(UTC))
    states = get_voyager_1_states(params)
    expected = datetime.strptime(params["STOP_TIME"], "'%Y-%m-%d %H:%M'").replace(
        tzinfo=UTC
    )
    if (
        len(states) != 2
        or states[0].epoch_utc != expected - timedelta(hours=1)
        or states[1].epoch_utc != expected
    ):
        raise ValueError("Horizons returned unexpected current-time epochs.")
    return states[-1]


if __name__ == "__main__":
    for state in get_voyager_1_states():
        print(f"Epoch: {state.epoch_utc}")
        print(f"Distance from Sun: {state.distance_from_sun_km:,.0f} km")
        print(f"Speed relative to Sun: {state.speed_relative_to_sun_km_s:.3f} km/s")
        print()
