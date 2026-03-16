from __future__ import annotations

from datetime import UTC

import pandas as pd
from loguru import logger


TELEMETRY_NUMERIC_COLUMNS = [
    "X_Coarse_Spin",
    "Y_Coarse_Spin",
    "Z_Coarse_Spin",
    "PD1_CSS_theta",
    "PD2_CSS_theta",
    "PD3_CSS_theta",
    "PD4_CSS_theta",
    "PD5_CSS_theta",
    "PD6_CSS_theta",
    "HD_Cam_Temp",
    "ACU2_Temp",
    "Battery_Temp",
    "Battery_Voltage",
    "NanoMind_Temp",
    "PDU_Channels_Status",
    "SDR_Temp",
    "SEPP_Temp",
    "Background_RSSI",
    "Last_RSSI",
    "NanoCom_Temp",
    "ADCS_mode",
]


def load_telemetry_dataframe(csv_path: str) -> pd.DataFrame:
    """Загружает сырую телеметрию из CSV."""
    logger.debug("Загрузка телеметрии из {}", csv_path)
    dataframe = pd.read_csv(csv_path)
    if "Timestamp" not in dataframe.columns:
        raise ValueError("В телеметрии отсутствует колонка Timestamp")

    dataframe["Timestamp"] = pd.to_datetime(dataframe["Timestamp"], errors="coerce", utc=True)
    dataframe = dataframe.dropna(subset=["Timestamp"]).sort_values("Timestamp").reset_index(drop=True)

    for column in TELEMETRY_NUMERIC_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    logger.debug("Телеметрия загружена: {} строк", len(dataframe))
    return dataframe


def normalize_resample_forward_fill(dataframe: pd.DataFrame, resample_freq: str) -> pd.DataFrame:
    """Нормализует временную шкалу, выполняет resample и forward fill."""
    if dataframe.empty:
        return dataframe.copy()

    indexed = dataframe.set_index("Timestamp").sort_index()

    # Сначала берем первый пакет в каждом интервале, затем заполняем пропуски предыдущими значениями.
    regular = indexed.resample(resample_freq).first().ffill()
    regular = regular.dropna(how="all").reset_index()
    logger.debug("Нормализованная телеметрия: {} строк, частота {}", len(regular), resample_freq)
    return regular


def iterate_windows(dataframe: pd.DataFrame, window_minutes: int, step_minutes: int):
    """Итерирует окна инцидентов по нормализованной телеметрии."""
    if dataframe.empty:
        return

    indexed = dataframe.set_index("Timestamp").sort_index()
    start = indexed.index.min()
    finish = indexed.index.max()

    window_delta = pd.Timedelta(minutes=window_minutes)
    step_delta = pd.Timedelta(minutes=step_minutes)

    cursor = start
    while cursor <= finish:
        window_end = cursor + window_delta
        chunk = indexed[(indexed.index >= cursor) & (indexed.index < window_end)]
        if not chunk.empty:
            yield cursor.to_pydatetime().astimezone(UTC), window_end.to_pydatetime().astimezone(UTC), chunk.reset_index()
        cursor += step_delta
