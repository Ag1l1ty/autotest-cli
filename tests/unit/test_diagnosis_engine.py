"""Tests for diagnosis engine."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from autotest.config import AutoTestConfig
from autotest.diagnosis.engine import DiagnosisEngine
from autotest.models.analysis import AnalysisReport, FunctionMetrics, ModuleMetrics
from autotest.models.diagnosis import Finding, FindingCategory, Severity, SuggestedFix
from autotest.models.project import Language, LanguageInfo, ProjectInfo


def _make_project(root: Path) -> ProjectInfo:
    return ProjectInfo(
        name="test-project",
        root_path=root,
        languages=[LanguageInfo(language=Language.PYTHON, total_loc=100, percentage=100.0)],
    )


def _make_analysis() -> AnalysisReport:
    return AnalysisReport(
        total_functions=5,
        tested_function_count=3,
        estimated_coverage=60.0,
    )


def _make_finding(
    severity: Severity = Severity.WARNING,
    category: FindingCategory = FindingCategory.BUG,
    file_path: str = "module.py",
    line_start: int = 10,
    confidence: float = 0.8,
    source: str = "static",
) -> Finding:
    return Finding(
        severity=severity,
        category=category,
        title=f"Test finding at {file_path}:{line_start}",
        description="Test description",
        file_path=file_path,
        line_start=line_start,
        confidence=confidence,
        source=source,
    )


class TestHealthScore:

    def test_perfect_score_no_findings(self, tmp_path: Path) -> None:
        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        score = engine._calculate_health_score(0, 0, 0, _make_analysis())
        assert score > 90  # coverage gap penalty reduces from 100

    def test_criticals_reduce_score(self, tmp_path: Path) -> None:
        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        score = engine._calculate_health_score(3, 0, 0, _make_analysis())
        assert score < 80

    def test_score_never_below_zero(self, tmp_path: Path) -> None:
        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        score = engine._calculate_health_score(100, 100, 100, _make_analysis())
        assert score >= 0.0

    def test_score_capped_at_100(self, tmp_path: Path) -> None:
        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        analysis = AnalysisReport(estimated_coverage=100.0)
        score = engine._calculate_health_score(0, 0, 0, analysis)
        assert score == 100.0


class TestHealthLabel:

    def test_healthy(self, tmp_path: Path) -> None:
        engine = DiagnosisEngine(AutoTestConfig(target_path=tmp_path))
        assert engine._health_label(85.0) == "healthy"

    def test_moderate(self, tmp_path: Path) -> None:
        engine = DiagnosisEngine(AutoTestConfig(target_path=tmp_path))
        assert engine._health_label(65.0) == "moderate"

    def test_at_risk(self, tmp_path: Path) -> None:
        engine = DiagnosisEngine(AutoTestConfig(target_path=tmp_path))
        assert engine._health_label(45.0) == "at-risk"

    def test_critical(self, tmp_path: Path) -> None:
        engine = DiagnosisEngine(AutoTestConfig(target_path=tmp_path))
        assert engine._health_label(30.0) == "critical"


class TestDeduplication:

    def test_same_file_line_category_deduplicates(self) -> None:
        f1 = _make_finding(source="static", confidence=0.7)
        f2 = _make_finding(source="ai", confidence=0.9)
        result = DiagnosisEngine._deduplicate([f1, f2])
        assert len(result) == 1
        assert result[0].source == "ai"  # Higher confidence / AI preferred

    def test_different_files_not_deduplicated(self) -> None:
        f1 = _make_finding(file_path="a.py")
        f2 = _make_finding(file_path="b.py")
        result = DiagnosisEngine._deduplicate([f1, f2])
        assert len(result) == 2

    def test_different_categories_not_deduplicated(self) -> None:
        f1 = _make_finding(category=FindingCategory.BUG)
        f2 = _make_finding(category=FindingCategory.SECURITY)
        result = DiagnosisEngine._deduplicate([f1, f2])
        assert len(result) == 2

    def test_nearby_lines_deduplicated(self) -> None:
        f1 = _make_finding(line_start=10, confidence=0.5)
        f2 = _make_finding(line_start=12, confidence=0.9)
        result = DiagnosisEngine._deduplicate([f1, f2])
        assert len(result) == 1

    def test_distant_lines_not_deduplicated(self) -> None:
        f1 = _make_finding(line_start=10)
        f2 = _make_finding(line_start=100)
        result = DiagnosisEngine._deduplicate([f1, f2])
        assert len(result) == 2

    def test_empty_list(self) -> None:
        result = DiagnosisEngine._deduplicate([])
        assert result == []


class TestRelativizePaths:

    def test_absolute_paths_made_relative(self) -> None:
        root = Path("/home/user/project")
        findings = [_make_finding(file_path="/home/user/project/src/main.py")]
        DiagnosisEngine._relativize_paths(findings, root)
        assert findings[0].file_path == "src/main.py"

    def test_already_relative_paths_unchanged(self) -> None:
        root = Path("/home/user/project")
        findings = [_make_finding(file_path="src/main.py")]
        DiagnosisEngine._relativize_paths(findings, root)
        assert findings[0].file_path == "src/main.py"


class TestDiagnoseIntegration:

    @pytest.mark.asyncio
    async def test_diagnose_without_ai(self, tmp_path: Path) -> None:
        """Full diagnosis pipeline without AI."""
        # Create a minimal Python file
        (tmp_path / "main.py").write_text('password = "super_secret_password_12345"\n')

        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        project = _make_project(tmp_path)
        analysis = _make_analysis()

        diagnosis = await engine.diagnose(project, analysis)

        assert diagnosis.health_score >= 0
        assert diagnosis.health_score <= 100
        assert diagnosis.health_label in ("healthy", "moderate", "at-risk", "critical")
        assert len(diagnosis.summary) > 0
        # Security scanner should find the hardcoded password
        security_findings = [
            f for f in diagnosis.findings if f.category == FindingCategory.SECURITY
        ]
        assert len(security_findings) >= 1

    @pytest.mark.asyncio
    async def test_findings_have_sequential_ids(self, tmp_path: Path) -> None:
        config = AutoTestConfig(target_path=tmp_path, ai_enabled=False)
        engine = DiagnosisEngine(config)
        project = _make_project(tmp_path)
        analysis = _make_analysis()

        diagnosis = await engine.diagnose(project, analysis)

        for i, f in enumerate(diagnosis.findings, start=1):
            assert f.id == f"CD-{i:03d}"
