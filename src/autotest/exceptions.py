"""Custom exception hierarchy for AutoTest CLI."""

from __future__ import annotations


class AutoTestError(Exception):
    """Base exception for all AutoTest errors."""


class DetectionError(AutoTestError):
    """Error during project detection."""


class AnalysisError(AutoTestError):
    """Error during code analysis."""


class AdaptationError(AutoTestError):
    """Error during test adaptation/generation."""


class AIGenerationError(AdaptationError):
    """Error during AI test generation."""


class ExecutionError(AutoTestError):
    """Error during test execution."""


class PhaseError(ExecutionError):
    """Error during a specific test phase."""

    def __init__(self, phase: str, message: str) -> None:
        self.phase = phase
        super().__init__(f"Phase '{phase}': {message}")


class SandboxError(ExecutionError):
    """Error with test sandbox management."""


class ReportError(AutoTestError):
    """Error during report generation."""


class ConfigError(AutoTestError):
    """Error in configuration loading or validation."""
