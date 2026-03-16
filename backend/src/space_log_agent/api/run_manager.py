from __future__ import annotations

import asyncio
import contextlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger

from space_log_agent.api.schemas import AnalysisScenario
from space_log_agent.api.service import AnalysisService, _apply_scenario_to_envelope
from space_log_agent.graph import analyze_incident_envelope_with_history_async
from space_log_agent.models import IncidentEnvelope, RecentWindowHistory
from space_log_agent.tools.pre_hooks.incident_envelope import build_incident_envelopes
from space_log_agent.window_history.history_utils import get_recent_window_history


def _utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(UTC).isoformat()


@dataclass(slots=True, repr=True)
class DatasetRun:
    """In-memory state of one dataset analysis run."""

    run_id: str
    scenario: AnalysisScenario | None
    limit_windows: int | None
    created_at_utc: str
    mode: str = "dataset"
    envelope: IncidentEnvelope | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    subscribers: list[asyncio.Queue[dict[str, Any]]] = field(default_factory=list)
    task: asyncio.Task[None] | None = None
    status: str = "pending"


class DatasetRunManager:
    """Manage background dataset runs and WebSocket subscribers."""

    def __init__(self, service: AnalysisService) -> None:
        """Store the analysis service used by background runs."""

        self._service = service
        self._runs: dict[str, DatasetRun] = {}

    async def create_dataset_run(
        self,
        limit_windows: int | None,
        scenario: AnalysisScenario | None,
    ) -> DatasetRun:
        """Create and start a background dataset run."""

        run_id = uuid.uuid4().hex
        run = DatasetRun(
            run_id=run_id,
            scenario=scenario,
            limit_windows=limit_windows,
            created_at_utc=_utc_now_iso(),
        )
        self._runs[run_id] = run
        run.task = asyncio.create_task(self._execute_run(run))
        return run

    async def create_envelope_run(
        self,
        envelope: IncidentEnvelope,
        scenario: AnalysisScenario | None,
    ) -> DatasetRun:
        """Create and start a background run for one envelope."""

        run_id = uuid.uuid4().hex
        run = DatasetRun(
            run_id=run_id,
            scenario=scenario,
            limit_windows=1,
            created_at_utc=_utc_now_iso(),
            mode="envelope",
            envelope=envelope,
        )
        self._runs[run_id] = run
        run.task = asyncio.create_task(self._execute_run(run))
        return run

    def get_run(self, run_id: str) -> DatasetRun:
        """Return a known run by identifier."""

        run = self._runs.get(run_id)
        if run is None:
            raise KeyError(run_id)
        return run

    async def subscribe(self, run_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Subscribe to all future events of the specified run."""

        run = self.get_run(run_id)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        for event in run.events:
            await queue.put(event)
        run.subscribers.append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove an existing subscriber queue from a run."""

        run = self._runs.get(run_id)
        if run is None:
            return
        with contextlib.suppress(ValueError):
            run.subscribers.remove(queue)

    async def _publish(self, run: DatasetRun, payload: dict[str, Any]) -> None:
        """Broadcast one event to all subscribers of the run."""

        event = {
            "run_id": run.run_id,
            "timestamp_utc": _utc_now_iso(),
            **payload,
        }
        run.events.append(event)
        if len(run.events) > 4000:
            del run.events[: len(run.events) - 4000]
        for queue in list(run.subscribers):
            await queue.put(event)

    async def _load_run_envelopes(self, run: DatasetRun) -> list[IncidentEnvelope]:
        """Build the envelope list for a dataset or single-envelope run."""

        if run.mode == "envelope":
            if run.envelope is None:
                raise ValueError("Single-envelope run was created without envelope payload.")
            return [_apply_scenario_to_envelope(run.envelope, run.scenario)]

        envelopes = await asyncio.to_thread(build_incident_envelopes, self._service.config, run.limit_windows)
        return [_apply_scenario_to_envelope(envelope, run.scenario) for envelope in envelopes]

    async def _execute_run(self, run: DatasetRun) -> None:
        """Execute the dataset run and publish progress events."""

        run.status = "running"
        await self._publish(
            run,
            {
                "type": "run_started",
                "status": run.status,
                "mode": run.mode,
                "scenario": run.scenario,
                "limit_windows": run.limit_windows,
            },
        )
        log_task = asyncio.create_task(self._tail_logs(run, self._service.config.resolved_log_file_path))

        try:
            envelopes = await self._load_run_envelopes(run)
            recent_window_history = RecentWindowHistory()
            await self._publish(
                run,
                {
                    "type": "run_windows_discovered",
                    "windows_count": len(envelopes),
                },
            )

            for index, envelope in enumerate(envelopes, start=1):
                await self._publish(
                    run,
                    {
                        "type": "window_discovered",
                        "window_id": envelope.window_id,
                        "index": index,
                        "total": len(envelopes),
                        "timestamp_start": envelope.timestamp_start.isoformat(),
                        "timestamp_end": envelope.timestamp_end.isoformat(),
                    },
                )

            for index, envelope in enumerate(envelopes, start=1):
                await self._publish(
                    run,
                    {
                        "type": "window_started",
                        "window_id": envelope.window_id,
                        "index": index,
                        "total": len(envelopes),
                        "timestamp_start": envelope.timestamp_start.isoformat(),
                        "timestamp_end": envelope.timestamp_end.isoformat(),
                    },
                )

                async def progress_handler(event: dict[str, Any]) -> None:
                    await self._publish(
                        run,
                        {
                            "type": "window_node",
                            "window_id": envelope.window_id,
                            "index": index,
                            "total": len(envelopes),
                            "payload": event,
                        },
                    )

                try:
                    result = await analyze_incident_envelope_with_history_async(
                        envelope,
                        self._service._runtime,
                        recent_window_history=recent_window_history,
                        event_handler=progress_handler,
                    )
                    report = result.get("final_output")
                    if not isinstance(report, str) or not report.strip():
                        report = "Нет результата графа"
                    history_raw = result.get("recent_window_history")
                    recent_window_history = (
                        history_raw
                        if isinstance(history_raw, RecentWindowHistory)
                        else RecentWindowHistory.model_validate(history_raw or {})
                    )
                    recent_window_history = get_recent_window_history(
                        recent_window_history,
                        self._service.config.window_history_limit,
                    )
                    uv_plan_details = result.get("deep_uv_plan_details", []) or envelope.precomputed_features.get("deep_uv_plan_details", [])
                    await self._publish(
                        run,
                        {
                            "type": "window_completed",
                            "window_id": envelope.window_id,
                            "index": index,
                            "total": len(envelopes),
                            "report": report,
                            "uv_plan_details": uv_plan_details,
                            "timestamp_start": envelope.timestamp_start.isoformat(),
                            "timestamp_end": envelope.timestamp_end.isoformat(),
                            "recent_window_history": recent_window_history.model_dump(mode="json")["entries"],
                        },
                    )
                except Exception as exc:
                    logger.exception("Ошибка live-run для окна {}", envelope.window_id)
                    await self._publish(
                        run,
                        {
                            "type": "window_failed",
                            "window_id": envelope.window_id,
                            "index": index,
                            "total": len(envelopes),
                            "error": str(exc),
                        },
                    )

            run.status = "completed"
            await self._publish(run, {"type": "run_completed", "status": run.status})
        except Exception as exc:
            run.status = "failed"
            logger.exception("Ошибка dataset run {}", run.run_id)
            await self._publish(
                run,
                {
                    "type": "run_failed",
                    "status": run.status,
                    "error": str(exc),
                },
            )
        finally:
            log_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await log_task

    async def _tail_logs(self, run: DatasetRun, log_file_path: Path) -> None:
        """Stream appended log lines for the lifetime of the run."""

        last_position = log_file_path.stat().st_size if log_file_path.exists() else 0
        while run.status == "running":
            if log_file_path.exists():
                with log_file_path.open("r", encoding="utf-8") as file:
                    file.seek(last_position)
                    chunk = file.read()
                    last_position = file.tell()
                if chunk:
                    for line in chunk.splitlines():
                        await self._publish(run, {"type": "log_line", "line": line})
            await asyncio.sleep(0.35)
