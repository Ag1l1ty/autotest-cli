"""Pydantic models for inter-module communication."""

from autotest.models.project import (
    FrameworkInfo,
    Language,
    LanguageInfo,
    ProjectInfo,
    TestPhase,
)
from autotest.models.analysis import (
    AnalysisReport,
    CouplingInfo,
    FunctionMetrics,
    ModuleMetrics,
)
from autotest.models.diagnosis import (
    DiagnosisReport,
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)
from autotest.models.report import QualitySummary, ReportData

__all__ = [
    "FrameworkInfo",
    "Language",
    "LanguageInfo",
    "ProjectInfo",
    "TestPhase",
    "AnalysisReport",
    "CouplingInfo",
    "FunctionMetrics",
    "ModuleMetrics",
    "DiagnosisReport",
    "Finding",
    "FindingCategory",
    "Severity",
    "SuggestedFix",
    "QualitySummary",
    "ReportData",
]
