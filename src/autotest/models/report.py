"""Models for report generation."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from autotest.models.project import ProjectInfo
from autotest.models.analysis import AnalysisReport
from autotest.models.diagnosis import DiagnosisReport


def _generate_report_id() -> str:
    """Generate a unique report ID: AT-YYYYMMDD-XXXXXX."""
    date_part = datetime.now().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"AT-{date_part}-{unique_part}"


class QualitySummary(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    risk_areas: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ReportData(BaseModel):
    report_id: str = Field(default_factory=_generate_report_id)
    generated_at: datetime = Field(default_factory=datetime.now)
    autotest_version: str = "0.2.0"
    project: ProjectInfo
    analysis: AnalysisReport
    quality: QualitySummary = Field(default_factory=QualitySummary)
    diagnosis: DiagnosisReport | None = None
