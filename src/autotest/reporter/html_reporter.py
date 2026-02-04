"""HTML reporter using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

import jinja2

from collections import Counter

from autotest.config import AutoTestConfig
from autotest.models.diagnosis import Finding, Severity
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter

TEMPLATE_DIR = Path(__file__).parent / "templates"


class HTMLReporter(BaseReporter):
    """Generates interactive HTML reports."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    async def generate(self, report_data: ReportData) -> Path:
        """Generate HTML report file with unique ID in filename."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use report_id in filename for uniqueness
        output_path = output_dir / f"autotest-report-{report_data.report_id}.html"

        template = self.env.get_template("report.html.j2")

        # Pre-compute grouped findings for clean template rendering
        diag = report_data.diagnosis
        analysis = report_data.analysis
        top_actions: list = []
        criticals: list = []
        warnings: list = []
        infos: list = []
        if diag:
            top_actions = [f for f in diag.findings if f.suggested_fix][:3]
            criticals = [f for f in diag.findings if f.severity == Severity.CRITICAL]
            warnings = [f for f in diag.findings if f.severity == Severity.WARNING]
            infos = [f for f in diag.findings if f.severity == Severity.INFO]

        # Highlights: positive metrics
        highlights: list[tuple[str, str]] = []
        if analysis.estimated_coverage >= 70:
            highlights.append(("check", f"{analysis.estimated_coverage:.0f}% coverage estimado"))
        if analysis.tested_function_count > 0:
            ratio = analysis.tested_function_count / max(analysis.total_functions, 1) * 100
            highlights.append((
                "check",
                f"{analysis.tested_function_count} de {analysis.total_functions} funciones testeadas ({ratio:.0f}%)",
            ))
        if diag and diag.critical_count == 0:
            highlights.append(("shield", "0 problemas criticos encontrados"))
        security_findings = [
            f for f in (diag.findings if diag else [])
            if f.category.value == "security"
        ]
        if not security_findings:
            highlights.append(("lock", "Sin vulnerabilidades de seguridad detectadas"))

        # Untested function names for the Functions card
        untested_names = [f.name for f in analysis.untested_functions[:5]]
        untested_total = len(analysis.untested_functions)

        # CC values for urgency gradient (parse from title)
        cc_values: dict[str, int] = {}
        for f in warnings + criticals:
            if "CC=" in f.title:
                try:
                    cc_values[f.id] = int(f.title.split("CC=")[1])
                except (ValueError, IndexError):
                    pass

        # Sort top_actions by CC descending (highest impact first)
        top_actions.sort(
            key=lambda f: cc_values.get(f.id, 0),
            reverse=True,
        )

        # Hidden findings count (filtered out by severity)
        hidden_info_count = (diag.info_count - len(infos)) if diag else 0
        hidden_warning_count = (diag.warning_count - len(warnings)) if diag else 0
        hidden_total = hidden_info_count + hidden_warning_count

        # Health score breakdown for desglose
        score_breakdown: list[tuple[str, float]] = []
        if diag:
            crit_penalty = min(diag.critical_count * 10, 40)
            warn_penalty = min(diag.warning_count * 3, 30)
            info_penalty = min(diag.info_count * 1, 10)
            coverage_penalty = 0.0
            if analysis.estimated_coverage < 100:
                coverage_penalty = round((1 - analysis.estimated_coverage / 100) * 15, 1)
            if crit_penalty > 0:
                score_breakdown.append((f"{diag.critical_count} critico(s)", crit_penalty))
            if warn_penalty > 0:
                score_breakdown.append((f"{diag.warning_count} warning(s)", warn_penalty))
            if info_penalty > 0:
                score_breakdown.append((f"{diag.info_count} nota(s)", info_penalty))
            if coverage_penalty > 0:
                score_breakdown.append(("coverage gap", coverage_penalty))

        # Category summaries per severity group (e.g. "16 complexity, 4 missing_tests")
        def _category_summary(findings: list[Finding]) -> str:
            counts = Counter(f.category.value.replace("_", " ") for f in findings)
            return ", ".join(f"{n} {cat}" for cat, n in counts.most_common())

        warning_summary = _category_summary(warnings) if warnings else ""
        critical_summary = _category_summary(criticals) if criticals else ""
        info_summary = _category_summary(infos) if infos else ""

        # Fixable count (findings with code_after)
        fixable_count = sum(
            1 for f in (diag.findings if diag else [])
            if f.suggested_fix and f.suggested_fix.code_after
        )

        # Prepare template context
        context = {
            "report": report_data,
            "report_id": report_data.report_id,
            "project": report_data.project,
            "analysis": analysis,
            "diagnosis": diag,
            "top_actions": top_actions,
            "criticals": criticals,
            "warnings": warnings,
            "infos": infos,
            "highlights": highlights,
            "untested_names": untested_names,
            "untested_total": untested_total,
            "cc_values": cc_values,
            "warning_summary": warning_summary,
            "critical_summary": critical_summary,
            "info_summary": info_summary,
            "score_breakdown": score_breakdown,
            "hidden_total": hidden_total,
            "fixable_count": fixable_count,
            "generated_at": report_data.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "version": report_data.autotest_version,
        }

        html_content = template.render(**context)
        output_path.write_text(html_content, encoding="utf-8")

        return output_path
