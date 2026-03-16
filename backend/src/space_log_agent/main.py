from __future__ import annotations

import argparse
import asyncio
import json

from loguru import logger
from pydantic import ValidationError

from space_log_agent.config import AppConfig
from space_log_agent.graph import analyze_incident_envelope_async, analyze_incident_envelopes_async
from space_log_agent.logging_setup import setup_logging
from space_log_agent.models import IncidentEnvelope
from space_log_agent.runtime import IncidentRuntime, build_incident_runtime
from space_log_agent.sgr_patches import patch_sgr_agent_logging
from space_log_agent.tools.pre_hooks.incident_envelope import build_incident_envelopes


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for incident analysis commands."""

    parser = argparse.ArgumentParser(description="Асинхронный анализ телеметрии КА (LangGraph + SGRAgent)")
    parser.add_argument("--input-json", help="JSON строка IncidentEnvelope для единичного анализа")
    parser.add_argument("--analyze-dataset", action="store_true", help="Анализировать CSV+TLE датасет")
    parser.add_argument("--limit-windows", type=int, default=3, help="Ограничение числа окон из датасета")
    return parser.parse_args()


async def run_single_envelope(runtime: IncidentRuntime, input_json: str) -> int:
    """Run analysis for one envelope passed via CLI JSON."""

    try:
        payload = json.loads(input_json)
        envelope = IncidentEnvelope.model_validate(payload)
    except json.JSONDecodeError as exc:
        logger.error("Некорректный JSON: {}", exc)
        return 2
    except ValidationError as exc:
        logger.error("Ошибка валидации IncidentEnvelope: {}", exc)
        return 3

    report = await analyze_incident_envelope_async(envelope, runtime)
    print(report)
    return 0


async def run_dataset(runtime: IncidentRuntime, limit_windows: int | None) -> int:
    """Run dataset analysis from CLI using shared runtime dependencies."""

    envelopes = build_incident_envelopes(config=runtime.config, limit_windows=limit_windows)
    if not envelopes:
        logger.warning("Не сформировано ни одного окна инцидента")
        return 4

    reports = await analyze_incident_envelopes_async(envelopes, runtime)
    for envelope, report in zip(envelopes, reports, strict=True):
        print(f"\n===== {envelope.window_id} =====")
        print(report)

    return 0


def main() -> None:
    """Run the CLI entrypoint for incident analysis."""

    args = parse_args()
    config = AppConfig()
    patch_sgr_agent_logging()
    runtime = build_incident_runtime(config)
    setup_logging(config)

    if args.input_json:
        exit_code = asyncio.run(run_single_envelope(runtime, args.input_json))
        raise SystemExit(exit_code)

    analyze_dataset = args.analyze_dataset or not args.input_json
    if analyze_dataset:
        exit_code = asyncio.run(run_dataset(runtime, args.limit_windows))
        raise SystemExit(exit_code)

    logger.error("Не передан режим запуска")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
