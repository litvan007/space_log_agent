from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOGS_DIR = (PROJECT_ROOT / "logs").resolve()
DEFAULT_LOG_FILE = (DEFAULT_LOGS_DIR / "space_agent.log").resolve()

DEFAULT_TELEMETRY_CSV_PATH = Path("/Users/litvan/Downloads/UHF_TM_notebook/uhf_telemetry.csv")
DEFAULT_TLE_PATH = Path("/Users/litvan/Downloads/UHF_TM_notebook/tle_opssat.txt")

DEFAULT_CLASSIFICATION_PROMPT_PATH = (PROJECT_ROOT / "src/space_log_agent/prompts/classification_system.txt").resolve()
DEFAULT_DEEP_SYSTEM_PROMPT_PATH = (PROJECT_ROOT / "src/space_log_agent/prompts/deep_system.txt").resolve()
DEFAULT_DEEP_USER_PROMPT_PATH = (PROJECT_ROOT / "src/space_log_agent/prompts/deep_user.txt").resolve()


def _abs_path(path_value: Path) -> Path:
    """Resolve relative application paths against the project root."""

    if path_value.is_absolute():
        return path_value
    return (PROJECT_ROOT / path_value).resolve()


class AppConfig(BaseSettings):
    """Application settings for telemetry analysis, prompts, and runtime limits."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_BASE_URL")
    model_name: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    model_temperature: float = Field(default=0.0, validation_alias="OPENAI_TEMPERATURE")

    anomaly_threshold: float = Field(default=0.6, validation_alias="ANOMALY_THRESHOLD")
    sgr_max_iterations: int = Field(default=8, validation_alias="SGR_MAX_ITERATIONS")
    window_history_limit: int = Field(default=5, validation_alias="WINDOW_HISTORY_LIMIT")

    telemetry_csv_path: Path = Field(default=DEFAULT_TELEMETRY_CSV_PATH, validation_alias="TELEMETRY_CSV_PATH")
    tle_path: Path = Field(default=DEFAULT_TLE_PATH, validation_alias="TLE_PATH")

    resample_freq: str = Field(default="30s", validation_alias="RESAMPLE_FREQ")
    window_minutes: int = Field(default=10, validation_alias="WINDOW_MINUTES")
    step_minutes: int = Field(default=10, validation_alias="STEP_MINUTES")

    ground_station_lat: float = Field(default=55.7558, validation_alias="GROUND_STATION_LAT")
    ground_station_lon: float = Field(default=37.6173, validation_alias="GROUND_STATION_LON")
    ground_station_visibility_km: float = Field(default=2500.0, validation_alias="GROUND_STATION_VISIBILITY_KM")

    logs_dir: Path = Field(default=DEFAULT_LOGS_DIR, validation_alias="LOGS_DIR")
    log_file_path: Path = Field(default=DEFAULT_LOG_FILE, validation_alias="LOG_FILE_PATH")

    classification_prompt_path: Path = Field(
        default=DEFAULT_CLASSIFICATION_PROMPT_PATH,
        validation_alias="CLASSIFICATION_PROMPT_PATH",
    )
    deep_system_prompt_path: Path = Field(
        default=DEFAULT_DEEP_SYSTEM_PROMPT_PATH,
        validation_alias="DEEP_SYSTEM_PROMPT_PATH",
    )
    deep_user_prompt_path: Path = Field(
        default=DEFAULT_DEEP_USER_PROMPT_PATH,
        validation_alias="DEEP_USER_PROMPT_PATH",
    )

    @property
    def resolved_telemetry_csv_path(self) -> Path:
        """Return the absolute path to the telemetry CSV file."""

        return _abs_path(self.telemetry_csv_path)

    @property
    def resolved_tle_path(self) -> Path:
        """Return the absolute path to the TLE file."""

        return _abs_path(self.tle_path)

    @property
    def resolved_logs_dir(self) -> Path:
        """Return the absolute path to the logs directory."""

        return _abs_path(self.logs_dir)

    @property
    def resolved_log_file_path(self) -> Path:
        """Return the absolute path to the backend log file."""

        return _abs_path(self.log_file_path)

    @property
    def resolved_classification_prompt_path(self) -> Path:
        """Return the absolute path to the classification prompt."""

        return _abs_path(self.classification_prompt_path)

    @property
    def resolved_deep_system_prompt_path(self) -> Path:
        """Return the absolute path to the deep system prompt."""

        return _abs_path(self.deep_system_prompt_path)

    @property
    def resolved_deep_user_prompt_path(self) -> Path:
        """Return the absolute path to the deep user prompt."""

        return _abs_path(self.deep_user_prompt_path)


def load_prompts(config: AppConfig) -> dict[str, str]:
    """Load all prompt templates from configured files."""

    return {
        "classification_system": config.resolved_classification_prompt_path.read_text(encoding="utf-8").strip(),
        "deep_system": config.resolved_deep_system_prompt_path.read_text(encoding="utf-8").strip(),
        "deep_user": config.resolved_deep_user_prompt_path.read_text(encoding="utf-8").strip(),
    }
