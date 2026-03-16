from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from loguru import logger

from space_log_agent.agent import run_deep_research_sgr_async
from space_log_agent.config import load_prompts
from space_log_agent.graph_helpers import (
    build_uv_plan_markdown,
    get_classification,
    get_config,
    get_envelope,
    get_runtime,
    get_window_history_limit,
    publish_event,
)
from space_log_agent.models import (
    IncidentClassification,
    IncidentEnvelope,
    RecentWindowHistory,
    UVActionDetail,
    UVPostCheck,
)
from space_log_agent.runtime import IncidentRuntime
from space_log_agent.tools.pre_hooks.incident_envelope import enrich_incident_envelope
from space_log_agent.tools.pre_hooks.uv_post_hook import (
    extract_uv_actions_from_report,
    verify_uv_plan,
)
from space_log_agent.window_history.history_utils import (
    append_history_entry,
    build_window_history_entry,
    format_nominal_history_summary,
    get_recent_window_history,
    serialize_recent_window_history,
)


class IncidentGraphState(TypedDict, total=False):
    """State container for the incident analysis graph."""

    envelope: IncidentEnvelope | dict
    runtime: IncidentRuntime
    event_handler: Callable[[dict[str, Any]], Awaitable[None]]
    classification: IncidentClassification | dict
    deep_report: str
    deep_uv_plan_actions: list[str]
    deep_uv_plan_details: list[dict[str, Any]]
    uv_post_check: UVPostCheck
    final_output: str
    recent_window_history: RecentWindowHistory | dict[str, Any]


async def classification_node(state: IncidentGraphState) -> IncidentGraphState:
    """Нода первичной классификации состояния КА через structured output."""
    envelope = get_envelope(state)
    runtime = get_runtime(state)
    prompts = load_prompts(runtime.config)
    history_limit = get_window_history_limit(state)
    recent_window_history = get_recent_window_history(
        state.get("recent_window_history"),
        history_limit,
    )

    messages = [
        ("system", prompts["classification_system"]),
        (
            "user",
            "Классифицируй окно НС строго по схеме.\n"
            "Текущее окно:\n"
            + json.dumps(envelope.to_agent_payload(), ensure_ascii=False, indent=2)
            + "\n\n"
            + "Краткая история предыдущих окон"
            + " (вспомогательный контекст, не замещающий факты текущего окна):\n"
            + json.dumps(
                serialize_recent_window_history(recent_window_history, history_limit),
                ensure_ascii=False,
                indent=2,
            ),
        ),
    ]

    classification = await runtime.classification_llm.ainvoke(messages)
    logger.info(
        "Классификация окна {}: anomaly={}, confidence={:.2f}, class={}, observation='{}', evidences={}",
        envelope.window_id,
        classification.is_anomaly,
        classification.confidence_alarm,
        classification.anomaly_class,
        classification.observation,
        classification.evidences,
    )
    await publish_event(
        state,
        {
            "node": "classification",
            "status": "completed",
            "classification": classification.model_dump(mode="json"),
            "recent_window_history": serialize_recent_window_history(
                recent_window_history,
                history_limit,
            ),
        },
    )
    return {"classification": classification}


async def pre_hook_node(state: IncidentGraphState) -> IncidentGraphState:
    """Предварительная нода: прогон deterministic pre-hooks по окну."""
    envelope = get_envelope(state)
    config = get_config(state)
    # Pre-hooks используют pandas/skyfield и синхронный I/O, выносим в thread pool,
    # чтобы не блокировать event loop LangGraph ASGI.
    enriched = await asyncio.to_thread(enrich_incident_envelope, envelope, config)
    await publish_event(
        state,
        {
            "node": "pre_hook",
            "status": "completed",
            "envelope": enriched.model_dump(mode="json"),
        },
    )
    return {"envelope": enriched}


def route_after_classification(state: IncidentGraphState) -> str:
    """Choose the next graph branch from classification confidence."""

    classification = get_classification(state)
    threshold = get_config(state).anomaly_threshold
    if classification.is_anomaly and classification.confidence_alarm >= threshold:
        return "deep_research"
    return "nominal_summary"


async def nominal_summary_node(state: IncidentGraphState) -> IncidentGraphState:
    """Build a short report for nominal telemetry windows."""

    envelope = get_envelope(state)
    classification = get_classification(state)
    history_limit = get_window_history_limit(state)
    recent_window_history = get_recent_window_history(
        state.get("recent_window_history"),
        history_limit,
    )
    history_summary = format_nominal_history_summary(recent_window_history)

    summary = (
        "Краткий отчет\n"
        f"Окно: {envelope.window_id}\n"
        f"Период: {envelope.timestamp_start.isoformat()} - {envelope.timestamp_end.isoformat()}\n"
        f"Классификация: {classification.anomaly_class}\n"
        f"Уверенность тревоги: {classification.confidence_alarm:.2f}\n"
        "Решение: глубокий анализ не требуется."
    )
    if history_summary:
        summary += "\n" + history_summary

    updated_history = append_history_entry(
        state.get("recent_window_history"),
        build_window_history_entry(
            envelope=envelope,
            classification=classification,
            analysis_branch="nominal",
        ),
        history_limit,
    )
    await publish_event(
        state,
        {
            "node": "nominal_summary",
            "status": "completed",
            "final_output": summary,
            "recent_window_history": serialize_recent_window_history(
                updated_history,
                history_limit,
            ),
        },
    )
    return {"final_output": summary, "recent_window_history": updated_history}


async def deep_research_node(state: IncidentGraphState) -> IncidentGraphState:
    """Run deep research for anomaly windows."""

    envelope = get_envelope(state)
    history_limit = get_window_history_limit(state)
    report = await run_deep_research_sgr_async(
        envelope=envelope,
        config=get_config(state),
        classification=get_classification(state),
        recent_window_history=get_recent_window_history(
            state.get("recent_window_history"),
            history_limit,
        ),
    )
    structured_actions = envelope.precomputed_features.get("deep_uv_plan_actions", []) or []
    if not isinstance(structured_actions, list):
        structured_actions = []
    structured_details_raw = envelope.precomputed_features.get("deep_uv_plan_details", []) or []
    if not isinstance(structured_details_raw, list):
        structured_details_raw = []
    structured_details = [
        UVActionDetail.model_validate(detail).model_dump(mode="json")
        for detail in structured_details_raw
    ]
    await publish_event(
        state,
        {
            "node": "deep_research",
            "status": "completed",
            "deep_report": report,
            "deep_uv_plan_actions": [str(action) for action in structured_actions],
            "deep_uv_plan_details": structured_details,
            "recent_window_history": serialize_recent_window_history(
                get_recent_window_history(state.get("recent_window_history"), history_limit),
                history_limit,
            ),
        },
    )
    return {
        "deep_report": report,
        "deep_uv_plan_actions": [str(action) for action in structured_actions],
        "deep_uv_plan_details": structured_details,
    }


async def post_hook_node(state: IncidentGraphState) -> IncidentGraphState:
    """Validate the generated UV plan and append post-hook results."""

    envelope = get_envelope(state)
    deep_report = state.get("deep_report", "")
    classification = get_classification(state)
    history_limit = get_window_history_limit(state)

    uv_actions = state.get("deep_uv_plan_actions", []) or []
    if not uv_actions:
        uv_actions = extract_uv_actions_from_report(deep_report)
    details_source = (
        state.get("deep_uv_plan_details", [])
        or envelope.precomputed_features.get("deep_uv_plan_details", [])
        or []
    )
    uv_action_details = [
        UVActionDetail.model_validate(detail)
        for detail in details_source
        if isinstance(detail, dict)
    ]
    post_check = verify_uv_plan(envelope=envelope, uv_actions=uv_actions)

    logger.info(
        "Post-hook валидация окна {}: valid={}, actions={}",
        envelope.window_id,
        post_check.valid,
        len(uv_actions),
    )

    post_hook_text = (
        "\n\n### Проверка плана (post_hook)\n"
        f"- valid: {'true' if post_check.valid else 'false'}\n"
        f"- actions: {', '.join(uv_actions) if uv_actions else 'не извлечены'}\n"
        f"- constraints: {post_check.constraints if post_check.constraints else ['нет']}\n"
        f"- recommendations: {post_check.recommendations if post_check.recommendations else ['нет']}"
    )

    final_output = (
        deep_report + build_uv_plan_markdown(uv_action_details) + post_hook_text
        if deep_report
        else post_hook_text
    )
    updated_history = append_history_entry(
        state.get("recent_window_history"),
        build_window_history_entry(
            envelope=envelope,
            classification=classification,
            analysis_branch="deep",
            proposed_uv_actions=uv_actions,
            uv_post_check=post_check,
        ),
        history_limit,
    )
    await publish_event(
        state,
        {
            "node": "post_hook",
            "status": "completed",
            "uv_post_check": post_check.model_dump(mode="json"),
            "deep_uv_plan_details": [
                detail.model_dump(mode="json")
                for detail in uv_action_details
            ],
            "final_output": final_output,
            "recent_window_history": serialize_recent_window_history(
                updated_history,
                history_limit,
            ),
        },
    )
    return {
        "uv_post_check": post_check,
        "final_output": final_output,
        "recent_window_history": updated_history,
    }


def build_incident_graph():
    """Assemble and compile the incident analysis graph."""

    builder = StateGraph(IncidentGraphState)
    builder.add_node("pre_hook", pre_hook_node)
    builder.add_node("classification", classification_node)
    builder.add_node("nominal_summary", nominal_summary_node)
    builder.add_node("deep_research", deep_research_node)
    builder.add_node("post_hook", post_hook_node)
    builder.set_entry_point("pre_hook")
    builder.add_edge("pre_hook", "classification")
    builder.add_conditional_edges(
        "classification",
        route_after_classification,
        {
            "nominal_summary": "nominal_summary",
            "deep_research": "deep_research",
        },
    )
    builder.add_edge("nominal_summary", END)
    builder.add_edge("deep_research", "post_hook")
    builder.add_edge("post_hook", END)
    return builder.compile()


INCIDENT_GRAPH = build_incident_graph()


async def analyze_incident_envelope_result_async(
    envelope: IncidentEnvelope,
    runtime: IncidentRuntime,
    event_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> IncidentGraphState:
    """Analyze one incident envelope and return the resulting graph state."""

    return await analyze_incident_envelope_with_history_async(
        envelope=envelope,
        runtime=runtime,
        recent_window_history=None,
        event_handler=event_handler,
    )


async def analyze_incident_envelope_with_history_async(
    envelope: IncidentEnvelope,
    runtime: IncidentRuntime,
    recent_window_history: RecentWindowHistory | None = None,
    event_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> IncidentGraphState:
    """Analyze one incident envelope with optional recent window history."""

    state: IncidentGraphState = {"envelope": envelope, "runtime": runtime}
    if recent_window_history is not None:
        state["recent_window_history"] = recent_window_history
    if event_handler is not None:
        state["event_handler"] = event_handler
    return await INCIDENT_GRAPH.ainvoke(state)


async def analyze_incident_envelope_async(
    envelope: IncidentEnvelope,
    runtime: IncidentRuntime,
    recent_window_history: RecentWindowHistory | None = None,
    event_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> str:
    """Analyze one incident envelope with shared runtime dependencies."""

    result = await analyze_incident_envelope_with_history_async(
        envelope=envelope,
        runtime=runtime,
        recent_window_history=recent_window_history,
        event_handler=event_handler,
    )
    final_output = result.get("final_output")
    if isinstance(final_output, str) and final_output.strip():
        return final_output
    return "Нет результата графа"


async def analyze_incident_envelopes_async(
    envelopes: list[IncidentEnvelope],
    runtime: IncidentRuntime,
) -> list[str]:
    """Analyze multiple incident envelopes sequentially with shared runtime."""

    results: list[str] = []
    recent_window_history = RecentWindowHistory()
    history_limit = max(
        1,
        int(getattr(getattr(runtime, "config", None), "window_history_limit", 5)),
    )
    for envelope in envelopes:
        result = await analyze_incident_envelope_with_history_async(
            envelope=envelope,
            runtime=runtime,
            recent_window_history=recent_window_history,
        )
        final_output = result.get("final_output")
        if isinstance(final_output, str) and final_output.strip():
            results.append(final_output)
        else:
            results.append("Нет результата графа")
        recent_window_history = get_recent_window_history(
            result.get("recent_window_history"),
            history_limit,
        )
    return results
