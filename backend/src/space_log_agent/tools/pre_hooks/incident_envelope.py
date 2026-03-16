from __future__ import annotations

from datetime import UTC, datetime

from loguru import logger

from space_log_agent.config import AppConfig
from space_log_agent.models import IncidentEnvelope
from space_log_agent.tools.pre_hooks.anomaly_rules import detect_all_anomalies
from space_log_agent.tools.pre_hooks.features import (
    aggregate_multi,
    detect_change_points,
    rough_anomaly_score,
    rolling_stats,
    summarize_alerts,
    summarize_errors,
    summarize_events,
    trend,
)
from space_log_agent.tools.pre_hooks.telemetry_loader import (
    iterate_windows,
    load_telemetry_dataframe,
    normalize_resample_forward_fill,
)
from space_log_agent.tools.pre_hooks.scenario_injection import AnalysisScenario, apply_analysis_scenario
from space_log_agent.tools.pre_hooks.tle_tools import derive_orbit_state, load_tle_records


KEY_CHANNELS = [
    "Battery_Temp",
    "Battery_Voltage",
    "NanoMind_Temp",
    "ACU2_Temp",
    "Background_RSSI",
    "X_Coarse_Spin",
    "Y_Coarse_Spin",
    "Z_Coarse_Spin",
    "PD1_CSS_theta",
    "ADCS_mode",
]


def _extract_analysis_scenario(envelope: IncidentEnvelope) -> AnalysisScenario | None:
    """Extract the selected analysis scenario from envelope features."""

    raw_scenario = envelope.precomputed_features.get("analysis_scenario")
    valid_scenarios: tuple[AnalysisScenario, ...] = ("mixed", "thermal", "power", "adcs", "rf", "nominal")
    if isinstance(raw_scenario, str) and raw_scenario in valid_scenarios:
        return raw_scenario
    return None


def _safe_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def build_incident_envelopes(config: AppConfig, limit_windows: int | None = None) -> list[IncidentEnvelope]:
    """Формирует минимальные IncidentEnvelope из сырых телеметрических данных."""
    telemetry = load_telemetry_dataframe(str(config.resolved_telemetry_csv_path))
    prepared = normalize_resample_forward_fill(telemetry, config.resample_freq)

    envelopes: list[IncidentEnvelope] = []

    for index, (window_start, window_end, window_df) in enumerate(
        iterate_windows(prepared, config.window_minutes, config.step_minutes),
        start=1,
    ):
        if limit_windows is not None and len(envelopes) >= limit_windows:
            break

        if window_df.empty:
            continue

        envelope = IncidentEnvelope(
            window_id=f"window_{index:05d}",
            timestamp_start=_safe_timestamp(window_start),
            timestamp_end=_safe_timestamp(window_end),
            raw_telemetry_ref=str(config.resolved_telemetry_csv_path),
            tle_ref=str(config.resolved_tle_path),
        )

        envelopes.append(envelope)

    logger.info("Сформировано окон инцидентов: {}", len(envelopes))
    return envelopes


def enrich_incident_envelope(envelope: IncidentEnvelope, config: AppConfig) -> IncidentEnvelope:
    """Прогоняет pre-hooks для одного окна и возвращает обогащенный IncidentEnvelope."""
    telemetry_path = envelope.raw_telemetry_ref or str(config.resolved_telemetry_csv_path)
    tle_path = envelope.tle_ref or str(config.resolved_tle_path)

    telemetry = load_telemetry_dataframe(telemetry_path)
    prepared = normalize_resample_forward_fill(telemetry, config.resample_freq)

    window_start = _safe_timestamp(envelope.timestamp_start)
    window_end = _safe_timestamp(envelope.timestamp_end)
    window_df = prepared[(prepared["Timestamp"] >= window_start) & (prepared["Timestamp"] <= window_end)]
    window_df = apply_analysis_scenario(window_df, _extract_analysis_scenario(envelope))

    if window_df.empty:
        logger.warning("Pre-hook: окно {} пустое после фильтрации, возвращаю исходный envelope", envelope.window_id)
        return envelope

    alerts, errors, evidence_map = detect_all_anomalies(window_df)
    trends = {channel: trend(channel, window_df) for channel in KEY_CHANNELS}
    change_points = {channel: detect_change_points(channel, window_df) for channel in KEY_CHANNELS}
    rolling = {channel: rolling_stats(channel, window_df) for channel in KEY_CHANNELS[:5]}

    anomaly_score = rough_anomaly_score(window_df, KEY_CHANNELS)
    summary = aggregate_multi(KEY_CHANNELS, window_df)

    tle_records, timescale = load_tle_records(tle_path)
    orbit_context = derive_orbit_state(
        timestamp=_safe_timestamp(window_df["Timestamp"].iloc[-1].to_pydatetime()),
        records=tle_records,
        timescale=timescale,
        ground_station_lat=config.ground_station_lat,
        ground_station_lon=config.ground_station_lon,
        visibility_threshold_km=config.ground_station_visibility_km,
    )

    logger.info("Pre-hook: окно {} обогащено, alerts={}, errors={}", envelope.window_id, len(alerts), len(errors))
    return envelope.model_copy(
        update={
            "telemetry_summary": summary,
            "alerts": alerts,
            "errors": errors,
            "orbit_context": orbit_context,
            "precomputed_features": {
                "rough_anomaly_score": anomaly_score,
                "trends": trends,
                "change_points": change_points,
                "rolling": rolling,
                "evidence_map": evidence_map,
                "alerts_summary": summarize_alerts(alerts),
                "errors_summary": summarize_errors(errors),
                "events": summarize_events(alerts, errors),
            },
            "raw_telemetry_ref": telemetry_path,
            "tle_ref": tle_path,
        }
    )
