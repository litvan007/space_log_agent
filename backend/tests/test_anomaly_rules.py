from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_log_agent.tools.pre_hooks.anomaly_rules import (
    detect_all_anomalies,
    detect_comm_degradation,
    detect_overheating,
    detect_power_issue,
    detect_sensor_degradation,
    detect_stabilization_loss,
)

TELEMETRY_CSV_PATH = Path("/Users/litvan/Downloads/UHF_TM_notebook/uhf_telemetry.csv")


def _base_window() -> pd.DataFrame:
    """Берет реальную телеметрию и готовит рабочее окно для инъекций НС."""
    dataframe = pd.read_csv(TELEMETRY_CSV_PATH, nrows=240)
    dataframe["Timestamp"] = pd.to_datetime(dataframe["Timestamp"], utc=True, errors="coerce")
    dataframe = dataframe.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)

    # Для стабильности тестов приводим ключевые каналы к числам.
    numeric_columns = [
        "Battery_Temp",
        "NanoMind_Temp",
        "ACU2_Temp",
        "Battery_Voltage",
        "Background_RSSI",
        "X_Coarse_Spin",
        "Y_Coarse_Spin",
        "Z_Coarse_Spin",
        "ADCS_mode",
        "PD1_CSS_theta",
    ]
    for column in numeric_columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    return dataframe


def _inject_overheating(dataframe: pd.DataFrame) -> pd.DataFrame:
    mutated = dataframe.copy()
    indices = mutated.index[-25:]
    mutated.loc[indices, "Battery_Temp"] = np.linspace(250, 275, len(indices))
    mutated.loc[indices, "NanoMind_Temp"] = np.linspace(300, 322, len(indices))
    mutated.loc[indices, "ACU2_Temp"] = np.linspace(360, 383, len(indices))
    return mutated


def _inject_power_issue(dataframe: pd.DataFrame) -> pd.DataFrame:
    mutated = dataframe.copy()
    indices = mutated.index[-25:]
    mutated.loc[indices, "Battery_Voltage"] = np.linspace(8120, 7900, len(indices))
    mutated.loc[indices, "Battery_Temp"] = np.linspace(280, 295, len(indices))
    return mutated


def _inject_comm_degradation(dataframe: pd.DataFrame) -> pd.DataFrame:
    mutated = dataframe.copy()
    indices = mutated.index[-20:]
    mutated.loc[indices, "Background_RSSI"] = np.linspace(-95, -112, len(indices))

    # Эмулируем packet gap, сохраняя общую структуру окна.
    synthetic_ts = pd.date_range("2024-05-01T00:00:00Z", periods=len(mutated), freq="30s")
    synthetic_ts = pd.Series(synthetic_ts)
    synthetic_ts.iloc[-2] = synthetic_ts.iloc[-3] + pd.Timedelta(seconds=300)
    synthetic_ts.iloc[-1] = synthetic_ts.iloc[-2] + pd.Timedelta(seconds=30)
    mutated["Timestamp"] = synthetic_ts
    return mutated


def _inject_stabilization_loss(dataframe: pd.DataFrame) -> pd.DataFrame:
    mutated = dataframe.copy()
    indices = mutated.index[-20:]
    mutated.loc[indices, "X_Coarse_Spin"] = np.linspace(0.01, 0.07, len(indices))
    mutated.loc[indices, "Y_Coarse_Spin"] = np.linspace(0.00, 0.06, len(indices))
    mutated.loc[indices, "Z_Coarse_Spin"] = np.linspace(0.01, 0.08, len(indices))
    mutated.loc[indices[:10], "ADCS_mode"] = 3
    mutated.loc[indices[10:], "ADCS_mode"] = 4
    return mutated


def _inject_sensor_degradation(dataframe: pd.DataFrame) -> pd.DataFrame:
    mutated = dataframe.copy()
    indices = mutated.index[-30:]
    pattern = [0.05, 0.62, 0.08, 0.58, 0.07, 0.66] * 5
    mutated.loc[indices, "PD1_CSS_theta"] = pattern[: len(indices)]
    return mutated


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_overheating_from_real_csv_window() -> None:
    dataframe = _inject_overheating(_base_window())
    flag, evidence = detect_overheating(dataframe)
    assert flag is True
    assert evidence


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_power_issue_from_real_csv_window() -> None:
    dataframe = _inject_power_issue(_base_window())
    flag, evidence = detect_power_issue(dataframe)
    assert flag is True
    assert evidence


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_comm_degradation_from_real_csv_window() -> None:
    dataframe = _inject_comm_degradation(_base_window())
    flag, evidence = detect_comm_degradation(dataframe)
    assert flag is True
    assert evidence


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_stabilization_loss_from_real_csv_window() -> None:
    dataframe = _inject_stabilization_loss(_base_window())
    flag, evidence = detect_stabilization_loss(dataframe)
    assert flag is True
    assert evidence


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_sensor_degradation_from_real_csv_window() -> None:
    dataframe = _inject_sensor_degradation(_base_window())
    flag, evidence = detect_sensor_degradation(dataframe)
    assert flag is True
    assert evidence


@pytest.mark.skipif(not TELEMETRY_CSV_PATH.exists(), reason="Нет файла телеметрии")
def test_detect_all_anomalies_from_real_csv_window() -> None:
    dataframe = _base_window()
    dataframe = _inject_overheating(dataframe)
    dataframe = _inject_power_issue(dataframe)
    dataframe = _inject_comm_degradation(dataframe)

    alerts, errors, evidence_map = detect_all_anomalies(dataframe)

    assert "THERMAL_OVERHEAT" in alerts
    assert "POWER_DEGRADATION" in alerts
    assert "COMM_DEGRADATION" in alerts
    assert "CRITICAL_POWER_THERMAL_COUPLING" in errors
    assert evidence_map
