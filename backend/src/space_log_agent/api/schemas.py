from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from space_log_agent.models import IncidentEnvelope, RecentWindowHistory, UVActionDetail


AnalysisScenario = Literal["mixed", "thermal", "power", "adcs", "rf", "nominal"]


class AnalyzeEnvelopeRequest(BaseModel):
    """Request payload for a single envelope analysis."""

    envelope: IncidentEnvelope
    scenario: AnalysisScenario | None = None
    recent_window_history: RecentWindowHistory | None = None


class AnalyzeEnvelopeResponse(BaseModel):
    """Response payload for a single envelope analysis."""

    window_id: str
    report: str
    processed_at_utc: datetime
    recent_window_history: RecentWindowHistory
    uv_plan_details: list[UVActionDetail] = Field(default_factory=list)


class AnalyzeDatasetRequest(BaseModel):
    """Request payload for dataset-wide analysis."""

    limit_windows: int | None = Field(default=3, ge=1, le=200)
    scenario: AnalysisScenario | None = None


class AnalyzeDatasetItem(BaseModel):
    """One analyzed telemetry window from the dataset."""

    window_id: str
    timestamp_start: datetime
    timestamp_end: datetime
    report: str


class AnalyzeDatasetResponse(BaseModel):
    """Dataset analysis response containing per-window reports."""

    windows_count: int
    processed_at_utc: datetime
    items: list[AnalyzeDatasetItem]


class EnrichEnvelopeRequest(BaseModel):
    """Request payload for deterministic envelope enrichment."""

    envelope: IncidentEnvelope
    scenario: AnalysisScenario | None = None


class EnrichEnvelopeResponse(BaseModel):
    """Response payload for deterministic envelope enrichment."""

    envelope: IncidentEnvelope
    processed_at_utc: datetime


class TelemetryWindowRequest(BaseModel):
    """Request payload for telemetry window extraction."""

    timestamp_start: datetime
    timestamp_end: datetime
    channels: list[str] | None = None
    raw_telemetry_ref: str | None = None
    resample_freq: str | None = None
    scenario: AnalysisScenario | None = None


class TelemetryWindowPoint(BaseModel):
    timestamp_utc: datetime
    values: dict[str, float | None]


class TelemetryWindowResponse(BaseModel):
    source_csv_path: str
    resample_freq: str
    channels: list[str]
    points: list[TelemetryWindowPoint]


class OrbitTrackRequest(BaseModel):
    """Request payload for orbit track generation."""

    start_utc: datetime | None = None
    duration_minutes: int = Field(default=90, ge=5, le=1440)
    step_seconds: int = Field(default=60, ge=10, le=900)
    tle_path: str | None = None


class OrbitTrackPoint(BaseModel):
    timestamp_utc: datetime
    lat_deg: float
    lon_deg: float
    altitude_km: float
    is_eclipse: bool | None = None
    ground_station_visible: bool | None = None


class OrbitTrackResponse(BaseModel):
    source_tle_path: str
    start_utc: datetime
    end_utc: datetime
    duration_minutes: int
    step_seconds: int
    points: list[OrbitTrackPoint]


class BackendLogsResponse(BaseModel):
    """Recent backend log lines for UI display."""

    log_file_path: str
    processed_at_utc: datetime
    lines: list[str]


class DatasetRunRequest(BaseModel):
    """Request payload for starting a live dataset run."""

    limit_windows: int | None = Field(default=None, ge=1, le=200)
    scenario: AnalysisScenario | None = None


class EnvelopeRunRequest(BaseModel):
    """Request payload for starting a live single-envelope run."""

    envelope: IncidentEnvelope
    scenario: AnalysisScenario | None = None


class DatasetRunResponse(BaseModel):
    """Response payload with the created live run identifier."""

    run_id: str
    created_at_utc: datetime
