from voyager_tracker.schemas.spacecraft import SpacecraftState


def make_state() -> SpacecraftState:
    # 3-4-0 and 6-8-0 triangles give exact magnitudes of 5 and 10.
    return SpacecraftState(
        epoch_utc="A.D. 2026-Oct-19 00:00:00.0000",
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
