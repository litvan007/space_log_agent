# Space Log Agent

Research prototype of an LLM-based agent for spacecraft telemetry anomaly analysis and operator action planning.

`Space Log Agent` is a monorepo for an experimental stand that analyzes telemetry windows of a spacecraft, classifies anomaly scenarios, runs an agent-driven deep investigation, and produces a structured operator-oriented action plan.

The project combines:
- telemetry and TLE preprocessing;
- a LangGraph execution pipeline;
- an SGRAgent-based deep analysis branch with tools;
- a FastAPI backend;
- a lightweight frontend for demonstration;
- an article with the research description and results.

## What The System Does

At a high level, the stand processes telemetry in fixed windows and moves each window through a hybrid pipeline:

```text
raw telemetry CSV + TLE
  -> pre_hook
  -> classification
  -> nominal_summary | deep_research
  -> post_hook
  -> final report
```

The backend prepares a formalized `IncidentEnvelope`, computes orbit context, derives basic features, classifies the window, and, for anomaly cases, runs a deeper agent flow before validating the resulting action plan.

## Repository Layout

```text
.
├── article/         Research paper and LaTeX sources
├── backend/         Python backend, LangGraph pipeline, API, agent tools
├── data_opssat/     OPS-SAT telemetry CSV and TLE data
├── frontend/        Static UI for stand visualization
├── logs/            Runtime logs and traces
└── docker-compose.yml
```

Key backend modules:

- `backend/src/space_log_agent/graph.py` builds the main LangGraph flow.
- `backend/src/space_log_agent/agent.py` runs the `deep_research` branch through `SGRAgent`.
- `backend/src/space_log_agent/models.py` defines the formal domain schemas.
- `backend/src/space_log_agent/tools/pre_hooks/` contains preprocessing and post-check logic.
- `backend/src/space_log_agent/tools/deep_research/` contains deep analysis tools.
- `backend/src/space_log_agent/api/` contains FastAPI app, routes, schemas, and services.
- `backend/src/space_log_agent/prompts/` stores reusable prompt files.

## Main Concepts

- `IncidentEnvelope`
  One telemetry window prepared for analysis. It stores time bounds, telemetry summary, alerts, errors, orbit context, precomputed features, and references to raw telemetry and TLE.

- `IncidentClassification`
  Structured result of the primary classification step. It contains `observation`, `evidences`, `confidence_alarm`, `is_anomaly`, and `anomaly_class`.

- `UVPlan`
  Structured proposal of operator actions for the current anomaly window.

- `UVPostCheck`
  Validation result for the proposed action plan under stand constraints.

## Current Deep Analysis Logic

The current text and implementation describe `deep_research` as a sequence of narrow diagnostic and planning steps. In the research framing, the agent works with tools such as:

- `CheckPowerThermalCouplingTool`
- `CheckADCSStabilityLossTool`
- `CheckCommVisibilityConstraintTool`
- `CheckRecentWindowTrendTool`
- `BuildUVPlanTool`

In the current codebase, the implemented toolset includes:

- `InspectIncidentEnvelopeTool`
- `ComputeTelemetryDiagnosticsTool`
- `BuildUVPlanTool`
- `FinalAnswerTool`

This split is intentional: the research text already motivates a more domain-specific future toolset, while the code implements the current experimental subset.

## Quick Start

### Option 1: Run Everything With Docker

From the repository root:

```bash
docker compose up --build
```

After startup:

- Backend API: `http://127.0.0.1:8000/docs`
- Frontend UI: `http://127.0.0.1:8080`
- Health check: `http://127.0.0.1:8000/health`

Simple check:

```bash
curl http://127.0.0.1:8000/health
```

### Option 2: Run Backend Locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
space-log-agent-api
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Option 3: Run CLI Dataset Analysis

```bash
cd backend
source .venv/bin/activate
space-log-agent --analyze-dataset --limit-windows 3
```

Run a single window from JSON:

```bash
space-log-agent --input-json '{"window_id":"window_001","timestamp_start":"2024-05-18T18:37:00Z","timestamp_end":"2024-05-18T18:47:00Z","raw_telemetry_ref":"../data_opssat/uhf_telemetry.csv","tle_ref":"../data_opssat/tle_opssat.txt"}'
```

## Configuration

The backend is configured through `backend/.env`.

Important variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`
- `OPENAI_TEMPERATURE`
- `ANOMALY_THRESHOLD`
- `SGR_MAX_ITERATIONS`
- `WINDOW_HISTORY_LIMIT`
- `TELEMETRY_CSV_PATH`
- `TLE_PATH`
- `RESAMPLE_FREQ`
- `WINDOW_MINUTES`
- `STEP_MINUTES`
- `GROUND_STATION_LAT`
- `GROUND_STATION_LON`
- `GROUND_STATION_VISIBILITY_KM`
- `LOGS_DIR`
- `LOG_FILE_PATH`
- `CLASSIFICATION_PROMPT_PATH`
- `DEEP_SYSTEM_PROMPT_PATH`
- `DEEP_USER_PROMPT_PATH`

The example file is here:

- [`backend/.env.example`](backend/.env.example)

## API Overview

The FastAPI service exposes:

- `GET /health`
- `POST /api/v1/analyze/envelope`
- `POST /api/v1/analyze/dataset`
- `POST /api/v1/envelope/enrich`
- `POST /api/v1/telemetry/window`
- `POST /api/v1/orbit/track`
- `GET /api/v1/logs/recent`
- `POST /api/v1/runs/dataset`
- `POST /api/v1/runs/envelope`
- `WS /api/v1/runs/{run_id}/ws`

Example request for single-window analysis:

```json
{
  "envelope": {
    "window_id": "manual_20240518_1837_1847",
    "timestamp_start": "2024-05-18T18:37:00Z",
    "timestamp_end": "2024-05-18T18:47:00Z",
    "raw_telemetry_ref": "data_opssat/uhf_telemetry.csv",
    "tle_ref": "data_opssat/tle_opssat.txt"
  }
}
```

## Frontend

The frontend is a static demonstration UI served by `nginx` in Docker or directly from the `frontend/` directory.

It provides:

- a dashboard-style telemetry view;
- an agent graph visualization;
- node-level details for the execution pipeline;
- scenario switching;
- mock mode and backend-connected mode.

Relevant files:

- [`frontend/index.html`](frontend/index.html)
- [`frontend/styles.css`](frontend/styles.css)
- [`frontend/app.js`](frontend/app.js)

## Data

The stand is built around OPS-SAT telemetry and TLE-based orbit context reconstruction.

Expected local data paths in the default setup:

- `data_opssat/uhf_telemetry.csv`
- `data_opssat/tle_opssat.txt`

## Logs And Traces

Runtime logs are written to:

- [`logs/`](logs/)

The backend also stores deeper traces for agent runs, including `deep_research` execution logs.

## Tests

Run backend tests with:

```bash
cd backend
source .venv/bin/activate
pytest -q tests
```

## Research Article

The LaTeX article describing the architecture, experiment setup, and results lives in:

- [`article/main.tex`](article/main.tex)

Build the paper locally:

```bash
cd article
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Current Status

This repository is a research prototype, not a production flight operations system.

What is already useful:

- formalized telemetry-window processing;
- hybrid deterministic + LLM analysis flow;
- structured anomaly classification;
- deep analysis with tool usage;
- structured action-plan generation and validation;
- API and UI integration for stand experiments.

What is still experimental:

- domain completeness of the deep analysis tools;
- consistency between classification hypotheses and numerical diagnostics;
- action catalog coverage for spacecraft-specific operator procedures;
- production-grade operational safety controls.
