from math import hypot

from pydantic import BaseModel


class SpacecraftState(BaseModel):
    """One Sun-relative geometric state in the ICRF frame."""

    epoch_utc: str
    julian_date: float

    x_km: float
    y_km: float
    z_km: float

    vx_km_s: float
    vy_km_s: float
    vz_km_s: float

    @property
    def distance_from_sun_km(self) -> float:
        return hypot(self.x_km, self.y_km, self.z_km)

    @property
    def speed_relative_to_sun_km_s(self) -> float:
        return hypot(self.vx_km_s, self.vy_km_s, self.vz_km_s)
