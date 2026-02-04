"""Models for code diagnosis findings and reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class FindingCategory(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    ERROR_HANDLING = "error_handling"
    DEAD_CODE = "dead_code"
    COMPLEXITY = "complexity"
    COUPLING = "coupling"
    MISSING_TESTS = "missing_tests"
    STYLE = "style"


class SuggestedFix(BaseModel):
    description: str
    code_before: str = ""
    code_after: str = ""
    explanation: str = ""


class Finding(BaseModel):
    id: str = ""
    severity: Severity
    category: FindingCategory
    title: str
    description: str
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    function_name: str = ""
    qualified_name: str = ""
    language: str = ""
    suggested_fix: SuggestedFix | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "static"  # "static" | "ai" | "security"


class DiagnosisReport(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    health_label: str = "healthy"
    summary: str = ""
    ai_tokens_used: int = 0
    functions_analyzed: int = 0
