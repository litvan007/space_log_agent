from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from space_log_agent.api.dependencies import get_analysis_service, get_run_manager
from space_log_agent.api.run_manager import DatasetRunManager
from space_log_agent.api.schemas import (
    AnalyzeDatasetRequest,
    AnalyzeDatasetResponse,
    AnalyzeEnvelopeRequest,
    AnalyzeEnvelopeResponse,
    BackendLogsResponse,
    DatasetRunRequest,
    DatasetRunResponse,
    EnvelopeRunRequest,
    EnrichEnvelopeRequest,
    EnrichEnvelopeResponse,
    OrbitTrackRequest,
    OrbitTrackResponse,
    TelemetryWindowRequest,
    TelemetryWindowResponse,
)
from space_log_agent.api.service import AnalysisService


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "space-log-agent-api"}


@router.post("/api/v1/analyze/envelope", response_model=AnalyzeEnvelopeResponse)
async def analyze_envelope(
    request: AnalyzeEnvelopeRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeEnvelopeResponse:
    return await service.analyze_envelope(
        request.envelope,
        request.scenario,
        request.recent_window_history,
    )


@router.post("/api/v1/analyze/dataset", response_model=AnalyzeDatasetResponse)
async def analyze_dataset(
    request: AnalyzeDatasetRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalyzeDatasetResponse:
    return await service.analyze_dataset(request.limit_windows, request.scenario)


@router.post("/api/v1/envelope/enrich", response_model=EnrichEnvelopeResponse)
async def enrich_envelope(
    request: EnrichEnvelopeRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> EnrichEnvelopeResponse:
    return await service.enrich_envelope(request.envelope, request.scenario)


@router.post("/api/v1/telemetry/window", response_model=TelemetryWindowResponse)
async def telemetry_window(
    request: TelemetryWindowRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> TelemetryWindowResponse:
    return await service.telemetry_window(request)


@router.post("/api/v1/orbit/track", response_model=OrbitTrackResponse)
async def orbit_track(
    request: OrbitTrackRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> OrbitTrackResponse:
    return await service.orbit_track(request)


@router.get("/api/v1/logs/recent", response_model=BackendLogsResponse)
async def recent_logs(
    limit: int = 250,
    service: AnalysisService = Depends(get_analysis_service),
) -> BackendLogsResponse:
    """Return the most recent backend log lines for UI display."""

    return await service.get_recent_logs(limit)


@router.post("/api/v1/runs/dataset", response_model=DatasetRunResponse)
async def start_dataset_run(
    request: DatasetRunRequest,
    run_manager: DatasetRunManager = Depends(get_run_manager),
) -> DatasetRunResponse:
    """Create a background dataset run and return its identifier."""

    run = await run_manager.create_dataset_run(request.limit_windows, request.scenario)
    return DatasetRunResponse(
        run_id=run.run_id,
        created_at_utc=datetime.fromisoformat(run.created_at_utc),
    )


@router.post("/api/v1/runs/envelope", response_model=DatasetRunResponse)
async def start_envelope_run(
    request: EnvelopeRunRequest,
    run_manager: DatasetRunManager = Depends(get_run_manager),
) -> DatasetRunResponse:
    """Create a background single-envelope run and return its identifier."""

    run = await run_manager.create_envelope_run(request.envelope, request.scenario)
    return DatasetRunResponse(
        run_id=run.run_id,
        created_at_utc=datetime.fromisoformat(run.created_at_utc),
    )


@router.websocket("/api/v1/runs/{run_id}/ws")
async def dataset_run_ws(
    websocket: WebSocket,
    run_id: str,
) -> None:
    """Stream background dataset run events to the frontend."""

    await websocket.accept()
    run_manager: DatasetRunManager = websocket.app.state.run_manager
    try:
        queue = await run_manager.subscribe(run_id)
    except KeyError:
        await websocket.send_json({"type": "run_not_found", "run_id": run_id})
        await websocket.close(code=4404)
        return

    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("type") in {"run_completed", "run_failed"}:
                break
    except WebSocketDisconnect:
        pass
    finally:
        run_manager.unsubscribe(run_id, queue)
