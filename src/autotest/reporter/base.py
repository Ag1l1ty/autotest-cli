"""Base class for report generators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from autotest.models.report import ReportData


class BaseReporter(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    async def generate(self, report_data: ReportData) -> Path | str:
        """Generate a report and return file path or content string."""
