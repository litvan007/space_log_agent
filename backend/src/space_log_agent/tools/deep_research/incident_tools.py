from __future__ import annotations

import json
from typing import Literal

import numpy as np
import pandas as pd
from loguru import logger
from pydantic import Field
from sgr_agent_core.agents.sgr_agent import SGRAgent
from sgr_agent_core.base_tool import BaseTool
from sgr_agent_core.next_step_tool import NextStepToolStub, NextStepToolsBuilder
from sgr_agent_core.tools import FinalAnswerTool

from space_log_agent.models import UVActionDetail


UV_ACTION_CATALOG: dict[str, dict[str, str]] = {
    "LIMIT_PAYLOAD_POWER": {
        "description": "Снизить нагрузку полезной нагрузки для разгрузки EPS и теплового контура.",
        "priority": "HIGH",
    },
    "PREPARE_SAFE_MODE": {
        "description": "Подготовить безопасный режим без немедленного переключения.",
        "priority": "MEDIUM",
    },
    "RUN_DIAGNOSTICS": {
        "description": "Запустить встроенную диагностику подсистем и каналов телеметрии.",
        "priority": "MEDIUM",
    },
    "INCREASE_TELEMETRY_RATE": {
        "description": "Повысить частоту телеметрии на ближайшем доступном сеансе связи.",
        "priority": "MEDIUM",
    },
    "REPEAT_CONTACT_SESSION": {
        "description": "Запланировать повторный сеанс связи в ближайшем окне видимости.",
        "priority": "MEDIUM",
    },
    "RUN_ADCS_DIAGNOSTICS": {
        "description": "Проверить стабилизацию, датчики и исполнительные органы ADCS.",
        "priority": "HIGH",
    },
    "SWITCH_TO_REDUNDANT_SYSTEM": {
        "description": "Перевести деградирующий канал или датчик на резервный контур.",
        "priority": "MEDIUM",
    },
    "ENTER_SAFE_MODE": {
        "description": "Перевести КА в безопасный режим для остановки деградации состояния.",
        "priority": "HIGH",
    },
}


def build_uv_action_details(
    actions: list[str],
    prechecks: list[str],
    postchecks: list[str],
) -> list[UVActionDetail]:
    """Build structured UV action descriptions from the action catalog."""

    details: list[UVActionDetail] = []
    for action in actions:
        catalog_item = UV_ACTION_CATALOG.get(action, {})
        details.append(
            UVActionDetail(
                action=action,
                description=catalog_item.get("description", "Описание действия формируется агентом."),
                priority=catalog_item.get("priority", "MEDIUM"),
                prechecks=list(prechecks),
                postchecks=list(postchecks),
            )
        )
    return details


class InspectIncidentEnvelopeTool(BaseTool):
    """Извлекает нужные поля IncidentEnvelope для дальнейшего анализа."""

    reasoning: str = Field(description="Почему выбран этот фрагмент данных")
    focus: Literal[
        "telemetry_summary",
        "alerts",
        "errors",
        "orbit_context",
        "precomputed_features",
        "all",
    ] = Field(default="all")

    async def __call__(self, context, config, **_) -> str:
        payload = context.custom_context or {}
        if not isinstance(payload, dict):
            return json.dumps({"error": "custom_context не является словарем"}, ensure_ascii=False)

        selected = payload if self.focus == "all" else {self.focus: payload.get(self.focus)}
        logger.debug("InspectIncidentEnvelopeTool выполнен, focus={}", self.focus)
        return json.dumps({"focus": self.focus, "selected": selected}, ensure_ascii=False, indent=2)


class ComputeTelemetryDiagnosticsTool(BaseTool):
    """Вычисляет диагностические метрики по реальным телеметрическим данным окна."""

    reasoning: str = Field(description="Зачем нужна диагностика по сырым данным")
    channels: list[str] = Field(
        default_factory=lambda: [
            "Battery_Temp",
            "Battery_Voltage",
            "NanoMind_Temp",
            "ACU2_Temp",
            "Background_RSSI",
            "X_Coarse_Spin",
            "Y_Coarse_Spin",
            "Z_Coarse_Spin",
        ],
        min_length=1,
        max_length=12,
    )

    async def __call__(self, context, config, **_) -> str:
        payload = context.custom_context or {}
        if not isinstance(payload, dict):
            return json.dumps({"error": "custom_context не является словарем"}, ensure_ascii=False)

        telemetry_path = payload.get("raw_telemetry_ref")
        timestamp_start = payload.get("timestamp_start")
        timestamp_end = payload.get("timestamp_end")

        if not telemetry_path:
            logger.warning("ComputeTelemetryDiagnosticsTool: отсутствует raw_telemetry_ref")
            return json.dumps({"error": "raw_telemetry_ref отсутствует"}, ensure_ascii=False)

        dataframe = pd.read_csv(telemetry_path)
        if "Timestamp" not in dataframe.columns:
            return json.dumps({"error": "В CSV отсутствует Timestamp"}, ensure_ascii=False)

        dataframe["Timestamp"] = pd.to_datetime(dataframe["Timestamp"], utc=True, errors="coerce")
        dataframe = dataframe.dropna(subset=["Timestamp"]).sort_values("Timestamp")

        if timestamp_start and timestamp_end:
            left = pd.to_datetime(timestamp_start, utc=True, errors="coerce")
            right = pd.to_datetime(timestamp_end, utc=True, errors="coerce")
            if pd.notna(left) and pd.notna(right):
                dataframe = dataframe[(dataframe["Timestamp"] >= left) & (dataframe["Timestamp"] <= right)]

        diagnostics: dict[str, dict[str, float | None]] = {}
        for channel in self.channels:
            if channel not in dataframe.columns:
                continue
            series = pd.to_numeric(dataframe[channel], errors="coerce").dropna()
            if len(series) < 2:
                diagnostics[channel] = {
                    "mean": float(series.mean()) if len(series) else None,
                    "std": None,
                    "delta": None,
                    "slope": None,
                }
                continue

            x_axis = np.arange(len(series), dtype=float)
            slope, _ = np.polyfit(x_axis, series.to_numpy(dtype=float), 1)
            diagnostics[channel] = {
                "mean": float(series.mean()),
                "std": float(series.std(ddof=0)),
                "delta": float(series.iloc[-1] - series.iloc[0]),
                "slope": float(slope),
            }

        # Считаем грубые подскоры подсистем из диагностик.
        subsystem_scores = {
            "THERMAL": 0.0,
            "POWER": 0.0,
            "RF": 0.0,
            "ADCS": 0.0,
        }

        bt = diagnostics.get("Battery_Temp", {}).get("delta")
        nt = diagnostics.get("NanoMind_Temp", {}).get("delta")
        at = diagnostics.get("ACU2_Temp", {}).get("delta")
        if bt is not None:
            subsystem_scores["THERMAL"] += max(0.0, bt / 20.0)
        if nt is not None:
            subsystem_scores["THERMAL"] += max(0.0, nt / 20.0)
        if at is not None:
            subsystem_scores["THERMAL"] += max(0.0, at / 20.0)

        bv = diagnostics.get("Battery_Voltage", {}).get("delta")
        if bv is not None:
            subsystem_scores["POWER"] += max(0.0, -bv / 250.0)

        rssi = diagnostics.get("Background_RSSI", {}).get("delta")
        if rssi is not None:
            subsystem_scores["RF"] += max(0.0, -rssi / 20.0)

        xs = diagnostics.get("X_Coarse_Spin", {}).get("delta")
        ys = diagnostics.get("Y_Coarse_Spin", {}).get("delta")
        zs = diagnostics.get("Z_Coarse_Spin", {}).get("delta")
        for spin_delta in (xs, ys, zs):
            if spin_delta is not None:
                subsystem_scores["ADCS"] += max(0.0, spin_delta / 0.08)

        result = {
            "channels_analyzed": self.channels,
            "samples_in_window": int(len(dataframe)),
            "diagnostics": diagnostics,
            "subsystem_scores": subsystem_scores,
        }
        logger.debug("ComputeTelemetryDiagnosticsTool выполнен, выборка={}", len(dataframe))
        return json.dumps(result, ensure_ascii=False, indent=2)


class BuildUVPlanTool(BaseTool):
    """Формирует проект плана УВ на основе признаков НС."""

    reasoning: str = Field(description="Логика построения плана УВ")
    preferred_actions: list[str] = Field(default_factory=list, max_length=8)
    conservative_mode: bool = Field(default=True)

    async def __call__(self, context, config, **_) -> str:
        """Build a constrained UV plan from alerts, errors, and orbit context."""

        payload = context.custom_context or {}
        if not isinstance(payload, dict):
            return json.dumps({"error": "custom_context не является словарем"}, ensure_ascii=False)

        alerts = payload.get("alerts", []) or []
        errors = payload.get("errors", []) or []
        orbit_context = payload.get("orbit_context", {}) or {}
        ground_station_visible = orbit_context.get("ground_station_visible")
        actions: list[str] = []
        if "THERMAL_OVERHEAT" in alerts:
            actions.extend(["LIMIT_PAYLOAD_POWER", "PREPARE_SAFE_MODE"])
        if "POWER_DEGRADATION" in alerts:
            actions.extend(["LIMIT_PAYLOAD_POWER", "RUN_DIAGNOSTICS"])
        if "COMM_DEGRADATION" in alerts:
            if ground_station_visible is True and "POWER_DEGRADATION" not in alerts:
                actions.append("INCREASE_TELEMETRY_RATE")
            if ground_station_visible is True:
                actions.append("REPEAT_CONTACT_SESSION")
        if "ADCS_STABILIZATION_LOSS" in alerts:
            actions.extend(["RUN_ADCS_DIAGNOSTICS", "PREPARE_SAFE_MODE"])
        if "SENSOR_DEGRADATION" in alerts:
            actions.extend(["SWITCH_TO_REDUNDANT_SYSTEM", "RUN_DIAGNOSTICS"])

        if errors:
            actions.append("ENTER_SAFE_MODE")

        for action in self.preferred_actions:
            if action not in actions:
                actions.append(action)

        # Удаляем дубликаты, сохраняя порядок.
        dedup_actions: list[str] = []
        for action in actions:
            if action not in dedup_actions:
                dedup_actions.append(action)

        if ground_station_visible is not True:
            dedup_actions = [
                action
                for action in dedup_actions
                if action not in {"INCREASE_TELEMETRY_RATE", "REPEAT_CONTACT_SESSION"}
            ]

        if "POWER_DEGRADATION" in alerts:
            dedup_actions = [action for action in dedup_actions if action != "INCREASE_TELEMETRY_RATE"]

        if self.conservative_mode and "ENTER_SAFE_MODE" not in dedup_actions and len(errors) > 0:
            dedup_actions.append("ENTER_SAFE_MODE")

        prechecks = [
            "Проверить доступный энергобаланс EPS",
            "Проверить активный режим ADCS",
            "Проверить термозапас ключевых подсистем",
        ]
        postchecks = [
            "Подтвердить стабилизацию температур",
            "Проверить восстановление RSSI/телеметрии",
            "Проверить отсутствие новых error codes",
        ]
        action_details = build_uv_action_details(dedup_actions, prechecks, postchecks)

        result = {
            "alerts": alerts,
            "errors": errors,
            "uv_plan": dedup_actions,
            "uv_plan_details": [detail.model_dump(mode="json") for detail in action_details],
            "prechecks": prechecks,
            "postchecks": postchecks,
        }
        # Передаем structured-план в контекст агента для post_hook ноды графа.
        payload["deep_uv_plan_actions"] = dedup_actions
        payload["deep_uv_plan_details"] = [detail.model_dump(mode="json") for detail in action_details]
        payload["deep_uv_plan_prechecks"] = prechecks
        payload["deep_uv_plan_postchecks"] = postchecks
        context.custom_context = payload
        logger.debug("BuildUVPlanTool выполнен, УВ={}", len(dedup_actions))
        return json.dumps(result, ensure_ascii=False, indent=2)


class IncidentSGRAgent(SGRAgent):
    """Кастомный SGRAgent для deep research инцидентов КА."""

    async def _prepare_tools(self) -> type[NextStepToolStub]:
        tools = set(self.toolkit)
        if self._context.iteration >= self.config.execution.max_iterations:
            tools = {FinalAnswerTool}
        return NextStepToolsBuilder.build_NextStepTools(list(tools))
