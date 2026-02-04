"""Tests for static findings generation."""

from __future__ import annotations

from pathlib import Path

from autotest.diagnosis.static_findings import generate_static_findings
from autotest.models.analysis import (
    AnalysisReport,
    CouplingInfo,
    FunctionMetrics,
    ModuleMetrics,
)
from autotest.models.diagnosis import FindingCategory, Severity
from autotest.models.project import Language


def _make_func(
    name: str,
    cc: int = 5,
    is_public: bool = True,
    is_tested: bool = True,
    file_path: str = "module.py",
    line_start: int = 1,
) -> FunctionMetrics:
    return FunctionMetrics(
        name=name,
        qualified_name=f"Module.{name}",
        file_path=Path(file_path),
        line_start=line_start,
        line_end=line_start + 10,
        language=Language.PYTHON,
        cyclomatic_complexity=cc,
        is_public=is_public,
        is_tested=is_tested,
    )


def _make_analysis(**kwargs) -> AnalysisReport:
    defaults = {
        "modules": [],
        "high_complexity_functions": [],
        "dead_code_functions": [],
        "untested_functions": [],
        "coupling_issues": [],
        "total_functions": 10,
        "tested_function_count": 8,
        "estimated_coverage": 80.0,
    }
    defaults.update(kwargs)
    return AnalysisReport(**defaults)


class TestComplexityFindings:

    def test_high_complexity_generates_warning(self) -> None:
        analysis = _make_analysis(
            high_complexity_functions=[_make_func("complex_func", cc=15)]
        )
        findings = generate_static_findings(analysis)
        complexity = [f for f in findings if f.category == FindingCategory.COMPLEXITY]
        assert len(complexity) == 1
        assert complexity[0].severity == Severity.WARNING
        assert "CC=15" in complexity[0].title

    def test_very_high_complexity_generates_critical(self) -> None:
        analysis = _make_analysis(
            high_complexity_functions=[_make_func("mega_func", cc=50)]
        )
        findings = generate_static_findings(analysis)
        complexity = [f for f in findings if f.category == FindingCategory.COMPLEXITY]
        assert len(complexity) == 1
        assert complexity[0].severity == Severity.CRITICAL

    def test_complexity_finding_has_fix(self) -> None:
        analysis = _make_analysis(
            high_complexity_functions=[_make_func("big_func", cc=12)]
        )
        findings = generate_static_findings(analysis)
        assert findings[0].suggested_fix is not None
        assert "Descomponer" in findings[0].suggested_fix.description


class TestDeadCodeFindings:

    def test_dead_code_generates_info(self) -> None:
        analysis = _make_analysis(
            dead_code_functions=[_make_func("unused", cc=3)]
        )
        findings = generate_static_findings(analysis)
        dead = [f for f in findings if f.category == FindingCategory.DEAD_CODE]
        assert len(dead) == 1
        assert dead[0].severity == Severity.INFO

    def test_high_complexity_dead_code_generates_warning(self) -> None:
        analysis = _make_analysis(
            dead_code_functions=[_make_func("unused_complex", cc=25)]
        )
        findings = generate_static_findings(analysis)
        dead = [f for f in findings if f.category == FindingCategory.DEAD_CODE]
        assert len(dead) == 1
        assert dead[0].severity == Severity.WARNING


class TestCouplingFindings:

    def test_coupling_issue_generates_warning(self) -> None:
        analysis = _make_analysis(
            coupling_issues=[
                CouplingInfo(
                    module_path=Path("core.py"),
                    afferent_coupling=5,
                    efferent_coupling=10,
                    instability=0.67,
                )
            ]
        )
        findings = generate_static_findings(analysis)
        coupling = [f for f in findings if f.category == FindingCategory.COUPLING]
        assert len(coupling) == 1
        assert coupling[0].severity == Severity.WARNING
        assert coupling[0].line_start == 1


class TestMissingTestsFindings:

    def test_high_complexity_untested_generates_warning(self) -> None:
        analysis = _make_analysis(
            untested_functions=[_make_func("risky", cc=25, is_tested=False)]
        )
        findings = generate_static_findings(analysis)
        missing = [f for f in findings if f.category == FindingCategory.MISSING_TESTS]
        assert len(missing) == 1
        assert missing[0].severity == Severity.WARNING

    def test_moderate_complexity_untested_public_generates_info(self) -> None:
        analysis = _make_analysis(
            untested_functions=[_make_func("helper", cc=7, is_tested=False, is_public=True)]
        )
        findings = generate_static_findings(analysis)
        missing = [f for f in findings if f.category == FindingCategory.MISSING_TESTS]
        assert len(missing) == 1
        assert missing[0].severity == Severity.INFO

    def test_no_arbitrary_limit_on_untested(self) -> None:
        funcs = [
            _make_func(f"func_{i}", cc=7, is_tested=False, is_public=True)
            for i in range(20)
        ]
        analysis = _make_analysis(untested_functions=funcs)
        findings = generate_static_findings(analysis)
        missing = [f for f in findings if f.category == FindingCategory.MISSING_TESTS]
        assert len(missing) == 20  # No artificial limit


class TestGenerateStaticFindings:

    def test_empty_analysis_no_findings(self) -> None:
        analysis = _make_analysis()
        findings = generate_static_findings(analysis)
        assert len(findings) == 0

    def test_combined_findings(self) -> None:
        analysis = _make_analysis(
            high_complexity_functions=[_make_func("complex", cc=12)],
            dead_code_functions=[_make_func("dead", cc=2)],
            coupling_issues=[
                CouplingInfo(module_path=Path("x.py"), afferent_coupling=5, efferent_coupling=5)
            ],
        )
        findings = generate_static_findings(analysis)
        categories = {f.category for f in findings}
        assert FindingCategory.COMPLEXITY in categories
        assert FindingCategory.DEAD_CODE in categories
        assert FindingCategory.COUPLING in categories
