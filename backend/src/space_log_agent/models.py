from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class OrbitContext(BaseModel):
    """Orbital and ground-contact context attached to one telemetry window."""

    orbit_lat: float | None = Field(default=None, description="Широта КА, градусы")
    orbit_lon: float | None = Field(default=None, description="Долгота КА, градусы")
    orbit_altitude_km: float | None = Field(default=None, description="Высота орбиты, км")
    sun_exposure: bool | None = Field(default=None, description="КА на освещенной части орбиты")
    is_eclipse: bool | None = Field(default=None, description="КА в тени Земли")
    ground_station_visible: bool | None = Field(default=None, description="Видимость наземной станции")
    distance_to_ground_station_km: float | None = Field(default=None, description="Дистанция до НС, км")
    orbital_phase: float | None = Field(default=None, description="Фаза орбиты [0..1]")
    time_since_tle_epoch_sec: float | None = Field(default=None, description="Секунды от epoch выбранного TLE")


class IncidentEnvelope(BaseModel):
    """One telemetry window prepared for agent analysis."""

    window_id: str
    timestamp_start: datetime
    timestamp_end: datetime
    telemetry_summary: dict[str, Any] = Field(default_factory=dict)
    alerts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    orbit_context: OrbitContext = Field(default_factory=OrbitContext)
    precomputed_features: dict[str, Any] = Field(default_factory=dict)
    raw_telemetry_ref: str | None = None
    tle_ref: str | None = None

    def to_agent_payload(self) -> dict[str, Any]:
        """Serialize the envelope into a JSON-ready payload for LLM input."""

        return self.model_dump(mode="json")


class IncidentClassification(BaseModel):
    """Structured result of the primary anomaly classification step."""

    observation: str = Field(description="Что наблюдается в окне телеметрии")
    evidences: list[str] = Field(default_factory=list, max_length=10)
    confidence_alarm: float = Field(ge=0.0, le=1.0)
    is_anomaly: bool
    anomaly_class: Literal["POWER", "THERMAL", "ADCS", "RF", "MIXED", "UNKNOWN"]


class DatasetAnalysisResult(BaseModel):
    """One dataset-level analysis result for a telemetry window."""

    window_id: str
    classification: IncidentClassification
    report: str


class UVPlan(BaseModel):
    """Structured proposal of operator actions for one telemetry window."""

    reasoning: str = Field(description="Обоснование выбранного плана УВ")
    actions: list[str] = Field(description="Список управляющих воздействий", min_length=1, max_length=8)
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Приоритет выполнения плана")


class UVActionDetail(BaseModel):
    """Structured description of one proposed UV action."""

    action: str = Field(description="Код управляющего воздействия")
    description: str = Field(description="Краткое описание назначения действия")
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Приоритет выполнения действия")
    prechecks: list[str] = Field(default_factory=list, description="Проверки перед исполнением действия")
    postchecks: list[str] = Field(default_factory=list, description="Проверки после исполнения действия")


class UVPostCheck(BaseModel):
    """Post-hook validation result for the proposed UV plan."""

    valid: bool = Field(description="План УВ выполним в текущих ограничениях")
    constraints: list[str] = Field(default_factory=list, description="Обнаруженные ограничения")
    recommendations: list[str] = Field(default_factory=list, description="Рекомендации по корректировке плана")


class WindowHistoryEntry(BaseModel):
    """Compact deterministic summary of one previously processed telemetry window."""

    window_id: str
    timestamp_start: datetime
    timestamp_end: datetime
    anomaly_class: Literal["POWER", "THERMAL", "ADCS", "RF", "MIXED", "UNKNOWN"]
    confidence_alarm: float = Field(ge=0.0, le=1.0)
    is_anomaly: bool
    observation: str
    analysis_branch: Literal["nominal", "deep"]
    proposed_uv_actions: list[str] = Field(default_factory=list)
    post_hook_valid: bool | None = None
    post_hook_constraints: list[str] = Field(default_factory=list)
    post_hook_recommendations: list[str] = Field(default_factory=list)


class RecentWindowHistory(BaseModel):
    """Bounded rolling history of previously analyzed telemetry windows."""

    entries: list[WindowHistoryEntry] = Field(default_factory=list)

    def clipped(self, max_entries: int = 5) -> "RecentWindowHistory":
        """Return the most recent bounded window history."""

        return RecentWindowHistory(entries=self.entries[-max_entries:])

    def append_entry(self, entry: WindowHistoryEntry, max_entries: int = 5) -> "RecentWindowHistory":
        """Append one entry and keep only the most recent bounded tail."""

        return RecentWindowHistory(entries=[*self.entries, entry][-max_entries:])
