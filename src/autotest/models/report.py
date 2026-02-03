"""Models for report generation."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from autotest.models.project import ProjectInfo
from autotest.models.analysis import AnalysisReport
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import ExecutionReport


def _generate_report_id() -> str:
    """Generate a unique report ID: AT-YYYYMMDD-XXXXXX."""
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"AT-{date_part}-{unique_part}"


class FailedTestDetail(BaseModel):
    """Detailed information about a failed test."""

    test_name: str
    category: str  # import, mock, assertion, syntax, etc.
    summary: str  # Short error description
    file_path: str | None = None
    line_number: int | None = None
    recommendation: str  # Actionable fix suggestion
    code_snippet: str | None = None


class QualitySummary(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    test_health: str = "unknown"
    risk_areas: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    failed_tests: list[FailedTestDetail] = Field(default_factory=list)


class ReportData(BaseModel):
    report_id: str = Field(default_factory=_generate_report_id)
    generated_at: datetime = Field(default_factory=datetime.now)
    autotest_version: str = "0.1.0"
    project: ProjectInfo
    analysis: AnalysisReport
    strategy: TestStrategy
    execution: ExecutionReport
    quality: QualitySummary = Field(default_factory=QualitySummary)
