"""Base class for language detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from autotest.models.project import FrameworkInfo, LanguageInfo


class BaseLanguageDetector(ABC):
    """Abstract base class for language detectors."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Return the language name identifier."""

    @abstractmethod
    def detect(self, root: Path) -> LanguageInfo | None:
        """Detect if this language is present in the project.
        
        Returns LanguageInfo if found, None otherwise.
        """

    @abstractmethod
    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        """Detect frameworks and libraries for this language."""

    @abstractmethod
    def detect_test_tools(self, root: Path) -> list[str]:
        """Detect existing testing tools for this language."""
