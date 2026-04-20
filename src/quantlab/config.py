"""Central configuration for QuantLab.

All settings load from environment variables (via .env file in development).
Settings are validated at import time; any misconfiguration fails fast.

Usage:
    from quantlab.config import settings

    settings.polygon_api_key
    settings.ibkr.host
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment. Controls logging, safety checks, defaults."""

    DEVELOPMENT = "development"
    PAPER = "paper"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Standard logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    """Output format for structured logs."""

    JSON = "json"
    CONSOLE = "console"


class IBKRMode(StrEnum):
    """IBKR trading mode. Must be explicitly LIVE to enable real orders."""

    PAPER = "PAPER"
    LIVE = "LIVE"


class IBKRSettings(BaseSettings):
    """Interactive Brokers connection settings.

    Paper vs live is determined by both port and the explicit IBKR_MODE flag.
    Real trading requires IBKR_MODE=LIVE as an explicit opt-in.
    """

    model_config = SettingsConfigDict(env_prefix="IBKR_", extra="ignore")

    host: str = Field(default="127.0.0.1", description="TWS/Gateway host")
    port: int = Field(default=7497, description="TWS paper=7497, live=7496")
    client_id: int = Field(default=1, description="Unique client ID per connection")
    account_id: str = Field(default="", description="Account ID (DU prefix for paper)")
    mode: IBKRMode = Field(default=IBKRMode.PAPER, description="PAPER or LIVE")

    @field_validator("mode")
    @classmethod
    def _validate_mode_safety(cls, v: IBKRMode) -> IBKRMode:
        """Log loudly when live mode is selected — this is a safety rail."""
        if v == IBKRMode.LIVE:
            # Deliberately not using the logger here to avoid circular import;
            # this message prints during settings load before logging is configured.
            import sys

            print(  # noqa: T201
                "\n" + "=" * 72 + "\n"
                "WARNING: IBKR_MODE=LIVE is set. Real money trading is enabled.\n"
                "If this is unintentional, set IBKR_MODE=PAPER in your .env now.\n"
                + "=" * 72
                + "\n",
                file=sys.stderr,
            )
        return v

    @property
    def is_paper(self) -> bool:
        """True when in paper trading mode."""
        return self.mode == IBKRMode.PAPER


class AnthropicSettings(BaseSettings):
    """Anthropic API settings with pinned model versions."""

    model_config = SettingsConfigDict(env_prefix="ANTHROPIC_", extra="ignore")

    api_key: SecretStr = Field(default=SecretStr(""), description="Anthropic API key")
    opus_model: str = Field(default="claude-opus-4-6", description="Pinned Opus model version")
    sonnet_model: str = Field(
        default="claude-sonnet-4-6", description="Pinned Sonnet model version"
    )
    haiku_model: str = Field(
        default="claude-haiku-4-5-20251001", description="Pinned Haiku model version"
    )


class Settings(BaseSettings):
    """Top-level application settings.

    Nested settings (IBKR, Anthropic) are loaded from their own prefixed env vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="QUANTLAB_",
        extra="ignore",
    )

    # Environment
    env: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: LogFormat = Field(default=LogFormat.CONSOLE)

    # Paths (relative to project root unless absolute)
    data_dir: Path = Field(default=Path("./data"), description="Local data lake root")
    logs_dir: Path = Field(default=Path("./logs"), description="Log output directory")

    # External services
    polygon_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Polygon.io API key",
        validation_alias="POLYGON_API_KEY",
    )
    fred_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="FRED API key (optional)",
        validation_alias="FRED_API_KEY",
    )

    # Nested settings
    ibkr: IBKRSettings = Field(default_factory=IBKRSettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)

    @field_validator("data_dir", "logs_dir")
    @classmethod
    def _resolve_path(cls, v: Path) -> Path:
        """Resolve relative paths to absolute at load time."""
        return v.expanduser().resolve()

    @property
    def is_production(self) -> bool:
        """True when running in production environment."""
        return self.env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """True when running in development environment."""
        return self.env == Environment.DEVELOPMENT


# Singleton instance — import this, don't construct your own
settings = Settings()
