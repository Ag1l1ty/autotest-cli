"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from autotest.models.project import Language, TestPhase, ProjectInfo, LanguageInfo
from autotest.models.analysis import FunctionMetrics, AnalysisReport
from autotest.models.adaptation import ToolChainConfig, GeneratedTest, TestStrategy
from autotest.models.execution import TestResult, PhaseResult, ExecutionReport
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


class TestToolChainConfig:

    def test_defaults(self) -> None:
        tc = ToolChainConfig(language=Language.PYTHON, test_runner="pytest")
        assert tc.test_command == []
        assert tc.coverage_tool == ""
        assert tc.quality_tools == []

    def test_full_config(self) -> None:
        tc = ToolChainConfig(
            language=Language.PYTHON,
            test_runner="pytest",
            test_command=["python", "-m", "pytest"],
            coverage_tool="coverage",
            coverage_command=["coverage", "run"],
            mock_library="pytest-mock",
            security_tool="bandit",
            security_command=["bandit", "-r", "."],
            quality_tools=["ruff", "mypy"],
            quality_commands=[["ruff", "check", "."], ["mypy", "."]],
        )
        assert len(tc.quality_commands) == 2


class TestGeneratedTest:

    def test_default_invalid(self) -> None:
        gt = GeneratedTest(
            target_function="my_func",
            file_path=Path("test_my_func.py"),
            source_code="def test_it(): pass",
            language=Language.PYTHON,
            framework="pytest",
        )
        assert gt.is_valid is False
        assert gt.confidence == 0.0

    def test_confidence_bounds(self) -> None:
        with pytest.raises(Exception):
            GeneratedTest(
                target_function="f",
                file_path=Path("t.py"),
                source_code="",
                language=Language.PYTHON,
                framework="pytest",
                confidence=1.5,
            )


class TestTestResult:

    def test_basic_result(self) -> None:
        r = TestResult(name="test_add", passed=True, duration_ms=12.5)
        assert r.passed is True
        assert r.error_message is None


class TestPhaseResult:

    def test_success_rate(self) -> None:
        now = datetime.now()
        pr = PhaseResult(
            phase=TestPhase.UNIT,
            started_at=now,
            finished_at=now,
            total_tests=10,
            passed=8,
            failed=2,
            success_rate=0.8,
        )
        assert pr.success_rate == 0.8


class TestQualitySummary:

    def test_score_bounds(self) -> None:
        qs = QualitySummary(overall_score=85.0, test_health="healthy")
        assert qs.overall_score == 85.0

    def test_invalid_score(self) -> None:
        with pytest.raises(Exception):
            QualitySummary(overall_score=150.0)
