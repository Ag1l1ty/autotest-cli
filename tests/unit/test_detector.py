"""Tests for the project detector module."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from autotest.config import AutoTestConfig
from autotest.detector.scanner import ProjectScanner
from autotest.models.project import Language


@pytest.fixture
def scanner(default_config: AutoTestConfig) -> ProjectScanner:
    return ProjectScanner(default_config)


class TestProjectScanner:

    def test_detect_python_project(self, scanner: ProjectScanner, python_project: Path) -> None:
        result = asyncio.run(scanner.scan(python_project))
        languages = [lang.language for lang in result.languages]
        assert Language.PYTHON in languages

    def test_detect_js_project(self, scanner: ProjectScanner, js_project: Path) -> None:
        result = asyncio.run(scanner.scan(js_project))
        languages = [lang.language for lang in result.languages]
        assert Language.JAVASCRIPT in languages

    def test_detect_mixed_project(self, scanner: ProjectScanner, mixed_project: Path) -> None:
        result = asyncio.run(scanner.scan(mixed_project))
        languages = [lang.language for lang in result.languages]
        assert len(languages) >= 2

    def test_empty_directory(self, scanner: ProjectScanner, tmp_path: Path) -> None:
        result = asyncio.run(scanner.scan(tmp_path))
        assert len(result.languages) == 0

    def test_project_name_from_path(self, scanner: ProjectScanner, python_project: Path) -> None:
        result = asyncio.run(scanner.scan(python_project))
        assert result.name == "python_project"
