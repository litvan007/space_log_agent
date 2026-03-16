from __future__ import annotations

import asyncio
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from space_log_agent.api.schemas import (
    AnalysisScenario,
    AnalyzeDatasetItem,
    AnalyzeDatasetResponse,
    AnalyzeEnvelopeResponse,
    BackendLogsResponse,
    EnrichEnvelopeResponse,
    OrbitTrackPoint,
    OrbitTrackRequest,
    OrbitTrackResponse,
    TelemetryWindowPoint,
    TelemetryWindowRequest,
    TelemetryWindowResponse,
)
from space_log_agent.config import AppConfig
from space_log_agent.graph import (
    analyze_incident_envelope_with_history_async,
    analyze_incident_envelopes_async,
)
from space_log_agent.models import IncidentEnvelope, RecentWindowHistory
from space_log_agent.runtime import IncidentRuntime
from space_log_agent.tools.pre_hooks.incident_envelope import build_incident_envelopes, enrich_incident_envelope
from space_log_agent.tools.pre_hooks.orbit_track import build_orbit_track
from space_log_agent.tools.pre_hooks.scenario_injection import apply_analysis_scenario
from space_log_agent.tools.pre_hooks.telemetry_loader import load_telemetry_dataframe, normalize_resample_forward_fill
from space_log_agent.window_history.history_utils import get_recent_window_history


def _read_log_tail_lines(log_file_path: Path, limit: int) -> list[str]:
    """Read the last N lines from the backend log file."""

    if not log_file_path.exists():
        return []

    with log_file_path.open("r", encoding="utf-8") as file:
        return [line.rstrip("\n") for line in deque(file, maxlen=limit)]


def _apply_scenario_to_envelope(
    envelope: IncidentEnvelope,
    scenario: AnalysisScenario | None,
) -> IncidentEnvelope:
    """Attach the selected analysis scenario to an incident envelope."""

    if scenario is None:
        return envelope

    next_features = dict(envelope.precomputed_features)
    next_features["analysis_scenario"] = scenario
    return envelope.model_copy(update={"precomputed_features": next_features})


class AnalysisService:
    """Сервисный слой API для запуска аналитического графа."""

    def __init__(self, runtime: IncidentRuntime) -> None:
        """Store shared runtime for API handlers."""

        self._runtime = runtime

    @property
    def config(self) -> AppConfig:
        """Expose application configuration used by the service."""

        return self._runtime.config

    def _window_history_limit(self) -> int:
        """Return the configured recent-window history limit with a safe fallback."""

        runtime_config = getattr(self._runtime, "config", None)
        return max(1, int(getattr(runtime_config, "window_history_limit", 5)))

    async def analyze_envelope(
        self,
        envelope: IncidentEnvelope,
        scenario: AnalysisScenario | None = None,
        recent_window_history: RecentWindowHistory | None = None,
    ) -> AnalyzeEnvelopeResponse:
        """Analyze a single incident envelope."""

        scenario_envelope = _apply_scenario_to_envelope(envelope, scenario)
        result = await analyze_incident_envelope_with_history_async(
            scenario_envelope,
            self._runtime,
            recent_window_history=recent_window_history,
        )
        report = result.get("final_output")
        if not isinstance(report, str) or not report.strip():
            report = "Нет результата графа"
        next_history_raw = result.get("recent_window_history")
        next_history = (
            next_history_raw
            if isinstance(next_history_raw, RecentWindowHistory)
            else RecentWindowHistory.model_validate(next_history_raw or {})
        )
        next_history = get_recent_window_history(next_history, self._window_history_limit())
        uv_plan_details_raw = result.get("deep_uv_plan_details", []) or scenario_envelope.precomputed_features.get("deep_uv_plan_details", [])
        return AnalyzeEnvelopeResponse(
            window_id=scenario_envelope.window_id,
            report=report,
            processed_at_utc=datetime.now(UTC),
            recent_window_history=next_history,
            uv_plan_details=uv_plan_details_raw,
        )

    async def analyze_dataset(
        self,
        limit_windows: int | None,
        scenario: AnalysisScenario | None = None,
    ) -> AnalyzeDatasetResponse:
        """Analyze a dataset slice and return reports for each window."""

        logger.info("API: запуск dataset-анализа, limit_windows={}, scenario={}", limit_windows, scenario)
        envelopes = await asyncio.to_thread(build_incident_envelopes, self.config, limit_windows)
        envelopes = [_apply_scenario_to_envelope(envelope, scenario) for envelope in envelopes]
        reports = await analyze_incident_envelopes_async(envelopes, self._runtime)

        items = [
            AnalyzeDatasetItem(
                window_id=envelope.window_id,
                timestamp_start=envelope.timestamp_start,
                timestamp_end=envelope.timestamp_end,
                report=report,
            )
            for envelope, report in zip(envelopes, reports, strict=True)
        ]
        return AnalyzeDatasetResponse(
            windows_count=len(items),
            processed_at_utc=datetime.now(UTC),
            items=items,
        )

    async def enrich_envelope(
        self,
        envelope: IncidentEnvelope,
        scenario: AnalysisScenario | None = None,
    ) -> EnrichEnvelopeResponse:
        """Run deterministic enrichment for one envelope."""

        logger.info("API: enrich-envelope, window_id={}, scenario={}", envelope.window_id, scenario)
        scenario_envelope = _apply_scenario_to_envelope(envelope, scenario)
        enriched = await asyncio.to_thread(enrich_incident_envelope, scenario_envelope, self.config)
        return EnrichEnvelopeResponse(
            envelope=enriched,
            processed_at_utc=datetime.now(UTC),
        )

    async def telemetry_window(self, request: TelemetryWindowRequest) -> TelemetryWindowResponse:
        """Load and resample telemetry data for the requested time window."""

        csv_path = request.raw_telemetry_ref or str(self.config.resolved_telemetry_csv_path)
        resample_freq = request.resample_freq or self.config.resample_freq
        channels = request.channels or [
            "Battery_Voltage",
            "Battery_Temp",
            "NanoMind_Temp",
            "ACU2_Temp",
            "Background_RSSI",
            "Z_Coarse_Spin",
            "PD1_CSS_theta",
        ]
        logger.info(
            "API: telemetry-window, start={}, end={}, channels={}, scenario={}",
            request.timestamp_start.isoformat(),
            request.timestamp_end.isoformat(),
            channels,
            request.scenario,
        )

        dataframe = await asyncio.to_thread(load_telemetry_dataframe, csv_path)
        prepared = await asyncio.to_thread(normalize_resample_forward_fill, dataframe, resample_freq)

        left = request.timestamp_start.astimezone(UTC)
        right = request.timestamp_end.astimezone(UTC)
        window_df = prepared[(prepared["Timestamp"] >= left) & (prepared["Timestamp"] <= right)].copy()
        window_df = apply_analysis_scenario(window_df, request.scenario)

        points: list[TelemetryWindowPoint] = []
        if not window_df.empty:
            for _, row in window_df.iterrows():
                values: dict[str, float | None] = {}
                for channel in channels:
                    raw_value = row[channel] if channel in window_df.columns else None
                    values[channel] = None if pd.isna(raw_value) else float(raw_value)
                timestamp_value = row["Timestamp"]
                timestamp_utc = timestamp_value.to_pydatetime().astimezone(UTC)
                points.append(TelemetryWindowPoint(timestamp_utc=timestamp_utc, values=values))

        return TelemetryWindowResponse(
            source_csv_path=csv_path,
            resample_freq=resample_freq,
            channels=channels,
            points=points,
        )

    async def orbit_track(self, request: OrbitTrackRequest) -> OrbitTrackResponse:
        """Build an orbit track projection for the requested interval."""

        start_utc = request.start_utc or datetime.now(UTC)
        tle_path = request.tle_path or str(self.config.resolved_tle_path)

        logger.info(
            "API: orbit-track, start={}, duration_minutes={}, step_seconds={}",
            start_utc.isoformat(),
            request.duration_minutes,
            request.step_seconds,
        )
        raw_points = await asyncio.to_thread(
            build_orbit_track,
            tle_path,
            start_utc,
            request.duration_minutes,
            request.step_seconds,
            self.config.ground_station_lat,
            self.config.ground_station_lon,
            self.config.ground_station_visibility_km,
        )

        points = [OrbitTrackPoint.model_validate(point) for point in raw_points]
        end_utc = points[-1].timestamp_utc if points else start_utc

        return OrbitTrackResponse(
            source_tle_path=tle_path,
            start_utc=start_utc,
            end_utc=end_utc,
            duration_minutes=request.duration_minutes,
            step_seconds=request.step_seconds,
            points=points,
        )

    async def get_recent_logs(self, limit: int) -> BackendLogsResponse:
        """Return the latest backend log lines for UI inspection."""

        safe_limit = max(20, min(limit, 800))
        lines = await asyncio.to_thread(_read_log_tail_lines, self.config.resolved_log_file_path, safe_limit)
        return BackendLogsResponse(
            log_file_path=str(self.config.resolved_log_file_path),
            processed_at_utc=datetime.now(UTC),
            lines=lines,
        )
