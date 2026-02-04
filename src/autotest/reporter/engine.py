"""Report engine - orchestrates report generation."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport
from autotest.models.diagnosis import DiagnosisReport, Severity
from autotest.models.project import ProjectInfo
from autotest.models.report import ReportData
from autotest.reporter.terminal import TerminalReporter
from autotest.reporter.json_reporter import JSONReporter
from autotest.reporter.html_reporter import HTMLReporter
from autotest.reporter.markdown_reporter import MarkdownReporter


class ReportEngine:
    """Orchestrates report generation across multiple formats."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    def _filter_diagnosis(self, diagnosis: DiagnosisReport) -> DiagnosisReport:
        """Return a DiagnosisReport filtered by config.severity_filter.

        Counts and health_score remain from the original (full) diagnosis
        so the user sees the real state. Only the findings list is filtered
        for display purposes.
        """
        severity_set = set(self.config.severity_filter)
        filtered = [
            f for f in diagnosis.findings
            if f.severity.value in severity_set
        ]
        return DiagnosisReport(
            findings=filtered,
            critical_count=diagnosis.critical_count,
            warning_count=diagnosis.warning_count,
            info_count=diagnosis.info_count,
            health_score=diagnosis.health_score,
            health_label=diagnosis.health_label,
            summary=diagnosis.summary,
            ai_tokens_used=diagnosis.ai_tokens_used,
            functions_analyzed=diagnosis.functions_analyzed,
        )

    async def report_diagnosis(
        self,
        project: ProjectInfo,
        analysis: AnalysisReport,
        diagnosis: DiagnosisReport,
    ) -> tuple[ReportData, dict[str, Path]]:
        """Generate reports for diagnosis results.

        Returns:
            Tuple of (ReportData, dict of format -> file path)
        """
        # Full report data (unfiltered) for JSON and internal use
        report_data = ReportData(
            project=project,
            analysis=analysis,
            diagnosis=diagnosis,
        )

        # Filtered diagnosis for display reporters
        filtered_diagnosis = self._filter_diagnosis(diagnosis)
        filtered_report_data = ReportData(
            report_id=report_data.report_id,
            generated_at=report_data.generated_at,
            project=project,
            analysis=analysis,
            diagnosis=filtered_diagnosis,
        )

        # JSON gets full data; display reporters get filtered data
        reporters = {
            "terminal": (lambda: TerminalReporter(self.config), filtered_report_data),
            "json": (lambda: JSONReporter(self.config), report_data),
            "html": (lambda: HTMLReporter(self.config), filtered_report_data),
            "markdown": (lambda: MarkdownReporter(self.config), filtered_report_data),
        }

        generated_files: dict[str, Path] = {}

        for fmt in self.config.output_formats:
            entry = reporters.get(fmt)
            if entry:
                factory, data = entry
                reporter = factory()
                result = await reporter.generate(data)
                if isinstance(result, Path):
                    generated_files[fmt] = result

        return report_data, generated_files
