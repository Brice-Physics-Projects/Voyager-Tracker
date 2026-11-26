import json
from datetime import UTC, datetime
from pathlib import Path

import httpx2
import pytest

from voyager_tracker.services import horizons
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
    assert states[0].epoch_utc == datetime(2026, 10, 19, tzinfo=UTC)
    assert states[0].x_km == -4.814738849405165e9
    assert states[0].vx_km_s == -2.069749408670841
    assert states[1].epoch_utc == datetime(2026, 10, 19, 1, tzinfo=UTC)
    assert states[0].model_dump(mode="json")["epoch_utc"] == "2026-10-19T00:00:00Z"


@pytest.mark.parametrize(
    ("row", "error"),
    [
        ("", "Expected 8 ephemeris fields"),
        ("2461332.5, A.D. 2026-Oct-19 00:00:00.0000, 1", "Expected 8"),
        ("2461332.5, invalid, 1, 2, 3, 4, 5, 6,", "does not match format"),
        (
            "2461332.5, A.D. 2026-Oct-19 00:00:00.0000, invalid, 2, 3, 4, 5, 6,",
            "could not convert string to float",
        ),
        (
            "2461332.5, A.D. 2026-Oct-19 00:00:00.0000, nan, 2, 3, 4, 5, 6,",
            "finite number",
        ),
        ("inf, A.D. 2026-Oct-19 00:00:00.0000, 1, 2, 3, 4, 5, 6,", "finite number"),
    ],
)
def test_invalid_rows_are_rejected(row, error):
    with pytest.raises(ValueError, match=error):
        parse_ephemeris_row(row)


@pytest.mark.parametrize(
    ("report", "error"),
    [
        ("", "missing ephemeris table markers"),
        ("$$EOE\n$$SOE", "markers are out of order"),
        ("$$SOE\n$$EOE", "table is empty"),
    ],
)
def test_invalid_tables_are_rejected(report, error):
    with pytest.raises(ValueError, match=error):
        extract_ephemeris_rows(report)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"error": "invalid query"}, "Horizons error: invalid query"),
        ([], "invalid response envelope"),
        ({"result": "no ephemeris"}, "did not return an ephemeris table"),
    ],
)
def test_invalid_response_is_rejected(monkeypatch, payload, error):
    client = httpx2.Client
    transport = httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
    monkeypatch.setattr(
        horizons.httpx2,
        "Client",
        lambda **kwargs: client(transport=transport, **kwargs),
    )

    with pytest.raises(RuntimeError, match=error):
        horizons.fetch_voyager_1()
