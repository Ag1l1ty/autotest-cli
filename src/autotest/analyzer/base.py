"""Base class for code analyzers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from autotest.models.analysis import ModuleMetrics


class BaseAnalyzer(ABC):
    """Abstract base class for code analyzers."""

    @abstractmethod
    async def analyze(self, file_path: Path, language: str) -> ModuleMetrics:
        """Analyze a single file and return its metrics."""
