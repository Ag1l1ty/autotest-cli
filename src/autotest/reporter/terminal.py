"""Terminal reporter using Rich for beautiful console output."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport
from autotest.models.diagnosis import DiagnosisReport, Finding, Severity
from autotest.models.project import ProjectInfo
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter


class TerminalReporter(BaseReporter):
    """Generates rich terminal output for diagnosis results."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.console = Console()

    async def generate(self, report_data: ReportData) -> str:
        """Generate full terminal report."""
        self.print_project_info(report_data.project)
        self.print_analysis(report_data.analysis)
        if report_data.diagnosis:
            self.print_diagnosis(
                report_data.diagnosis,
                top_n=self.config.top_findings,
                severity_filter=self.config.severity_filter,
            )
        return "terminal"

    def print_project_info(self, project: ProjectInfo) -> None:
        """Print project overview panel."""
        tree = Tree(f"[bold blue]{project.name}[/]")
        tree.add(f"Path: {project.root_path}")

        lang_branch = tree.add("[bold]Languages[/]")
        for lang_info in project.languages:
            lang_branch.add(
                f"{lang_info.language.value} — "
                f"{lang_info.percentage:.1f}% ({lang_info.total_loc} LOC)"
            )

        self.console.print(Panel(tree, title="Project Info", border_style="blue"))

    def print_analysis(self, analysis: AnalysisReport) -> None:
        """Print analysis results table."""
        table = Table(title="Code Analysis", border_style="cyan")
        table.add_column("Metric", style="bold")
        table.add_column("Value", justify="right")

        table.add_row("Total Functions", str(analysis.total_functions))
        table.add_row("Tested Functions", str(analysis.tested_function_count))
        table.add_row("Untested Functions", str(len(analysis.untested_functions)))
        table.add_row("Avg Complexity", f"{analysis.avg_complexity:.1f}")
        table.add_row("Total LOC", str(analysis.total_loc))
        table.add_row("Dead Code Functions", str(len(analysis.dead_code_functions)))
        table.add_row("High Complexity Functions", str(len(analysis.high_complexity_functions)))

        if analysis.estimated_coverage > 0:
            table.add_row("Estimated Coverage", f"{analysis.estimated_coverage:.1f}%")

        self.console.print(table)

    def print_diagnosis(
        self,
        diagnosis: DiagnosisReport,
        top_n: int = 5,
        severity_filter: list[str] | None = None,
    ) -> None:
        """Print diagnosis findings with actionable output."""
        self.console.print()

        # Health Score
        score = diagnosis.health_score
        label = diagnosis.health_label.upper()
        if score >= 80:
            score_style = "bold green"
        elif score >= 60:
            score_style = "bold yellow"
        elif score >= 40:
            score_style = "bold red"
        else:
            score_style = "bold red"

        self.console.print(Panel(
            f"[{score_style}]{score:.0f}/100[/] ({label})",
            title="Health Score",
            border_style=score_style.split()[-1],
        ))

        # Filter findings by severity
        filter_set = set(severity_filter or ["critical", "warning"])
        findings = [
            f for f in diagnosis.findings
            if f.severity.value in filter_set
        ]

        if not findings:
            self.console.print("[green]No se encontraron problemas con la severidad seleccionada.[/green]")
            return

        # Group by severity
        criticals = [f for f in findings if f.severity == Severity.CRITICAL]
        warnings = [f for f in findings if f.severity == Severity.WARNING]
        infos = [f for f in findings if f.severity == Severity.INFO]

        if criticals:
            self.console.print()
            self._print_finding_group("CRITICAL", criticals, "red", top_n)

        if warnings:
            self.console.print()
            self._print_finding_group("WARNING", warnings, "yellow", top_n)

        if infos:
            self.console.print()
            self._print_finding_group("INFO", infos, "dim", top_n)

        # Top Actions
        self.console.print()
        actionable = [f for f in findings if f.suggested_fix][:top_n]
        if actionable:
            self.console.print(f"[bold]Top {min(top_n, len(actionable))} acciones:[/]")
            for i, finding in enumerate(actionable, 1):
                location = ""
                if finding.file_path and finding.line_start:
                    location = f" en {Path(finding.file_path).name}:{finding.line_start}"
                fix = finding.suggested_fix
                self.console.print(
                    f"  {i}. {fix.description}{location}"
                )

        # Summary
        self.console.print()
        self.console.print(f"[dim]{diagnosis.summary}[/]")

        if diagnosis.ai_tokens_used > 0:
            self.console.print(
                f"[dim]AI: {diagnosis.functions_analyzed} funciones analizadas, "
                f"{diagnosis.ai_tokens_used} tokens usados[/]"
            )

        # Hidden findings indicator
        total_findings = diagnosis.critical_count + diagnosis.warning_count + diagnosis.info_count
        shown_findings = len(findings)
        hidden_count = total_findings - shown_findings
        if hidden_count > 0:
            self.console.print(
                f"[dim]{hidden_count} hallazgo(s) oculto(s) por filtro de severidad "
                f"— usar --severity critical,warning,info para verlos.[/]"
            )

    def _print_finding_group(
        self,
        label: str,
        findings: list[Finding],
        color: str,
        max_show: int = 0,
    ) -> None:
        """Print a group of findings with the same severity."""
        total = len(findings)
        self.console.print(f"[bold {color}]{label} ({total})[/]")

        # Category mini-summary
        cat_counts = Counter(f.category.value.replace("_", " ") for f in findings)
        summary = ", ".join(f"{n} {cat}" for cat, n in cat_counts.most_common())
        if summary:
            self.console.print(f"[dim]  {summary}[/]")

        show = findings[:max_show] if max_show > 0 else findings
        hidden = total - len(show)

        for finding in show:
            # ID + category + location
            location = ""
            if finding.file_path:
                fname = Path(finding.file_path).name
                if finding.line_start:
                    location = f"{fname}:{finding.line_start}"
                else:
                    location = fname

            category = finding.category.value.replace("_", " ")
            self.console.print(
                f"[{color}]{finding.id}[/]  "
                f"[dim]{category:<14}[/] "
                f"[bold]{location:<25}[/] "
                f"{finding.title}"
            )

            # Fix preview
            if finding.suggested_fix:
                fix = finding.suggested_fix
                if fix.description:
                    self.console.print(
                        f"{'':>6}Fix: {fix.description}"
                    )
                if fix.code_after:
                    for line in fix.code_after.splitlines()[:3]:
                        self.console.print(f"{'':>6}[green]>>> {line}[/]")

        if hidden > 0:
            self.console.print(f"[dim]  ... y {hidden} mas (usar --top {total} para ver todos)[/]")
