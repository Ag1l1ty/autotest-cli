"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.config import AutoTestConfig, load_config


class TestAutoTestConfig:

    def test_defaults(self) -> None:
        config = AutoTestConfig()
        assert config.ai_enabled is True
        assert config.sandbox_enabled is True
        assert config.fail_fast is False
        assert config.timeout_seconds == 300

    def test_env_prefix(self) -> None:
        config = AutoTestConfig()
        assert config.model_config["env_prefix"] == "AUTOTEST_"

    def test_phases_default(self) -> None:
        config = AutoTestConfig()
        assert "smoke" in config.phases
        assert "unit" in config.phases


class TestLoadConfig:

    def test_load_with_target_path(self, tmp_path: Path) -> None:
        config = load_config(target_path=tmp_path)
        assert config.target_path == tmp_path

    def test_overrides(self, tmp_path: Path) -> None:
        config = load_config(
            target_path=tmp_path,
            ai_enabled=False,
            timeout_seconds=60,
        )
        assert config.ai_enabled is False
        assert config.timeout_seconds == 60

    def test_yaml_config(self, tmp_path: Path) -> None:
        yaml_content = "phases:\n  - smoke\n  - unit\nai_enabled: false\n"
        yaml_file = tmp_path / ".autotest.yaml"
        yaml_file.write_text(yaml_content)
        config = load_config(target_path=tmp_path)
        assert config.ai_enabled is False
