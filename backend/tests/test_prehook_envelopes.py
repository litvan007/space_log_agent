from __future__ import annotations

from pathlib import Path

import pytest

from space_log_agent.config import AppConfig
from space_log_agent.tools.pre_hooks.incident_envelope import build_incident_envelopes


@pytest.mark.skipif(
    not Path("/Users/litvan/Downloads/UHF_TM_notebook/uhf_telemetry.csv").exists(),
    reason="Нет файла телеметрии",
)
@pytest.mark.skipif(
    not Path("/Users/litvan/Downloads/UHF_TM_notebook/tle_opssat.txt").exists(),
    reason="Нет TLE файла",
)
def test_build_incident_envelopes_contains_required_blocks() -> None:
    config = AppConfig(
        telemetry_csv_path=Path("/Users/litvan/Downloads/UHF_TM_notebook/uhf_telemetry.csv"),
        tle_path=Path("/Users/litvan/Downloads/UHF_TM_notebook/tle_opssat.txt"),
        window_minutes=10,
        step_minutes=10,
    )

    envelopes = build_incident_envelopes(config=config, limit_windows=2)

    assert len(envelopes) > 0
    for envelope in envelopes:
        assert envelope.window_id
        assert envelope.telemetry_summary
        assert "rough_anomaly_score" in envelope.precomputed_features
        assert "trends" in envelope.precomputed_features
        assert "change_points" in envelope.precomputed_features
        assert envelope.orbit_context.orbit_lat is not None
        assert envelope.orbit_context.orbit_lon is not None
        assert envelope.orbit_context.orbit_altitude_km is not None
