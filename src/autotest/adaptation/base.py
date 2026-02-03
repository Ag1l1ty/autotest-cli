"""Base class for language adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import TestPhase


class BaseAdapter(ABC):
    """Abstract base class for language-specific test adapters."""

    @abstractmethod
    def get_toolchain(self) -> ToolChainConfig:
        """Return the test/coverage/mock tool configuration."""

    @abstractmethod
    def get_test_command(self, phase: TestPhase) -> list[str]:
        """Return the shell command to run tests for a given phase."""

    @abstractmethod
    def get_coverage_command(self) -> list[str]:
        """Return the shell command to generate coverage data."""

    @abstractmethod
    def get_lint_commands(self) -> list[list[str]]:
        """Return linting/quality commands."""
