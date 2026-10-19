import httpx
import csv
from voyager_tracker.schemas.spacecraft import SpacecraftState

HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"


def fetch_voyager_1() -> str:
    """Fetch a small sample of Voyager 1's Sun-relative state vectors."""
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

    with httpx.Client(timeout=30.0) as client:
        response = client.get(HORIZONS_URL, params=params)
        response.raise_for_status()

    payload = response.json()

    if payload.get("error"):
        raise RuntimeError(f"Horizons error: {payload['error']}")

    result = payload.get("result")

    if not isinstance(result, str) or "$$SOE" not in result:
        raise RuntimeError("Horizons did not return an ephemeris table.")

    return result

def extract_ephemeris_rows(report: str) -> list[str]:
    """Extract nonempty data rows between Horizons' table markers."""
    if "$$SOE" not in report or "$$EOE" not in report:
        raise ValueError("The report is missing ephemeris table markers.")

    table = report.split("$$SOE", 1)[1].split("$$EOE", 1)[0]

    return [
        line.strip()
        for line in table.splitlines()
        if line.strip()
    ]

def parse_ephemeris_row(row: str) -> SpacecraftState:
    """Convert one Horizons CSV row into a validated spacecraft state."""
    fields = next(csv.reader([row], skipinitialspace=True))

    # Horizons includes an empty field after the trailing comma.
    if fields and not fields[-1].strip():
        fields.pop()

    if len(fields) != 8:
        raise ValueError(
            f"Expected 8 ephemeris fields, received {len(fields)}."
        )

    return SpacecraftState(
        julian_date=float(fields[0]),
        epoch_utc=fields[1].strip(),
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
        print(
            f"Distance from Sun: "
            f"{state.distance_from_sun_km:,.0f} km"
        )
        print(
            f"Speed relative to Sun: "
            f"{state.speed_relative_to_sun_km_s:.3f} km/s"
        )
        print()
