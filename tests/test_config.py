"""Tests for quantlab.config."""

from __future__ import annotations

import pytest

from quantlab.config import Environment, IBKRMode, LogFormat, LogLevel, Settings


class TestSettings:
    """Verify the Settings object loads from environment correctly."""

    def test_defaults_for_development(self, fresh_settings: Settings) -> None:
        assert fresh_settings.env == Environment.DEVELOPMENT
        assert fresh_settings.log_level == LogLevel.DEBUG
        assert fresh_settings.log_format == LogFormat.CONSOLE

    def test_ibkr_defaults_to_paper_mode(self, fresh_settings: Settings) -> None:
        assert fresh_settings.ibkr.mode == IBKRMode.PAPER
        assert fresh_settings.ibkr.is_paper is True
        assert fresh_settings.ibkr.port == 7497

    def test_anthropic_model_pins_loaded(self, fresh_settings: Settings) -> None:
        # Model strings must be loaded from environment; we care that SOME value is present
        assert fresh_settings.anthropic.opus_model
        assert fresh_settings.anthropic.sonnet_model
        assert fresh_settings.anthropic.haiku_model

    def test_api_keys_are_secret_str(self, fresh_settings: Settings) -> None:
        # Secret values are wrapped to prevent accidental logging
        assert fresh_settings.polygon_api_key.get_secret_value() == "test_polygon_key"
        assert fresh_settings.anthropic.api_key.get_secret_value() == "test_anthropic_key"

    def test_is_production_flag(self, fresh_settings: Settings) -> None:
        assert fresh_settings.is_production is False
        assert fresh_settings.is_development is True

    def test_paths_resolved_to_absolute(self, fresh_settings: Settings) -> None:
        assert fresh_settings.data_dir.is_absolute()
        assert fresh_settings.logs_dir.is_absolute()


class TestIBKRSafety:
    """The live-mode safety rail is load-bearing — test it carefully."""

    def test_live_mode_triggers_warning_on_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setenv("IBKR_MODE", "LIVE")
        # Force fresh construction to trigger the validator
        Settings()
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "Real money" in captured.err
