"""Helper utilities for the incident analysis graph."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from space_log_agent.config import AppConfig
from space_log_agent.models import (
    IncidentClassification,
    IncidentEnvelope,
    UVActionDetail,
)
from space_log_agent.runtime import IncidentRuntime

if TYPE_CHECKING:
    from space_log_agent.graph import IncidentGraphState


def build_uv_plan_markdown(details: list[UVActionDetail]) -> str:
    """Render structured UV action details as a compact markdown section."""

    if not details:
        return ""

    lines = ["\n\n### Структурированный план УВ"]
    for index, detail in enumerate(details, start=1):
        prechecks = "; ".join(detail.prechecks) if detail.prechecks else "нет"
        lines.append(
            f"{index}. {detail.action}: {detail.description} "
            f"(priority={detail.priority}; prechecks={prechecks})"
        )
    return "\n".join(lines)


def get_envelope(state: IncidentGraphState) -> IncidentEnvelope:
    """Return a validated incident envelope from graph state."""

    raw = state["envelope"]
    if isinstance(raw, IncidentEnvelope):
        return raw
    if isinstance(raw, dict):
        return IncidentEnvelope.model_validate(raw)
    raise TypeError("Некорректный тип envelope в состоянии графа")


def get_runtime(state: IncidentGraphState) -> IncidentRuntime:
    """Return shared runtime dependencies from graph state."""

    runtime = state.get("runtime")
    if isinstance(runtime, IncidentRuntime):
        return runtime
    raise TypeError("Некорректный тип runtime в состоянии графа")


def get_config(state: IncidentGraphState) -> AppConfig:
    """Return runtime configuration from graph state."""

    return get_runtime(state).config


def get_window_history_limit(state: IncidentGraphState) -> int:
    """Return the configured limit for bounded recent window history."""

    return max(1, int(getattr(get_config(state), "window_history_limit", 5)))


async def publish_event(state: IncidentGraphState, payload: dict[str, Any]) -> None:
    """Publish one progress event if a runtime handler is present."""

    handler = state.get("event_handler")
    if callable(handler):
        await handler(payload)


def get_classification(state: IncidentGraphState) -> IncidentClassification:
    """Return a validated classification from graph state."""

    raw = state["classification"]
    if isinstance(raw, IncidentClassification):
        return raw
    if isinstance(raw, dict):
        return IncidentClassification.model_validate(raw)
    raise TypeError("Некорректный тип classification в состоянии графа")
