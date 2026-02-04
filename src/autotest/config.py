"""Configuration management for AutoTest CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from autotest.constants import (
    DEFAULT_AI_MAX_FUNCTIONS,
    DEFAULT_MIN_FINDING_CONFIDENCE,
    DEFAULT_OUTPUT_FORMATS,
    DEFAULT_SEVERITY_FILTER,
    DEFAULT_TOP_FINDINGS,
)


def _get_api_key() -> str:
    """Get API key from various environment variables."""
    return (
        os.environ.get("AUTOTEST_AI_API_KEY", "")
        or os.environ.get("ANTHROPIC_API_KEY", "")
        or ""
    )


class AutoTestConfig(BaseSettings):
    """Configuration loaded from .autotest.yaml, pyproject.toml, env vars, and CLI flags."""

    model_config = {"env_prefix": "AUTOTEST_", "env_file": ".env", "extra": "ignore"}

    # Target project
    target_path: Path = Field(default=Path("."))

    # Output configuration
    output_formats: list[str] = Field(default_factory=lambda: list(DEFAULT_OUTPUT_FORMATS))
    output_dir: Path = Field(default=Path("./reports"))

    # AI configuration
    ai_enabled: bool = True
    ai_api_key: str = Field(default_factory=_get_api_key)
    ai_model: str = "claude-sonnet-4-20250514"
    ai_max_functions: int = DEFAULT_AI_MAX_FUNCTIONS
    ai_max_cost_usd: float = 5.0

    # Diagnosis configuration
    min_finding_confidence: float = DEFAULT_MIN_FINDING_CONFIDENCE
    severity_filter: list[str] = Field(
        default_factory=lambda: list(DEFAULT_SEVERITY_FILTER)
    )
    top_findings: int = DEFAULT_TOP_FINDINGS

    # Analysis thresholds
    complexity_threshold: int = 10
    coupling_threshold: int = 8

    # Logging
    verbose: bool = False
    debug: bool = False


def load_config(
    target_path: Path | None = None,
    config_file: Path | None = None,
    **overrides: Any,
) -> AutoTestConfig:
    """Load configuration from multiple sources with precedence:
    CLI flags > env vars > .autotest.yaml > pyproject.toml > defaults.
    """
    file_config: dict[str, Any] = {}

    # Try .autotest.yaml first
    if config_file and config_file.exists():
        file_config = _load_yaml(config_file)
    elif target_path:
        yaml_path = target_path / ".autotest.yaml"
        if yaml_path.exists():
            file_config = _load_yaml(yaml_path)
        else:
            # Try pyproject.toml [tool.autotest]
            pyproject = target_path / "pyproject.toml"
            if pyproject.exists():
                file_config = _load_pyproject(pyproject)

    # Merge: file config + overrides
    merged = {**file_config, **{k: v for k, v in overrides.items() if v is not None}}
    if target_path is not None:
        merged["target_path"] = target_path

    return AutoTestConfig(**merged)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load configuration from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _load_pyproject(path: Path) -> dict[str, Any]:
    """Load [tool.autotest] section from pyproject.toml."""
    try:
        if hasattr(path, "read_text"):
            import tomllib

            with open(path, "rb") as f:
                data = tomllib.load(f)
            return data.get("tool", {}).get("autotest", {})
    except Exception:
        return {}
    return {}
