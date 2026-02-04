"""Tests for Pydantic models."""

from __future__ import annotations

import pytest

from autotest.models.project import Language, TestPhase
from autotest.models.diagnosis import (
    DiagnosisReport,
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)
from autotest.models.report import QualitySummary, ReportData


class TestLanguageEnum:

    def test_all_languages_exist(self) -> None:
        assert Language.PYTHON.value == "python"
        assert Language.JAVASCRIPT.value == "javascript"
        assert Language.JAVA.value == "java"
        assert Language.GO.value == "go"
        assert Language.RUST.value == "rust"
        assert Language.CSHARP.value == "csharp"

    def test_language_from_string(self) -> None:
        assert Language("python") == Language.PYTHON


class TestTestPhaseEnum:

    def test_all_phases_exist(self) -> None:
        phases = [p.value for p in TestPhase]
        assert "smoke" in phases
        assert "unit" in phases
        assert "integration" in phases
        assert "security" in phases
        assert "quality" in phases


class TestFinding:

    def test_basic_finding(self) -> None:
        f = Finding(
            severity=Severity.CRITICAL,
            category=FindingCategory.BUG,
            title="Test bug",
            description="A test bug description",
        )
        assert f.severity == Severity.CRITICAL
        assert f.confidence == 1.0
        assert f.source == "static"

    def test_confidence_bounds(self) -> None:
        with pytest.raises(Exception):
            Finding(
                severity=Severity.INFO,
                category=FindingCategory.STYLE,
                title="x",
                description="x",
                confidence=1.5,
            )

    def test_finding_with_fix(self) -> None:
        fix = SuggestedFix(
            description="Use env var",
            code_before="secret = 'abc'",
            code_after="secret = os.environ['SECRET']",
        )
        f = Finding(
            severity=Severity.CRITICAL,
            category=FindingCategory.SECURITY,
            title="Hardcoded secret",
            description="Found hardcoded secret",
            suggested_fix=fix,
        )
        assert f.suggested_fix.code_before == "secret = 'abc'"


class TestDiagnosisReport:

    def test_defaults(self) -> None:
        dr = DiagnosisReport()
        assert dr.findings == []
        assert dr.health_score == 100.0
        assert dr.health_label == "healthy"

    def test_health_score_bounds(self) -> None:
        with pytest.raises(Exception):
            DiagnosisReport(health_score=150.0)


class TestQualitySummary:

    def test_score_bounds(self) -> None:
        qs = QualitySummary(overall_score=85.0)
        assert qs.overall_score == 85.0

    def test_invalid_score(self) -> None:
        with pytest.raises(Exception):
            QualitySummary(overall_score=150.0)
