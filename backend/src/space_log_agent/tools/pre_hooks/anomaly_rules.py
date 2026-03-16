from __future__ import annotations

import numpy as np
import pandas as pd


def _to_series(window_dataframe: pd.DataFrame, channel: str) -> pd.Series:
    if channel not in window_dataframe.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(window_dataframe[channel], errors="coerce").dropna()


def detect_overheating(window_dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    battery = _to_series(window_dataframe, "Battery_Temp")
    nanomind = _to_series(window_dataframe, "NanoMind_Temp")
    acu2 = _to_series(window_dataframe, "ACU2_Temp")

    evidence: list[str] = []
    if len(battery) >= 2 and (battery.iloc[-1] - battery.iloc[0]) > 10:
        evidence.append("Battery_Temp растет в пределах окна")
    if len(nanomind) >= 2 and (nanomind.iloc[-1] - nanomind.iloc[0]) > 8:
        evidence.append("NanoMind_Temp растет в пределах окна")
    if len(acu2) >= 2 and (acu2.iloc[-1] - acu2.iloc[0]) > 8:
        evidence.append("ACU2_Temp растет в пределах окна")

    return len(evidence) >= 2, evidence


def detect_power_issue(window_dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    voltage = _to_series(window_dataframe, "Battery_Voltage")
    battery_temp = _to_series(window_dataframe, "Battery_Temp")

    evidence: list[str] = []
    if len(voltage) >= 2 and (voltage.iloc[-1] - voltage.iloc[0]) < -80:
        evidence.append("Battery_Voltage заметно снижается")
    if len(battery_temp) >= 2 and (battery_temp.iloc[-1] - battery_temp.iloc[0]) > 8:
        evidence.append("Battery_Temp одновременно растет")

    return len(evidence) >= 1, evidence


def detect_comm_degradation(window_dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    rssi = _to_series(window_dataframe, "Background_RSSI")
    evidence: list[str] = []

    if len(rssi) >= 2 and (rssi.iloc[-1] - rssi.iloc[0]) < -8:
        evidence.append("Background_RSSI деградирует")

    if "Timestamp" in window_dataframe.columns and len(window_dataframe) >= 3:
        timestamps = pd.to_datetime(window_dataframe["Timestamp"], utc=True, errors="coerce").dropna()
        if len(timestamps) >= 3:
            gaps = timestamps.diff().dropna().dt.total_seconds()
            if not gaps.empty and float(gaps.max()) > 3 * float(gaps.median()):
                evidence.append("Обнаружены packet gaps")

    return len(evidence) >= 1, evidence


def detect_stabilization_loss(window_dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    x_spin = _to_series(window_dataframe, "X_Coarse_Spin")
    y_spin = _to_series(window_dataframe, "Y_Coarse_Spin")
    z_spin = _to_series(window_dataframe, "Z_Coarse_Spin")

    evidence: list[str] = []
    if len(x_spin) >= 2 and len(y_spin) >= 2 and len(z_spin) >= 2:
        start_norm = float(np.linalg.norm([x_spin.iloc[0], y_spin.iloc[0], z_spin.iloc[0]]))
        end_norm = float(np.linalg.norm([x_spin.iloc[-1], y_spin.iloc[-1], z_spin.iloc[-1]]))
        if (end_norm - start_norm) > 0.04:
            evidence.append("Наблюдается рост суммарного spin")

    adcs_mode = _to_series(window_dataframe, "ADCS_mode")
    if len(adcs_mode) >= 2 and adcs_mode.nunique() > 1:
        evidence.append("ADCS_mode изменился в пределах окна")

    return len(evidence) >= 1, evidence


def detect_sensor_degradation(window_dataframe: pd.DataFrame) -> tuple[bool, list[str]]:
    css = _to_series(window_dataframe, "PD1_CSS_theta")
    evidence: list[str] = []

    if len(css) >= 5:
        std_value = float(css.std(ddof=0))
        if std_value > 0.2:
            evidence.append("PD1_CSS_theta имеет повышенный шум")

        spikes = (css - css.rolling(5, min_periods=1).mean()).abs()
        if float(spikes.max()) > 0.4:
            evidence.append("Зафиксированы spikes в CSS")

    return len(evidence) >= 1, evidence


def detect_all_anomalies(window_dataframe: pd.DataFrame) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Возвращает alerts, errors и объяснения по признакам."""
    alerts: list[str] = []
    errors: list[str] = []
    evidence_map: dict[str, list[str]] = {}

    checks = {
        "THERMAL_OVERHEAT": detect_overheating(window_dataframe),
        "POWER_DEGRADATION": detect_power_issue(window_dataframe),
        "COMM_DEGRADATION": detect_comm_degradation(window_dataframe),
        "ADCS_STABILIZATION_LOSS": detect_stabilization_loss(window_dataframe),
        "SENSOR_DEGRADATION": detect_sensor_degradation(window_dataframe),
    }

    for label, (flag, evidence) in checks.items():
        if flag:
            alerts.append(label)
            evidence_map[label] = evidence

    if "POWER_DEGRADATION" in alerts and "THERMAL_OVERHEAT" in alerts:
        errors.append("CRITICAL_POWER_THERMAL_COUPLING")

    return alerts, errors, evidence_map
