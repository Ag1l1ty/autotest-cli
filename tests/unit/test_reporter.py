"""Tests for the reporter module."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from autotest.models.analysis import AnalysisReport
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import ExecutionReport, PhaseResult, TestResult
from autotest.models.project import ProjectInfo, TestPhase, Language, LanguageInfo
from autotest.models.report import QualitySummary, ReportData
from autotest.reporter.engine import ReportEngine
from autotest.config import AutoTestConfig


@pytest.fixture
def sample_report_data() -> ReportData:
    now = datetime.now()
    project = ProjectInfo(
        name="test-project",
        root_path=Path("/tmp/test"),
        languages=[
            LanguageInfo(language=Language.PYTHON, percentage=100.0, total_loc=500),
        ],
    )
    analysis = AnalysisReport(
        total_functions=10,
        total_loc=500,
        avg_complexity=5.0,
    )
    execution = ExecutionReport(
        phases=[
            PhaseResult(
                phase=TestPhase.UNIT,
                started_at=now,
                finished_at=now + timedelta(seconds=5),
                duration=timedelta(seconds=5),
                total_tests=8,
                passed=7,
                failed=1,
                success_rate=0.875,
                test_results=[
                    TestResult(name="test_add", passed=True, duration_ms=10),
                    TestResult(name="test_div", passed=False, duration_ms=5, error_message="ZeroDivisionError"),
                ],
            ),
        ],
        total_duration=timedelta(seconds=5),
        overall_pass_rate=0.875,
    )
    strategy = TestStrategy(phases_to_run=[TestPhase.UNIT])
    quality = QualitySummary(overall_score=72.0, test_health="moderate")

    return ReportData(
        project=project,
        analysis=analysis,
        strategy=strategy,
        execution=execution,
        quality=quality,
    )


class TestQualityScoring:

    def test_calculate_quality(self) -> None:
        engine = ReportEngine(AutoTestConfig(
            output_formats=["terminal"],
            ai_enabled=False,
        ))
        analysis = AnalysisReport(
            total_functions=10,
            total_loc=500,
            avg_complexity=5.0,
        )
        execution = ExecutionReport(
            overall_pass_rate=0.9,
            overall_coverage=75.0,
        )
        quality = engine._calculate_quality(analysis, execution)
        assert quality.overall_score > 0
        assert quality.test_health in ("healthy", "moderate", "at-risk", "critical")
