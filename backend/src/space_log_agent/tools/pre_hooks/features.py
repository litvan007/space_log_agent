from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def aggregate(channel: str, window_dataframe: pd.DataFrame) -> dict[str, float | None]:
    """Возвращает агрегаты по одному каналу на окне."""
    if channel not in window_dataframe.columns:
        return {"mean": None, "std": None, "min": None, "max": None, "last": None}

    series = pd.to_numeric(window_dataframe[channel], errors="coerce").dropna()
    if series.empty:
        return {"mean": None, "std": None, "min": None, "max": None, "last": None}

    return {
        "mean": float(series.mean()),
        "std": float(series.std(ddof=0)) if len(series) > 1 else 0.0,
        "min": float(series.min()),
        "max": float(series.max()),
        "last": float(series.iloc[-1]),
    }


def aggregate_multi(channels: list[str], window_dataframe: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    """Возвращает агрегаты сразу по нескольким каналам."""
    return {channel: aggregate(channel, window_dataframe) for channel in channels}


def rolling_stats(channel: str, window_dataframe: pd.DataFrame, rolling_window: int = 5) -> dict[str, list[float]]:
    """Вычисляет rolling mean/std для канала."""
    if channel not in window_dataframe.columns:
        return {"rolling_mean": [], "rolling_std": []}

    series = pd.to_numeric(window_dataframe[channel], errors="coerce")
    rolling_mean = series.rolling(rolling_window, min_periods=1).mean().ffill().fillna(0)
    rolling_std = series.rolling(rolling_window, min_periods=1).std().fillna(0)

    return {
        "rolling_mean": [float(value) for value in rolling_mean.tolist()],
        "rolling_std": [float(value) for value in rolling_std.tolist()],
    }


def trend(channel: str, window_dataframe: pd.DataFrame) -> float:
    """Линейный тренд канала (наклон аппроксимации)."""
    if channel not in window_dataframe.columns:
        return 0.0

    series = pd.to_numeric(window_dataframe[channel], errors="coerce").dropna()
    if len(series) < 2:
        return 0.0

    x_axis = np.arange(len(series), dtype=float)
    slope, _ = np.polyfit(x_axis, series.to_numpy(dtype=float), deg=1)
    return float(slope)


def detect_change_points(channel: str, window_dataframe: pd.DataFrame, z_threshold: float = 3.0) -> list[int]:
    """Грубая детекция точек смены режима по скачкам первой разности."""
    if channel not in window_dataframe.columns:
        return []

    series = pd.to_numeric(window_dataframe[channel], errors="coerce").dropna()
    if len(series) < 3:
        return []

    diffs = series.diff().dropna()
    diff_std = float(diffs.std(ddof=0))
    if diff_std == 0:
        return []

    z_score = np.abs((diffs - diffs.mean()) / diff_std)
    points = [int(index) for index, value in zip(diffs.index, z_score) if value >= z_threshold]
    return points


def rough_anomaly_score(window_dataframe: pd.DataFrame, key_channels: list[str]) -> float:
    """Агрегированный скор аномальности окна на базе z-score и трендов."""
    scores: list[float] = []

    for channel in key_channels:
        if channel not in window_dataframe.columns:
            continue
        series = pd.to_numeric(window_dataframe[channel], errors="coerce").dropna()
        if len(series) < 3:
            continue

        mean_value = float(series.mean())
        std_value = float(series.std(ddof=0))
        if std_value <= 1e-9:
            continue

        last_z = abs((float(series.iloc[-1]) - mean_value) / std_value)
        delta = abs(float(series.iloc[-1]) - float(series.iloc[0]))
        scores.append(last_z + 0.05 * delta)

    if not scores:
        return 0.0

    # Нормализация через tanh, чтобы результат был в диапазоне [0..1].
    return float(np.tanh(np.mean(scores) / 3.0))


def summarize_events(alerts: list[str], errors: list[str]) -> dict[str, Any]:
    """Краткая сводка событий окна."""
    return {
        "alerts_count": len(alerts),
        "errors_count": len(errors),
        "alerts": alerts,
        "errors": errors,
    }


def summarize_alerts(alerts: list[str]) -> dict[str, Any]:
    """Сводка по предупреждениям."""
    return {"alerts_count": len(alerts), "alerts": alerts}


def summarize_errors(errors: list[str]) -> dict[str, Any]:
    """Сводка по ошибкам."""
    return {"errors_count": len(errors), "errors": errors}
