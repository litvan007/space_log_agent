# Space Log Agent

Экспериментальный стенд анализа телеметрии КА:
- pre-hooks по телеметрии + TLE (SGP4/skyfield)
- асинхронный граф LangGraph
- глубокий анализ в ветке `SGRAgent`
- FastAPI backend-слой для интеграции с UI

## Архитектура

```text
CSV telemetry + TLE
  -> FastAPI:
       /api/v1/analyze/envelope | /api/v1/analyze/dataset
       /api/v1/envelope/enrich | /api/v1/telemetry/window | /api/v1/orbit/track
  -> LangGraph:
       pre_hook (resample/ffill, orbit context, признаки)
       classification (structured output)
       -> nominal_summary | deep_research (SGRAgent) -> post_hook
```

### Целевой граф (концепт)

```mermaid
flowchart TD
    A[START] --> B[pre_hook]
    B --> C[classification (SO)]
    C -->|is_anomaly = false<br/>или confidence_alarm < threshold| D[nominal_summary]
    C -->|is_anomaly = true<br/>и confidence_alarm >= threshold| E[deep_research]

    E --> F[uv_plan_generation]
    F --> G[post_hook_uv_feasibility_check]
    G --> H[final_report]

    D --> Z[END]
    H --> Z[END]
```

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
space-log-agent --analyze-dataset --limit-windows 3
```

Запуск FastAPI локально:

```bash
cd /Users/litvan/space_agent/backend
source /Users/litvan/space_agent/.venv/bin/activate
pip install -e .
space-log-agent-api
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Тесты:

```bash
pip install -e .[dev]
pytest -q tests
```

## Режимы CLI

- `--analyze-dataset` — загрузка CSV/TLE, чанкование, анализ окон.
- `--input-json '<IncidentEnvelope JSON>'` — анализ одного окна.
- `--limit-windows N` — ограничение числа окон из датасета.

## API Эндпоинты

- `GET /health`
- `POST /api/v1/analyze/envelope`
- `POST /api/v1/analyze/dataset`
- `POST /api/v1/envelope/enrich`
- `POST /api/v1/telemetry/window`
- `POST /api/v1/orbit/track`

Пример `POST /api/v1/analyze/envelope`:

```json
{
  "envelope": {
    "window_id": "window_02531",
    "timestamp_start": "2024-05-18T18:37:00Z",
    "timestamp_end": "2024-05-18T18:47:00Z",
    "raw_telemetry_ref": "/Users/litvan/space_agent/data_opssat/uhf_telemetry.csv",
    "tle_ref": "/Users/litvan/space_agent/data_opssat/tle_opssat.txt"
  }
}
```

Пример `POST /api/v1/orbit/track`:

```json
{
  "start_utc": "2024-05-18T18:37:00Z",
  "duration_minutes": 100,
  "step_seconds": 120,
  "tle_path": "/Users/litvan/space_agent/data_opssat/tle_opssat.txt"
}
```

Пример `POST /api/v1/envelope/enrich`:

```json
{
  "envelope": {
    "window_id": "window_02531",
    "timestamp_start": "2024-05-18T18:37:00Z",
    "timestamp_end": "2024-05-18T18:47:00Z",
    "raw_telemetry_ref": "/Users/litvan/space_agent/data_opssat/uhf_telemetry.csv",
    "tle_ref": "/Users/litvan/space_agent/data_opssat/tle_opssat.txt"
  }
}
```

Пример `POST /api/v1/telemetry/window`:

```json
{
  "timestamp_start": "2024-05-18T18:37:00Z",
  "timestamp_end": "2024-05-18T18:47:00Z",
  "raw_telemetry_ref": "/Users/litvan/space_agent/data_opssat/uhf_telemetry.csv",
  "channels": [
    "Battery_Voltage",
    "Battery_Temp",
    "NanoMind_Temp",
    "ACU2_Temp",
    "Background_RSSI",
    "Z_Coarse_Spin",
    "PD1_CSS_theta"
  ]
}
```

## Docker

Сборка и запуск контейнера:

```bash
cd /Users/litvan/space_agent
docker compose up --build
```

Проверка:

```bash
curl http://127.0.0.1:8000/health
```

## Структура

- `src/space_log_agent/prompts/*.txt` — все промпты на русском.
- `src/space_log_agent/api/` — API-модуль (app, routes, schemas, service).
- `src/space_log_agent/tools/pre_hooks/*` — инструменты pre-hooks.
- `src/space_log_agent/tools/deep_research/*` — инструменты deep analysis.
- `src/space_log_agent/graph.py` — асинхронный LangGraph.
- `src/space_log_agent/agent.py` — запуск deep ветки через SGRAgent.
- `tests/*` — тесты pre-hooks и сценариев аномалий.
