from __future__ import annotations

from datetime import UTC, datetime, timedelta

from space_log_agent.tools.pre_hooks.tle_tools import derive_orbit_state, load_tle_records


def _normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_orbit_track(
    tle_path: str,
    start_utc: datetime,
    duration_minutes: int,
    step_seconds: int,
    ground_station_lat: float,
    ground_station_lon: float,
    visibility_threshold_km: float,
) -> list[dict[str, object]]:
    """Вычисляет 2D-трек (lat/lon) по TLE на заданном интервале времени."""
    start = _normalize_utc(start_utc)
    records, timescale = load_tle_records(tle_path)

    total_seconds = duration_minutes * 60
    points: list[dict[str, object]] = []

    for offset in range(0, total_seconds + 1, step_seconds):
        timestamp = start + timedelta(seconds=offset)
        orbit = derive_orbit_state(
            timestamp=timestamp,
            records=records,
            timescale=timescale,
            ground_station_lat=ground_station_lat,
            ground_station_lon=ground_station_lon,
            visibility_threshold_km=visibility_threshold_km,
        )

        points.append(
            {
                "timestamp_utc": timestamp,
                "lat_deg": float(orbit.orbit_lat or 0.0),
                "lon_deg": float(orbit.orbit_lon or 0.0),
                "altitude_km": float(orbit.orbit_altitude_km or 0.0),
                "is_eclipse": orbit.is_eclipse,
                "ground_station_visible": orbit.ground_station_visible,
            }
        )

    return points
