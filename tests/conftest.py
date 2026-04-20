"""Shared pytest fixtures and configuration for QuantLab tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _safe_env_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Set safe defaults for every test so tests never accidentally hit prod config.

    - Forces QUANTLAB_ENV=development
    - Uses tmp_path for data and logs dirs
    - Provides dummy API keys
    - Forces IBKR_MODE=PAPER
    """
    monkeypatch.setenv("QUANTLAB_ENV", "development")
    monkeypatch.setenv("QUANTLAB_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("QUANTLAB_LOG_FORMAT", "console")
    monkeypatch.setenv("QUANTLAB_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("QUANTLAB_LOGS_DIR", str(tmp_path / "logs"))

    monkeypatch.setenv("POLYGON_API_KEY", "test_polygon_key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")

    monkeypatch.setenv("IBKR_HOST", "127.0.0.1")
    monkeypatch.setenv("IBKR_PORT", "7497")
    monkeypatch.setenv("IBKR_CLIENT_ID", "99")
    monkeypatch.setenv("IBKR_ACCOUNT_ID", "DU_TEST_ACCOUNT")
    monkeypatch.setenv("IBKR_MODE", "PAPER")

    yield


@pytest.fixture
def fresh_settings() -> object:  # return type boxed to avoid import cycles
    """Force a fresh Settings instance after environment overrides.

    Use this when a test needs settings to reflect monkeypatched env vars,
    since `quantlab.config.settings` is a module-level singleton loaded at import.
    """
    from quantlab.config import Settings

    return Settings()
