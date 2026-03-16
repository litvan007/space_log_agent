from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loguru import logger
from openai import AsyncOpenAI
from sgr_agent_core.agent_definition import AgentConfig as SGRAgentConfig
from sgr_agent_core.agent_definition import ExecutionConfig, LLMConfig, PromptsConfig
from sgr_agent_core.tools import FinalAnswerTool

from space_log_agent.config import AppConfig, load_prompts
from space_log_agent.models import IncidentClassification, IncidentEnvelope, RecentWindowHistory
from space_log_agent.tools.deep_research.incident_tools import (
    BuildUVPlanTool,
    ComputeTelemetryDiagnosticsTool,
    IncidentSGRAgent,
    InspectIncidentEnvelopeTool,
)


def _sanitize_log_token(value: str) -> str:
    """Return a filesystem-safe token for log file names."""

    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)


def _format_agent_log_entry(entry: dict[str, Any]) -> str:
    """Render one SGRAgent step entry into a readable text block."""

    step_type = str(entry.get("step_type", "unknown"))
    timestamp = str(entry.get("timestamp", ""))
    step_number = entry.get("step_number", "?")
    lines = [f"[step {step_number}] {step_type} @ {timestamp}"]
    if step_type == "reasoning":
        reasoning = entry.get("agent_reasoning", {})
        lines.append(json.dumps(reasoning, ensure_ascii=False, indent=2))
    elif step_type == "tool_execution":
        lines.append(f"tool_name: {entry.get('tool_name', '')}")
        lines.append("tool_context:")
        lines.append(json.dumps(entry.get("agent_tool_context", {}), ensure_ascii=False, indent=2))
        lines.append("tool_result:")
        lines.append(str(entry.get("agent_tool_execution_result", "")))
    else:
        lines.append(json.dumps(entry, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def _write_deep_research_trace(
    config: AppConfig,
    envelope: IncidentEnvelope,
    classification_payload: dict[str, Any],
    agent: IncidentSGRAgent,
    final_result: str | None,
) -> Path:
    """Write a full deep-research trace to a text file in the logs directory."""

    config.resolved_logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    safe_window_id = _sanitize_log_token(envelope.window_id)
    trace_path = config.resolved_logs_dir / f"{timestamp}-{safe_window_id}-deep-trace.txt"
    custom_context = agent._context.custom_context if isinstance(agent._context.custom_context, dict) else {}
    sections = [
        f"window_id: {envelope.window_id}",
        f"agent_id: {agent.id}",
        "",
        "classification:",
        json.dumps(classification_payload, ensure_ascii=False, indent=2),
        "",
        "envelope:",
        json.dumps(envelope.to_agent_payload(), ensure_ascii=False, indent=2),
        "",
        "task_messages:",
        json.dumps(agent.task_messages, ensure_ascii=False, indent=2),
        "",
        "execution_log:",
        "\n\n".join(_format_agent_log_entry(entry) for entry in agent.log),
        "",
        "custom_context:",
        json.dumps(custom_context, ensure_ascii=False, indent=2),
        "",
        "final_result:",
        final_result or "",
    ]
    trace_path.write_text("\n".join(sections), encoding="utf-8")
    return trace_path


def build_sgr_config(config: AppConfig) -> SGRAgentConfig:
    """Build SGRAgent configuration from application settings and prompt files."""

    prompts = load_prompts(config)
    return SGRAgentConfig(
        llm=LLMConfig(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            model=config.model_name,
            temperature=config.model_temperature,
        ),
        execution=ExecutionConfig(
            max_iterations=config.sgr_max_iterations,
            max_clarifications=0,
            # В режиме LangGraph ASGI библиотека пытается делать os.makedirs в конце
            # выполнения (сохранение JSON-лога), что помечается как blocking call.
            # Логи шагов остаются в stdout/file через обычный logger.
            logs_dir="",
        ),
        prompts=PromptsConfig(
            system_prompt_str=prompts["deep_system"],
            initial_user_request_str=(
                "Текущая дата: {current_date}. "
                "Выполни детальный анализ инцидента КА и заверши работу через финальный ответ."
            ),
            clarification_response_str=(
                "Текущая дата: {current_date}. "
                "Канал уточнений отключен в данном эксперименте."
            ),
        ),
    )


def _serialize_classification(classification: IncidentClassification | dict[str, Any] | None) -> dict[str, Any]:
    """Convert classification input to a plain JSON-serializable mapping."""

    if classification is None:
        return {
            "observation": "Классификация не передана",
            "evidences": [],
            "confidence_alarm": 0.0,
            "is_anomaly": False,
            "anomaly_class": "UNKNOWN",
        }
    if isinstance(classification, IncidentClassification):
        return classification.model_dump(mode="json")
    if isinstance(classification, dict):
        return classification
    raise TypeError("Некорректный тип classification для deep research")


def build_deep_user_message(
    envelope: IncidentEnvelope,
    config: AppConfig,
    classification: IncidentClassification | dict[str, Any] | None,
    recent_window_history: RecentWindowHistory | None,
) -> str:
    """Build the initial user message for the deep research agent."""

    prompts = load_prompts(config)
    classification_payload = _serialize_classification(classification)
    history_payload = recent_window_history.model_dump(mode="json") if recent_window_history is not None else {"entries": []}
    return prompts["deep_user"].format(
        payload_json=json.dumps(envelope.to_agent_payload(), ensure_ascii=False, indent=2),
        classification_json=json.dumps(classification_payload, ensure_ascii=False, indent=2),
        history_json=json.dumps(history_payload["entries"], ensure_ascii=False, indent=2),
    )


async def run_deep_research_sgr_async(
    envelope: IncidentEnvelope,
    config: AppConfig,
    classification: IncidentClassification | dict[str, Any] | None = None,
    recent_window_history: RecentWindowHistory | None = None,
) -> str:
    """Run deep research for one envelope and return the final operator report."""

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY не задан. Невозможно запустить deep analysis.")

    classification_payload = _serialize_classification(classification)
    logger.info(
        "Запуск deep research через SGRAgent для окна {}, class={}, conf={:.2f}",
        envelope.window_id,
        classification_payload.get("anomaly_class"),
        float(classification_payload.get("confidence_alarm", 0.0) or 0.0),
    )

    sgr_config = build_sgr_config(config)
    openai_client = AsyncOpenAI(api_key=config.openai_api_key, base_url=config.openai_base_url)

    agent = IncidentSGRAgent(
        task_messages=[
            {
                "role": "user",
                "content": build_deep_user_message(
                    envelope,
                    config,
                    classification_payload,
                    recent_window_history,
                ),
            }
        ],
        openai_client=openai_client,
        agent_config=sgr_config,
        toolkit=[
            InspectIncidentEnvelopeTool,
            ComputeTelemetryDiagnosticsTool,
            BuildUVPlanTool,
            FinalAnswerTool,
        ],
        def_name="space_incident_sgr",
    )
    deep_context = envelope.to_agent_payload()
    deep_context["classification_context"] = classification_payload
    deep_context["recent_window_history"] = (
        recent_window_history.model_dump(mode="json")["entries"] if recent_window_history is not None else []
    )
    agent._context.custom_context = deep_context

    result = await agent.execute()
    trace_path = _write_deep_research_trace(
        config=config,
        envelope=envelope,
        classification_payload=classification_payload,
        agent=agent,
        final_result=result if isinstance(result, str) else None,
    )
    logger.info("Полный deep trace сохранен в {}", trace_path)
    if isinstance(agent._context.custom_context, dict):
        structured_actions = agent._context.custom_context.get("deep_uv_plan_actions", [])
        if isinstance(structured_actions, list):
            envelope.precomputed_features["deep_uv_plan_actions"] = [
                str(action) for action in structured_actions if isinstance(action, str)
            ]
            logger.info(
                "Deep research structured uv_plan получен: {} действий",
                len(envelope.precomputed_features["deep_uv_plan_actions"]),
            )
        structured_details = agent._context.custom_context.get("deep_uv_plan_details", [])
        if isinstance(structured_details, list):
            envelope.precomputed_features["deep_uv_plan_details"] = [
                detail for detail in structured_details if isinstance(detail, dict)
            ]
        structured_prechecks = agent._context.custom_context.get("deep_uv_plan_prechecks", [])
        if isinstance(structured_prechecks, list):
            envelope.precomputed_features["deep_uv_plan_prechecks"] = [
                str(item) for item in structured_prechecks if isinstance(item, str)
            ]
        structured_postchecks = agent._context.custom_context.get("deep_uv_plan_postchecks", [])
        if isinstance(structured_postchecks, list):
            envelope.precomputed_features["deep_uv_plan_postchecks"] = [
                str(item) for item in structured_postchecks if isinstance(item, str)
            ]

    if isinstance(result, str) and result.strip():
        logger.info("Deep research завершен для окна {}", envelope.window_id)
        return result

    logger.warning("SGRAgent не вернул итоговый отчет для окна {}", envelope.window_id)
    return "Нет итогового отчета SGRAgent"
