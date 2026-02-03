"""Report engine - orchestrates report generation and quality scoring."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import ExecutionReport
from autotest.models.project import ProjectInfo, TestPhase
from autotest.models.report import QualitySummary, ReportData, FailedTestDetail
from autotest.reporter.terminal import TerminalReporter
from autotest.reporter.json_reporter import JSONReporter
from autotest.reporter.html_reporter import HTMLReporter
from autotest.utils.error_analyzer import (
    TestErrorAnalyzer,
    analyze_test_results,
    generate_actionable_recommendations,
)


class ReportEngine:
    """Orchestrates report generation across multiple formats."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def report(
        self,
        project: ProjectInfo,
        analysis: AnalysisReport,
        strategy: TestStrategy,
        execution: ExecutionReport,
    ) -> tuple[ReportData, dict[str, Path]]:
        """Generate reports in all configured formats.

        Returns:
            Tuple of (ReportData, dict of format -> file path)
        """
        quality = self._calculate_quality(analysis, execution)

        report_data = ReportData(
            project=project,
            analysis=analysis,
            strategy=strategy,
            execution=execution,
            quality=quality,
        )

        reporters = {
            "terminal": lambda: TerminalReporter(self.config),
            "json": lambda: JSONReporter(self.config),
            "html": lambda: HTMLReporter(self.config),
        }

        generated_files: dict[str, Path] = {}

        for fmt in self.config.output_formats:
            factory = reporters.get(fmt)
            if factory:
                reporter = factory()
                result = await reporter.generate(report_data)
                if isinstance(result, Path):
                    generated_files[fmt] = result

        return report_data, generated_files

    def _calculate_quality(
        self,
        analysis: AnalysisReport,
        execution: ExecutionReport,
    ) -> QualitySummary:
        """Calculate composite quality score (0-100)."""
        scores: list[float] = []
        risk_areas: list[str] = []
        recommendations: list[str] = []
        failed_tests: list[FailedTestDetail] = []

        # 1. Test pass rate (weight: 30%)
        if execution.overall_pass_rate is not None:
            pass_score = execution.overall_pass_rate * 100
            scores.append(pass_score * 0.30)
            if pass_score < 80:
                risk_areas.append(f"Test pass rate is low ({pass_score:.0f}%)")
        else:
            scores.append(0)

        # 2. Coverage (weight: 25%)
        if execution.overall_coverage is not None:
            cov_score = min(execution.overall_coverage, 100.0)
            scores.append(cov_score * 0.25)
            if cov_score < 60:
                risk_areas.append(f"Code coverage is low ({cov_score:.0f}%)")
                recommendations.append("Aumentar cobertura de tests en rutas críticas")
        else:
            scores.append(12.5)  # Neutral if unavailable

        # 3. Complexity (weight: 15%)
        if analysis.avg_complexity > 0:
            complexity_score = max(0, 100 - (analysis.avg_complexity - 5) * 10)
            scores.append(min(complexity_score, 100) * 0.15)
            if analysis.avg_complexity > 10:
                risk_areas.append(
                    f"Complejidad promedio alta ({analysis.avg_complexity:.1f})"
                )
                recommendations.append(
                    "Refactorizar funciones con complejidad ciclomática > 10"
                )
        else:
            scores.append(15.0)

        # 4. Untested functions (weight: 15%)
        if analysis.total_functions > 0:
            tested_ratio = 1 - (
                len(analysis.untested_functions) / analysis.total_functions
            )
            scores.append(tested_ratio * 100 * 0.15)
            if tested_ratio < 0.5:
                risk_areas.append(
                    f"{len(analysis.untested_functions)} funciones sin tests"
                )
                recommendations.append(
                    "Agregar tests para funciones no cubiertas, priorizar por complejidad"
                )
        else:
            scores.append(15.0)

        # 5. Security phase (weight: 15%)
        security_phase = next(
            (p for p in execution.phases if p.phase == TestPhase.SECURITY), None,
        )
        if security_phase:
            sec_score = security_phase.success_rate * 100
            scores.append(sec_score * 0.15)
            if sec_score < 100:
                risk_areas.append("Problemas de seguridad detectados")
                recommendations.append(
                    "Resolver hallazgos de seguridad antes de producción"
                )
        else:
            scores.append(7.5)

        overall = sum(scores)

        # Determine health label
        if overall >= 80:
            health = "healthy"
        elif overall >= 60:
            health = "moderate"
        elif overall >= 40:
            health = "at-risk"
        else:
            health = "critical"

        # Analyze failed tests and generate specific recommendations
        all_test_results = []
        for phase in execution.phases:
            all_test_results.extend(phase.test_results)

        error_analyses = analyze_test_results(all_test_results)

        # Create failed test details
        for item in error_analyses:
            analysis_data = item["analysis"]
            failed_tests.append(FailedTestDetail(
                test_name=item["test_name"],
                category=analysis_data.category,
                summary=analysis_data.summary,
                file_path=analysis_data.file_path,
                line_number=analysis_data.line_number,
                recommendation=analysis_data.recommendation,
                code_snippet=analysis_data.code_snippet,
            ))

        # Generate actionable recommendations from error analysis
        if error_analyses:
            actionable_recs = generate_actionable_recommendations(error_analyses)
            recommendations.extend(actionable_recs)

        return QualitySummary(
            overall_score=round(overall, 1),
            test_health=health,
            risk_areas=risk_areas,
            recommendations=recommendations,
            failed_tests=failed_tests,
        )
