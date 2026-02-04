"""Shared pytest fixtures for AutoTest tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.config import AutoTestConfig


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def python_project() -> Path:
    return FIXTURES_DIR / "python_project"


@pytest.fixture
def js_project() -> Path:
    return FIXTURES_DIR / "js_project"


@pytest.fixture
def mixed_project() -> Path:
    return FIXTURES_DIR / "mixed_project"


@pytest.fixture
def default_config(tmp_path: Path) -> AutoTestConfig:
    return AutoTestConfig(
        target_path=tmp_path,
        output_dir=tmp_path / "reports",
        ai_enabled=False,
        ai_api_key="",
    )


@pytest.fixture
def ai_config(tmp_path: Path) -> AutoTestConfig:
    return AutoTestConfig(
        target_path=tmp_path,
        output_dir=tmp_path / "reports",
        ai_enabled=True,
        ai_api_key="test-key-not-real",
        ai_model="claude-sonnet-4-20250514",
        ai_max_functions=5,
    )
