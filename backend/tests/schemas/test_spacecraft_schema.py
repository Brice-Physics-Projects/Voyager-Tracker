from datetime import UTC, datetime

from voyager_tracker.schemas.spacecraft import SpacecraftResponse, SpacecraftState


def make_state() -> SpacecraftState:
    # 3-4-0 and 6-8-0 triangles give exact magnitudes of 5 and 10.
    return SpacecraftState(
        epoch_utc=datetime(2026, 10, 19, tzinfo=UTC),
        julian_date=2461332.5,
        x_km=3.0,
        y_km=4.0,
        z_km=0.0,
        vx_km_s=6.0,
        vy_km_s=8.0,
        vz_km_s=0.0,
    )


def test_distance_and_speed_are_vector_magnitudes():
    state = make_state()

    assert state.distance_from_sun_km == 5.0
    assert state.speed_relative_to_sun_km_s == 10.0


def test_derived_values_are_serialized():
    dumped = make_state().model_dump()

    assert dumped["distance_from_sun_km"] == 5.0
    assert dumped["speed_relative_to_sun_km_s"] == 10.0


def test_spacecraft_response_exposes_provenance_and_state():
    response = SpacecraftResponse(
        spacecraft="Voyager 1",
        source="NASA/JPL Horizons",
        origin="Sun",
        frame="ICRF",
        time_scale="UTC",
        position_unit="km",
        velocity_unit="km/s",
        correction="geometric",
        retrieved_at_utc=datetime(2026, 10, 19, 2, tzinfo=UTC),
        state=make_state(),
    )
    serialized = response.model_dump(mode="json")

    assert serialized["spacecraft"] == "Voyager 1"
    assert serialized["source"] == "NASA/JPL Horizons"
    assert serialized["origin"] == "Sun"
    assert serialized["frame"] == "ICRF"
    assert serialized["time_scale"] == "UTC"
    assert serialized["position_unit"] == "km"
    assert serialized["velocity_unit"] == "km/s"
    assert serialized["correction"] == "geometric"
    assert serialized["retrieved_at_utc"] == "2026-10-19T02:00:00Z"
    assert serialized["state"]["epoch_utc"] == "2026-10-19T00:00:00Z"
    assert serialized["state"]["distance_from_sun_km"] == 5.0
    assert serialized["state"]["speed_relative_to_sun_km_s"] == 10.0
