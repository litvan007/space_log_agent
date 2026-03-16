from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest

from space_log_agent.config import DEFAULT_TELEMETRY_CSV_PATH, DEFAULT_TLE_PATH
from space_log_agent.tools.pre_hooks.tle_tools import derive_orbit_state, load_tle_records, select_tle_for_timestamp


@pytest.mark.skipif(not Path(DEFAULT_TELEMETRY_CSV_PATH).exists(), reason="Нет файла телеметрии")
@pytest.mark.skipif(not Path(DEFAULT_TLE_PATH).exists(), reason="Нет TLE файла")
def test_tle_alignment_and_orbit_state() -> None:
    telemetry = pd.read_csv(DEFAULT_TELEMETRY_CSV_PATH, nrows=1)
    timestamp = pd.to_datetime(telemetry["Timestamp"].iloc[0], utc=True).to_pydatetime().astimezone(UTC)

    records, timescale = load_tle_records(str(DEFAULT_TLE_PATH))
    chosen = select_tle_for_timestamp(records, timestamp)

    assert chosen.epoch <= timestamp

    orbit = derive_orbit_state(
        timestamp=timestamp,
        records=records,
        timescale=timescale,
        ground_station_lat=55.7558,
        ground_station_lon=37.6173,
        visibility_threshold_km=2500.0,
    )

    assert orbit.orbit_lat is not None
    assert orbit.orbit_lon is not None
    assert orbit.orbit_altitude_km is not None
    assert -90.0 <= orbit.orbit_lat <= 90.0
    assert -180.0 <= orbit.orbit_lon <= 180.0
    assert 100.0 <= orbit.orbit_altitude_km <= 2000.0
