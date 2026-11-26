from math import hypot
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, computed_field


class SpacecraftState(BaseModel):
    """One Sun-relative geometric state in the ICRF frame."""

    model_config = ConfigDict(allow_inf_nan=False)

    epoch_utc: AwareDatetime
    julian_date: float

    x_km: float
    y_km: float
    z_km: float

    vx_km_s: float
    vy_km_s: float
    vz_km_s: float

    @computed_field
    @property
    def distance_from_sun_km(self) -> float:
        return hypot(self.x_km, self.y_km, self.z_km)

    @computed_field
    @property
    def speed_relative_to_sun_km_s(self) -> float:
        return hypot(self.vx_km_s, self.vy_km_s, self.vz_km_s)


class SpacecraftResponse(BaseModel):
    """Public contract for a geometric Voyager 1 state from JPL Horizons."""

    spacecraft: Literal["Voyager 1"]
    source: Literal["NASA/JPL Horizons"]
    origin: Literal["Sun"]
    frame: Literal["ICRF"]
    time_scale: Literal["UTC"]
    position_unit: Literal["km"]
    velocity_unit: Literal["km/s"]
    correction: Literal["geometric"]
    retrieved_at_utc: AwareDatetime
    state: SpacecraftState
