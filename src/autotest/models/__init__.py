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
from autotest.models.adaptation import (
    GeneratedTest,
    TestStrategy,
    ToolChainConfig,
)
from autotest.models.execution import (
    ExecutionReport,
    PhaseResult,
    TestResult,
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
    "GeneratedTest",
    "TestStrategy",
    "ToolChainConfig",
    "ExecutionReport",
    "PhaseResult",
    "TestResult",
    "QualitySummary",
    "ReportData",
]
