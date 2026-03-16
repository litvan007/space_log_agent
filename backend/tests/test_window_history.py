from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from space_log_agent.api.service import AnalysisService
from space_log_agent.graph import analyze_incident_envelopes_async
from space_log_agent.models import IncidentEnvelope, RecentWindowHistory, WindowHistoryEntry


def _build_envelope(index: int) -> IncidentEnvelope:
    """Build a minimal envelope for deterministic history tests."""

    start = datetime(2025, 1, 1, 0, 0, tzinfo=UTC) + timedelta(minutes=index * 10)
    end = start + timedelta(minutes=10)
    return IncidentEnvelope(
        window_id=f"window_{index:05d}",
        timestamp_start=start,
        timestamp_end=end,
    )


def _build_history_entry(envelope: IncidentEnvelope) -> WindowHistoryEntry:
    """Build a compact deterministic history entry for one window."""

    return WindowHistoryEntry(
        window_id=envelope.window_id,
        timestamp_start=envelope.timestamp_start,
        timestamp_end=envelope.timestamp_end,
        anomaly_class="UNKNOWN",
        confidence_alarm=0.1,
        is_anomaly=False,
        observation=f"history for {envelope.window_id}",
        analysis_branch="nominal",
    )


def test_analyze_incident_envelopes_accumulates_and_clips_history(monkeypatch) -> None:
    """Sequential dataset analysis should pass bounded recent history between windows."""

    received_lengths: list[int] = []

    async def fake_analyze_incident_envelope_with_history_async(
        envelope: IncidentEnvelope,
        runtime,
        recent_window_history: RecentWindowHistory | None = None,
        event_handler=None,
    ) -> dict[str, object]:
        history = recent_window_history or RecentWindowHistory()
        received_lengths.append(len(history.entries))
        next_history = history.append_entry(_build_history_entry(envelope), max_entries=5)
        return {
            "final_output": envelope.window_id,
            "recent_window_history": next_history,
        }

    monkeypatch.setattr(
        "space_log_agent.graph.analyze_incident_envelope_with_history_async",
        fake_analyze_incident_envelope_with_history_async,
    )

    envelopes = [_build_envelope(index) for index in range(7)]
    reports = asyncio.run(analyze_incident_envelopes_async(envelopes, runtime=object()))

    assert reports == [envelope.window_id for envelope in envelopes]
    assert received_lengths == [0, 1, 2, 3, 4, 5, 5]


def test_single_envelope_service_returns_updated_history(monkeypatch) -> None:
    """Single-envelope API should accept external history and return updated history."""

    envelope = _build_envelope(1)
    incoming_history = RecentWindowHistory(entries=[_build_history_entry(_build_envelope(0))])

    async def fake_analyze_incident_envelope_with_history_async(
        envelope: IncidentEnvelope,
        runtime,
        recent_window_history: RecentWindowHistory | None = None,
        event_handler=None,
    ) -> dict[str, object]:
        history = recent_window_history or RecentWindowHistory()
        next_history = history.append_entry(_build_history_entry(envelope), max_entries=5)
        return {
            "final_output": "synthetic report",
            "recent_window_history": next_history,
        }

    monkeypatch.setattr(
        "space_log_agent.api.service.analyze_incident_envelope_with_history_async",
        fake_analyze_incident_envelope_with_history_async,
    )

    service = AnalysisService(runtime=SimpleNamespace(config=None))
    response = asyncio.run(service.analyze_envelope(envelope, recent_window_history=incoming_history))

    assert response.report == "synthetic report"
    assert len(response.recent_window_history.entries) == 2
    assert response.recent_window_history.entries[0].window_id == "window_00000"
    assert response.recent_window_history.entries[1].window_id == "window_00001"
