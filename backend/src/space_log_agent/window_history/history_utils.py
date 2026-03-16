from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from space_log_agent.models import IncidentClassification, IncidentEnvelope, RecentWindowHistory, UVPostCheck, WindowHistoryEntry


def get_recent_window_history(
    raw_history: RecentWindowHistory | Mapping[str, Any] | None,
    max_entries: int = 5,
) -> RecentWindowHistory:
    """Return bounded recent window history from an optional raw payload."""

    if raw_history is None:
        return RecentWindowHistory()
    if isinstance(raw_history, RecentWindowHistory):
        return raw_history.clipped(max_entries)
    if isinstance(raw_history, Mapping):
        return RecentWindowHistory.model_validate(raw_history).clipped(max_entries)
    raise TypeError("Некорректный тип recent_window_history")


def serialize_recent_window_history(
    history: RecentWindowHistory,
    max_entries: int = 5,
) -> list[dict[str, Any]]:
    """Convert bounded history into a compact JSON-ready list of entries."""

    return history.clipped(max_entries).model_dump(mode="json")["entries"]


def build_window_history_entry(
    envelope: IncidentEnvelope,
    classification: IncidentClassification,
    analysis_branch: Literal["nominal", "deep"],
    proposed_uv_actions: list[str] | None = None,
    uv_post_check: UVPostCheck | None = None,
) -> WindowHistoryEntry:
    """Build a deterministic compact summary for one analyzed telemetry window."""

    return WindowHistoryEntry(
        window_id=envelope.window_id,
        timestamp_start=envelope.timestamp_start,
        timestamp_end=envelope.timestamp_end,
        anomaly_class=classification.anomaly_class,
        confidence_alarm=classification.confidence_alarm,
        is_anomaly=classification.is_anomaly,
        observation=classification.observation,
        analysis_branch=analysis_branch,
        proposed_uv_actions=proposed_uv_actions or [],
        post_hook_valid=uv_post_check.valid if uv_post_check is not None else None,
        post_hook_constraints=uv_post_check.constraints if uv_post_check is not None else [],
        post_hook_recommendations=uv_post_check.recommendations if uv_post_check is not None else [],
    )


def append_history_entry(
    raw_history: RecentWindowHistory | Mapping[str, Any] | None,
    entry: WindowHistoryEntry,
    max_entries: int = 5,
) -> RecentWindowHistory:
    """Append one entry to bounded recent history and return the clipped result."""

    return get_recent_window_history(raw_history, max_entries).append_entry(entry, max_entries)


def format_nominal_history_summary(history: RecentWindowHistory) -> str:
    """Build a short deterministic summary line for the last processed windows."""

    if not history.entries:
        return ""

    tail = history.entries[-3:]
    parts = [
        (
            f"{entry.window_id}: {entry.anomaly_class}, "
            f"conf={entry.confidence_alarm:.2f}, "
            f"ветка={entry.analysis_branch}"
        )
        for entry in tail
    ]
    return "Контекст предыдущих окон: " + "; ".join(parts) + "."
