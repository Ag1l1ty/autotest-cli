"""Integration tests for the CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from autotest.cli import app

runner = CliRunner()


class TestCLI:

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "autotest" in result.output.lower() or "scan" in result.output.lower()

    def test_detect_command(self, python_project: Path) -> None:
        result = runner.invoke(app, ["detect", str(python_project)])
        assert result.exit_code == 0
