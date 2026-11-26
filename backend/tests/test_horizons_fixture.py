import json
from pathlib import Path

from voyager_tracker.services.horizons import (
    HORIZONS_URL,
    VOYAGER_1_SAMPLE_PARAMS,
    extract_ephemeris_rows,
    parse_ephemeris_row,
)


def test_recorded_voyager_1_response():
    path = (
        Path(__file__).parent
        / "fixtures"
        / "horizons"
        / "voyager_1_sun_vectors_2026-10-19.json"
    )
    fixture = json.loads(path.read_text(encoding="utf-8"))

    assert fixture["metadata"]["url"] == HORIZONS_URL
    assert fixture["metadata"]["method"] == "GET"
    assert fixture["metadata"]["params"] == VOYAGER_1_SAMPLE_PARAMS
    assert fixture["metadata"]["http_status"] == 200
    assert fixture["response"]["signature"]["source"] == "NASA/JPL Horizons API"

    rows = extract_ephemeris_rows(fixture["response"]["result"])
    states = [parse_ephemeris_row(row) for row in rows]
    assert len(states) == 2
    assert states[0].epoch_utc == "A.D. 2026-Oct-19 00:00:00.0000"
    assert states[0].x_km == -4.814738849405165e9
    assert states[0].vx_km_s == -2.069749408670841
    assert states[1].epoch_utc == "A.D. 2026-Oct-19 01:00:00.0000"
