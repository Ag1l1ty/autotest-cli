"""Markdown reporter for GitHub PRs and CI/CD logs."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.diagnosis import Severity
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Generates Markdown reports suitable for GitHub PR comments."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def generate(self, report_data: ReportData) -> Path:
        """Generate Markdown report file."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"autotest-report-{report_data.report_id}.md"

        lines: list[str] = []
        diag = report_data.diagnosis

        # Header
        lines.append(f"# Code Doctor: {report_data.project.name}")
        lines.append("")

        if not diag:
            lines.append("No diagnosis data available.")
            output_path.write_text("\n".join(lines), encoding="utf-8")
            return output_path

        # Health score
        lines.append(f"**Health Score:** {diag.health_score:.0f}/100 ({diag.health_label.upper()})")
        lines.append(f"**Critical:** {diag.critical_count} | **Warning:** {diag.warning_count} | **Info:** {diag.info_count}")
        lines.append("")

        # Top actions
        actionable = [f for f in diag.findings if f.suggested_fix][:self.config.top_findings]
        if actionable:
            lines.append("## Top Acciones Prioritarias")
            lines.append("")
            for i, finding in enumerate(actionable, 1):
                loc = ""
                if finding.file_path and finding.line_start:
                    loc = f" — `{finding.file_path}:{finding.line_start}`"
                lines.append(f"{i}. **{finding.suggested_fix.description}**{loc}")
            lines.append("")

        # Findings by severity
        severity_groups = [
            ("Critical", Severity.CRITICAL, diag.critical_count),
            ("Warning", Severity.WARNING, diag.warning_count),
            ("Info", Severity.INFO, diag.info_count),
        ]

        for label, sev, count in severity_groups:
            if count == 0:
                continue
            group = [f for f in diag.findings if f.severity == sev]
            lines.append(f"## {label} ({count})")
            lines.append("")

            for finding in group:
                loc = ""
                if finding.file_path:
                    loc = f"`{finding.file_path}"
                    if finding.line_start:
                        loc += f":{finding.line_start}"
                    loc += "` "
                lines.append(f"### {finding.id} — {finding.title}")
                lines.append("")
                if loc:
                    lines.append(f"**Location:** {loc}")
                lines.append(f"**Category:** {finding.category.value}")
                lines.append("")
                lines.append(finding.description)
                lines.append("")

                if finding.suggested_fix:
                    fix = finding.suggested_fix
                    lines.append(f"> **Fix:** {fix.description}")
                    lines.append("")
                    if fix.code_before and fix.code_after:
                        lines.append("```diff")
                        for line in fix.code_before.splitlines():
                            lines.append(f"- {line}")
                        for line in fix.code_after.splitlines():
                            lines.append(f"+ {line}")
                        lines.append("```")
                        lines.append("")
                    if fix.explanation:
                        lines.append(f"*{fix.explanation}*")
                        lines.append("")

        # Summary
        lines.append("---")
        lines.append("")
        lines.append(f"*{diag.summary}*")
        lines.append("")
        if diag.ai_tokens_used > 0:
            lines.append(
                f"AI: {diag.functions_analyzed} funciones analizadas | "
                f"{diag.ai_tokens_used} tokens"
            )
            lines.append("")
        lines.append(f"Report ID: `{report_data.report_id}` | Code Doctor v{report_data.autotest_version}")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
