"""Python toolchain adapter."""

from __future__ import annotations

import shutil
import sys

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


def _get_python_cmd() -> str:
    """Get the correct Python command for the current system."""
    # Prefer the current interpreter
    if sys.executable:
        return sys.executable
    # Fall back to python3 if available, else python
    if shutil.which("python3"):
        return "python3"
    return "python"


PYTHON = _get_python_cmd()


class PythonAdapter(BaseAdapter):

    def __init__(self, existing_tools: list[str] | None = None) -> None:
        self.existing_tools = existing_tools or []

    def get_toolchain(self) -> ToolChainConfig:
        test_runner = "pytest" if "pytest" in self.existing_tools else "pytest"
        return ToolChainConfig(
            language=Language.PYTHON,
            test_runner=test_runner,
            test_command=[PYTHON, "-m", "pytest", "-v", "--tb=short"],
            coverage_tool="coverage.py",
            coverage_command=[PYTHON, "-m", "pytest", "--cov", "--cov-report=json", "--cov-report=term"],
            mock_library="pytest-mock",
            security_tool="bandit",
            security_command=[PYTHON, "-m", "bandit", "-r", ".", "-f", "json", "-q"],
            quality_tools=["ruff", "mypy"],
            quality_commands=[
                [PYTHON, "-m", "ruff", "check", "."],
                [PYTHON, "-m", "mypy", "."],
            ],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        base = [PYTHON, "-m", "pytest"]
        match phase:
            case TestPhase.SMOKE:
                return base + ["--co", "-q"]  # collect-only, verify tests parse
            case TestPhase.UNIT:
                return base + ["-v", "--tb=short", "-x"]
            case TestPhase.INTEGRATION:
                return base + ["-v", "-m", "integration", "--tb=long"]
            case TestPhase.SECURITY:
                return [PYTHON, "-m", "bandit", "-r", ".", "-f", "json"]
            case TestPhase.QUALITY:
                return [PYTHON, "-m", "ruff", "check", "."]
        return base

    def get_coverage_command(self) -> list[str]:
        return [PYTHON, "-m", "pytest", "--cov", "--cov-report=json"]

    def get_lint_commands(self) -> list[list[str]]:
        return [
            [PYTHON, "-m", "ruff", "check", "."],
            [PYTHON, "-m", "mypy", "."],
        ]
