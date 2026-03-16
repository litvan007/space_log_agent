from __future__ import annotations

from fastapi import Request

from space_log_agent.api.run_manager import DatasetRunManager
from space_log_agent.api.service import AnalysisService


def get_analysis_service(request: Request) -> AnalysisService:
    """Return the shared analysis service from FastAPI state."""

    return request.app.state.analysis_service


def get_run_manager(request: Request) -> DatasetRunManager:
    """Return the shared dataset run manager from FastAPI state."""

    return request.app.state.run_manager
