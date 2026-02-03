"""Base class for phase executors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from autotest.models.adaptation import TestStrategy
from autotest.models.execution import PhaseResult
from autotest.models.project import TestPhase


class BasePhaseExecutor(ABC):
    """Abstract base class for test phase executors."""

    @property
    @abstractmethod
    def phase_name(self) -> TestPhase:
        """The phase this executor handles."""

    @abstractmethod
    async def execute(
        self,
        strategy: TestStrategy,
        project_root: "Path",
    ) -> PhaseResult:
        """Execute this test phase and return results."""
