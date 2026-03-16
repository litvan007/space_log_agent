from __future__ import annotations

import re

from space_log_agent.models import IncidentEnvelope, UVPostCheck


KNOWN_UV_ACTIONS = [
    "ENTER_SAFE_MODE",
    "LIMIT_PAYLOAD_POWER",
    "SWITCH_TO_REDUNDANT_SYSTEM",
    "RESTART_SUBSYSTEM",
    "RUN_DIAGNOSTICS",
    "INCREASE_TELEMETRY_RATE",
    "PREPARE_SAFE_MODE",
    "RUN_ADCS_DIAGNOSTICS",
    "REPEAT_CONTACT_SESSION",
]


def extract_uv_actions_from_report(report: str) -> list[str]:
    """Извлекает список УВ из текстового deep research отчета."""
    if not report.strip():
        return []

    found: list[str] = []
    for action in KNOWN_UV_ACTIONS:
        if re.search(rf"\b{re.escape(action)}\b", report):
            found.append(action)
    return found


def verify_uv_plan(envelope: IncidentEnvelope, uv_actions: list[str]) -> UVPostCheck:
    """Проверяет выполнимость плана УВ по орбитальному и событийному контексту."""
    constraints: list[str] = []
    recommendations: list[str] = []

    alerts = envelope.alerts
    orbit = envelope.orbit_context
    rough_score = float(envelope.precomputed_features.get("rough_anomaly_score", 0.0) or 0.0)

    if not uv_actions:
        constraints.append("План УВ пустой")
        recommendations.append("Сформировать минимум одно управляющее воздействие")

    if orbit.ground_station_visible is False and "INCREASE_TELEMETRY_RATE" in uv_actions:
        constraints.append("Нет видимости НС для INCREASE_TELEMETRY_RATE")
        recommendations.append("Перенести INCREASE_TELEMETRY_RATE на следующее окно связи")

    if "POWER_DEGRADATION" in alerts and "INCREASE_TELEMETRY_RATE" in uv_actions:
        constraints.append("INCREASE_TELEMETRY_RATE конфликтует с деградацией энергосистемы")
        recommendations.append("Сначала LIMIT_PAYLOAD_POWER, затем повторная оценка канала")

    if rough_score > 0.8 and "ENTER_SAFE_MODE" not in uv_actions:
        recommendations.append("Рассмотреть ENTER_SAFE_MODE из-за высокого anomaly score")

    valid = len(constraints) == 0
    return UVPostCheck(valid=valid, constraints=constraints, recommendations=recommendations)
