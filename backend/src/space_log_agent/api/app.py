from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from space_log_agent.api.routes import router
from space_log_agent.api.run_manager import DatasetRunManager
from space_log_agent.api.service import AnalysisService
from space_log_agent.config import AppConfig
from space_log_agent.logging_setup import setup_logging
from space_log_agent.runtime import build_incident_runtime
from space_log_agent.sgr_patches import patch_sgr_agent_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared application dependencies for FastAPI lifecycle."""

    config = AppConfig()
    patch_sgr_agent_logging()
    setup_logging(config)
    runtime = build_incident_runtime(config)
    analysis_service = AnalysisService(runtime=runtime)
    app.state.analysis_service = analysis_service
    app.state.run_manager = DatasetRunManager(service=analysis_service)
    logger.info("FastAPI сервис анализа КА инициализирован")
    yield


app = FastAPI(
    title="Space Log Agent API",
    version="0.1.0",
    description="API анализа телеметрии КА (LangGraph + SGRAgent).",
    lifespan=lifespan,
)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run() -> None:
    """Run the FastAPI application with Uvicorn."""

    uvicorn.run(
        "space_log_agent.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
