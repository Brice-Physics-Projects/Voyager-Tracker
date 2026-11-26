import json
from datetime import UTC, datetime, timedelta, timezone
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


@pytest.fixture
def horizons_fixture():
    path = (
        Path(__file__).parents[1]
        / "fixtures"
        / "horizons"
        / "voyager_1_sun_vectors_2026-10-19.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_recorded_voyager_1_response(horizons_fixture):
    fixture = horizons_fixture
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


def test_voyager_1_workflow_with_recorded_response(monkeypatch, horizons_fixture):
    fixture = horizons_fixture

    def respond(request):
        assert str(request.url.copy_with(query=None)) == fixture["metadata"]["url"]
        assert request.method == fixture["metadata"]["method"]
        assert dict(request.url.params) == fixture["metadata"]["params"]
        return httpx2.Response(200, json=fixture["response"])

    client = httpx2.Client
    transport = httpx2.MockTransport(respond)
    monkeypatch.setattr(
        horizons.httpx2,
        "Client",
        lambda **kwargs: client(transport=transport, **kwargs),
    )
    states = horizons.get_voyager_1_states()
    assert len(states) == 2
    assert states[0].epoch_utc == datetime(2026, 10, 19, tzinfo=UTC)
    assert states[0].x_km == -4.814738849405165e9
    assert states[1].epoch_utc == datetime(2026, 10, 19, 1, tzinfo=UTC)
    monkeypatch.setattr(
        horizons, "current_voyager_1_params", lambda now: VOYAGER_1_SAMPLE_PARAMS
    )
    assert horizons.get_current_voyager_1_state() == states[-1]


def test_current_query_rounds_down_and_respects_supported_interval():
    params = horizons.current_voyager_1_params(
        datetime(2026, 11, 26, 0, 24, tzinfo=UTC)
    )
    assert params["START_TIME"] == "'2026-11-25 23:00'"
    assert params["STOP_TIME"] == "'2026-11-26 00:00'"
    assert params["TIME_TYPE"] == "'UT'"
    assert VOYAGER_1_SAMPLE_PARAMS["START_TIME"] == "'2026-10-19 00:00'"
    offset_now = datetime(2026, 11, 25, 19, 24, tzinfo=timezone(-timedelta(hours=5)))
    assert horizons.current_voyager_1_params(offset_now) == params

    for now in (
        datetime(1981, 1, 1, tzinfo=UTC),
        datetime(2100, 1, 1, tzinfo=UTC),
    ):
        with pytest.raises(ValueError, match="outside the supported"):
            horizons.current_voyager_1_params(now)
    with pytest.raises(ValueError, match="timezone-aware"):
        horizons.current_voyager_1_params(datetime(2026, 11, 26))


def test_future_epochs_are_rejected(monkeypatch):
    epoch = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%b-%d %H:%M:%S.%f")
    row = f"2462502.5, A.D. {epoch}, 1, 2, 3, 4, 5, 6,"
    monkeypatch.setattr(
        horizons, "fetch_voyager_1", lambda params: f"$$SOE\n{row}\n$$EOE"
    )
    with pytest.raises(ValueError, match="in the future"):
        horizons.get_voyager_1_states()

    with pytest.raises(ValueError, match="requires UT epochs"):
        horizons.get_voyager_1_states({**VOYAGER_1_SAMPLE_PARAMS, "TIME_TYPE": "'TDB'"})


def test_current_query_rejects_unexpected_epochs(monkeypatch):
    monkeypatch.setattr(
        horizons, "current_voyager_1_params", lambda now: VOYAGER_1_SAMPLE_PARAMS
    )
    monkeypatch.setattr(horizons, "get_voyager_1_states", lambda params: [])
    with pytest.raises(ValueError, match="unexpected current-time epochs"):
        horizons.get_current_voyager_1_state()


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


@pytest.mark.parametrize(
    ("response", "error", "message"),
    [
        (httpx2.Response(200, text="not JSON"), RuntimeError, "invalid JSON"),
        (httpx2.Response(503), httpx2.HTTPStatusError, "503"),
    ],
)
def test_http_and_json_errors_are_reported(monkeypatch, response, error, message):
    client = httpx2.Client
    transport = httpx2.MockTransport(lambda request: response)
    monkeypatch.setattr(
        horizons.httpx2,
        "Client",
        lambda **kwargs: client(transport=transport, **kwargs),
    )

    with pytest.raises(error, match=message):
        horizons.fetch_voyager_1()


def test_timeout_is_reported(monkeypatch):
    client = httpx2.Client

    def timeout(request):
        raise httpx2.ReadTimeout("Horizons timed out", request=request)

    transport = httpx2.MockTransport(timeout)
    monkeypatch.setattr(
        horizons.httpx2,
        "Client",
        lambda **kwargs: client(transport=transport, **kwargs),
    )

    with pytest.raises(httpx2.ReadTimeout, match="Horizons timed out"):
        horizons.fetch_voyager_1()
