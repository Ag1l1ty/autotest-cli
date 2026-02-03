"""End-to-end integration tests for the full pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from autotest.config import AutoTestConfig
from autotest.detector.scanner import ProjectScanner


class TestFullPipeline:

    def test_scan_python_project(self, python_project: Path, default_config: AutoTestConfig) -> None:
        scanner = ProjectScanner(default_config)
        project = asyncio.run(scanner.scan(python_project))
        assert project.name == "python_project"
        assert len(project.languages) > 0

    def test_scan_empty_project(self, tmp_path: Path, default_config: AutoTestConfig) -> None:
        scanner = ProjectScanner(default_config)
        project = asyncio.run(scanner.scan(tmp_path))
        assert len(project.languages) == 0
