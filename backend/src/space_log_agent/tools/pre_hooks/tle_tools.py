from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import asin, atan2, cos, radians, sin, sqrt

from loguru import logger
from skyfield.api import EarthSatellite, load

from space_log_agent.models import OrbitContext


@dataclass(slots=True)
class TLERecord:
    line1: str
    line2: str
    epoch: datetime
    satellite: EarthSatellite


def load_tle_records(tle_path: str) -> tuple[list[TLERecord], object]:
    """Парсит TLE и возвращает список записей, отсортированный по epoch."""
    logger.debug("Загрузка TLE из {}", tle_path)
    timescale = load.timescale()

    with open(tle_path, "r", encoding="utf-8") as file:
        raw_lines = [line.strip() for line in file if line.strip()]

    records: list[TLERecord] = []
    index = 0
    while index < len(raw_lines) - 1:
        line1 = raw_lines[index]
        line2 = raw_lines[index + 1]

        if line1.startswith("1 ") and line2.startswith("2 "):
            satellite = EarthSatellite(line1, line2, "OPS-SAT", timescale)
            epoch = satellite.epoch.utc_datetime().replace(tzinfo=UTC)
            records.append(TLERecord(line1=line1, line2=line2, epoch=epoch, satellite=satellite))
            index += 2
            continue

        index += 1

    if not records:
        raise ValueError("Не удалось распарсить ни одной TLE записи")

    records.sort(key=lambda record: record.epoch)
    logger.debug("Загружено TLE записей: {}", len(records))
    return records, timescale


def select_tle_for_timestamp(records: list[TLERecord], timestamp: datetime) -> TLERecord:
    """Выбирает последний TLE, чей epoch <= timestamp."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)

    chosen = records[0]
    for record in records:
        if record.epoch <= timestamp:
            chosen = record
        else:
            break
    return chosen


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))


def _estimate_sun_exposure(timestamp: datetime, orbit_lon: float) -> bool:
    """Грубая модель освещенности по локальному солнечному времени орбиты."""
    utc_hour = timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600
    local_solar_hour = (utc_hour + orbit_lon / 15.0) % 24.0
    return 6.0 <= local_solar_hour < 18.0


def detect_eclipse(timestamp: datetime, orbit_lon: float) -> bool:
    """Определяет, находится ли КА в тени Земли (грубая оценка)."""
    return not _estimate_sun_exposure(timestamp, orbit_lon)


def compute_ground_station_visibility(
    orbit_lat: float,
    orbit_lon: float,
    ground_station_lat: float,
    ground_station_lon: float,
    visibility_threshold_km: float,
) -> tuple[bool, float]:
    """Оценивает видимость станции по дистанции до подспутниковой точки."""
    distance_to_station = _haversine_km(orbit_lat, orbit_lon, ground_station_lat, ground_station_lon)
    return distance_to_station <= visibility_threshold_km, distance_to_station


def derive_orbit_state(
    timestamp: datetime,
    records: list[TLERecord],
    timescale: object,
    ground_station_lat: float,
    ground_station_lon: float,
    visibility_threshold_km: float,
) -> OrbitContext:
    """Вычисляет положение КА и орбитальный контекст по выбранному TLE."""
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)

    tle = select_tle_for_timestamp(records, timestamp)
    time_value = timescale.from_datetime(timestamp)

    geocentric = tle.satellite.at(time_value)
    subpoint = geocentric.subpoint()

    lat = float(subpoint.latitude.degrees)
    lon = float(subpoint.longitude.degrees)
    alt = float(subpoint.elevation.km)

    station_visible, distance_to_station = compute_ground_station_visibility(
        orbit_lat=lat,
        orbit_lon=lon,
        ground_station_lat=ground_station_lat,
        ground_station_lon=ground_station_lon,
        visibility_threshold_km=visibility_threshold_km,
    )

    mean_motion = tle.satellite.model.no_kozai * 1440.0 / (2.0 * 3.141592653589793)
    if mean_motion > 0:
        period_sec = 86400.0 / mean_motion
        orbital_phase = ((timestamp - tle.epoch).total_seconds() % period_sec) / period_sec
    else:
        orbital_phase = None

    sun_exposure = _estimate_sun_exposure(timestamp, lon)
    eclipse = detect_eclipse(timestamp, lon)

    return OrbitContext(
        orbit_lat=lat,
        orbit_lon=lon,
        orbit_altitude_km=alt,
        sun_exposure=sun_exposure,
        is_eclipse=eclipse,
        ground_station_visible=station_visible,
        distance_to_ground_station_km=distance_to_station,
        orbital_phase=orbital_phase,
        time_since_tle_epoch_sec=(timestamp - tle.epoch).total_seconds(),
    )
