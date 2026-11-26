"""Capture the Voyager 1 Horizons sample response as a test fixture.

Run from ``backend/``:

    uv run python scripts/capture_horizons_fixture.py

The fixture stores the unmodified JSON response alongside the query that
produced it, so tests stay independent of live JPL availability. Re-run this
only when the sample query changes; review the diff before committing.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx2

from voyager_tracker.services.horizons import HORIZONS_URL, VOYAGER_1_SAMPLE_PARAMS

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "horizons"
    / "voyager_1_sun_vectors_2026-10-19.json"
)


def main() -> None:
    with httpx2.Client(timeout=30.0) as client:
        response = client.get(HORIZONS_URL, params=VOYAGER_1_SAMPLE_PARAMS)
        response.raise_for_status()

    payload = response.json()
    if payload.get("error"):
        raise SystemExit(f"Horizons returned an error: {payload['error']}")

    fixture = {
        "metadata": {
            "description": (
                "Voyager 1 (-31) Sun-centered geometric state vectors, ICRF, "
                "km and km/s, 2026-10-19 00:00-01:00 UT at 1 h steps."
            ),
            "url": HORIZONS_URL,
            "method": "GET",
            "params": VOYAGER_1_SAMPLE_PARAMS,
            "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "http_status": response.status_code,
            "secrets": "none; the Horizons API requires no credentials",
        },
        "response": payload,
    }

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
