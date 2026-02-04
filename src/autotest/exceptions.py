"""Custom exception hierarchy for AutoTest CLI."""

from __future__ import annotations


class AutoTestError(Exception):
    """Base exception for all AutoTest errors."""


class DetectionError(AutoTestError):
    """Error during project detection."""


class AnalysisError(AutoTestError):
    """Error during code analysis."""


class ReportError(AutoTestError):
    """Error during report generation."""


class ConfigError(AutoTestError):
    """Error in configuration loading or validation."""


class DiagnosisError(AutoTestError):
    """Error during code diagnosis."""


class AIReviewError(DiagnosisError):
    """Error during AI-powered code review."""
