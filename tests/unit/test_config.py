"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.config import AutoTestConfig, load_config


class TestAutoTestConfig:

    def test_defaults(self) -> None:
        config = AutoTestConfig()
        assert config.ai_enabled is True
        assert config.verbose is False
        assert config.complexity_threshold == 10
        assert config.coupling_threshold == 8

    def test_env_prefix(self) -> None:
        config = AutoTestConfig()
        assert config.model_config["env_prefix"] == "AUTOTEST_"

    def test_diagnosis_defaults(self) -> None:
        config = AutoTestConfig()
        assert config.ai_max_functions == 10
        assert config.min_finding_confidence == 0.6
        assert "critical" in config.severity_filter
        assert "warning" in config.severity_filter
        assert config.top_findings == 5


class TestLoadConfig:

    def test_load_with_target_path(self, tmp_path: Path) -> None:
        config = load_config(target_path=tmp_path)
        assert config.target_path == tmp_path

    def test_overrides(self, tmp_path: Path) -> None:
        config = load_config(
            target_path=tmp_path,
            ai_enabled=False,
            top_findings=10,
        )
        assert config.ai_enabled is False
        assert config.top_findings == 10

    def test_yaml_config(self, tmp_path: Path) -> None:
        yaml_content = "ai_enabled: false\nseverity_filter:\n  - critical\n"
        yaml_file = tmp_path / ".autotest.yaml"
        yaml_file.write_text(yaml_content)
        config = load_config(target_path=tmp_path)
        assert config.ai_enabled is False
