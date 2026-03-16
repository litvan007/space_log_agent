from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd


AnalysisScenario = Literal["mixed", "thermal", "power", "adcs", "rf", "nominal"]


def apply_analysis_scenario(window_dataframe: pd.DataFrame, scenario: AnalysisScenario | None) -> pd.DataFrame:
    """Apply a deterministic anomaly scenario mutation to one telemetry window."""

    if scenario is None or scenario == "nominal" or window_dataframe.empty:
        return window_dataframe.copy()

    mutated = window_dataframe.copy()
    scenario_handlers = {
        "mixed": _inject_mixed_anomaly,
        "thermal": _inject_overheating,
        "power": _inject_power_issue,
        "adcs": _inject_stabilization_loss,
        "rf": _inject_comm_degradation,
    }
    handler = scenario_handlers.get(scenario)
    if handler is None:
        return mutated
    return handler(mutated)


def _inject_mixed_anomaly(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject a mixed anomaly combining thermal, power and communication effects."""

    mutated = _inject_overheating(dataframe)
    mutated = _inject_power_issue(mutated)
    mutated = _inject_comm_degradation(mutated)
    return _inject_sensor_degradation(mutated)


def _inject_overheating(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject overheating trends into thermal channels."""

    mutated = dataframe.copy()
    indices = mutated.index[-25:]
    if len(indices) == 0:
        return mutated

    _assign_if_present(mutated, indices, "Battery_Temp", np.linspace(250, 275, len(indices)))
    _assign_if_present(mutated, indices, "NanoMind_Temp", np.linspace(300, 322, len(indices)))
    _assign_if_present(mutated, indices, "ACU2_Temp", np.linspace(360, 383, len(indices)))
    return mutated


def _inject_power_issue(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject power degradation into battery channels."""

    mutated = dataframe.copy()
    indices = mutated.index[-25:]
    if len(indices) == 0:
        return mutated

    _assign_if_present(mutated, indices, "Battery_Voltage", np.linspace(8120, 7900, len(indices)))
    _assign_if_present(mutated, indices, "Battery_Temp", np.linspace(280, 295, len(indices)))
    return mutated


def _inject_comm_degradation(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject radio degradation and packet gaps."""

    mutated = dataframe.copy()
    indices = mutated.index[-20:]
    if len(indices) == 0:
        return mutated

    _assign_if_present(mutated, indices, "Background_RSSI", np.linspace(-95, -112, len(indices)))
    if "Timestamp" not in mutated.columns:
        return mutated

    timestamps = pd.to_datetime(mutated["Timestamp"], utc=True, errors="coerce")
    timestamps = pd.Series(timestamps)
    if len(timestamps) >= 3:
        timestamps.iloc[-2] = timestamps.iloc[-3] + pd.Timedelta(seconds=300)
        timestamps.iloc[-1] = timestamps.iloc[-2] + pd.Timedelta(seconds=30)
        mutated["Timestamp"] = timestamps
    return mutated


def _inject_stabilization_loss(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject ADCS instability into spin and mode channels."""

    mutated = dataframe.copy()
    indices = mutated.index[-20:]
    if len(indices) == 0:
        return mutated

    _assign_if_present(mutated, indices, "X_Coarse_Spin", np.linspace(0.01, 0.07, len(indices)))
    _assign_if_present(mutated, indices, "Y_Coarse_Spin", np.linspace(0.00, 0.06, len(indices)))
    _assign_if_present(mutated, indices, "Z_Coarse_Spin", np.linspace(0.01, 0.08, len(indices)))
    if "ADCS_mode" in mutated.columns:
        half = len(indices) // 2
        mutated.loc[indices[:half], "ADCS_mode"] = 3
        mutated.loc[indices[half:], "ADCS_mode"] = 4
    return mutated


def _inject_sensor_degradation(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Inject noise and spikes into CSS telemetry."""

    mutated = dataframe.copy()
    indices = mutated.index[-30:]
    if len(indices) == 0 or "PD1_CSS_theta" not in mutated.columns:
        return mutated

    pattern = [0.05, 0.62, 0.08, 0.58, 0.07, 0.66] * 5
    mutated.loc[indices, "PD1_CSS_theta"] = pattern[: len(indices)]
    return mutated


def _assign_if_present(
    dataframe: pd.DataFrame,
    indices: pd.Index,
    column: str,
    values: np.ndarray,
) -> None:
    """Assign mutation values only when the telemetry column exists."""

    if column in dataframe.columns:
        dataframe.loc[indices, column] = values
