"""Terminal reporter using Rich for beautiful console output."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import ExecutionReport
from autotest.models.project import ProjectInfo
from autotest.models.report import QualitySummary, ReportData
from autotest.reporter.base import BaseReporter


class TerminalReporter(BaseReporter):
    """Generates rich terminal output for test results."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.console = Console()

    async def generate(self, report_data: ReportData) -> str:
        """Generate full terminal report."""
        self.print_project_info(report_data.project)
        self.print_analysis(report_data.analysis)
        self.print_strategy(report_data.strategy)
        self.print_execution(report_data.execution)
        self.print_quality_summary(report_data.quality)
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

        # Print high-complexity functions
        if analysis.high_complexity_functions:
            hc_table = Table(title="High Complexity Functions", border_style="yellow")
            hc_table.add_column("Function")
            hc_table.add_column("File")
            hc_table.add_column("Complexity", justify="right")

            for func in analysis.high_complexity_functions[:10]:
                hc_table.add_row(
                    func.name,
                    str(func.file_path.name),
                    str(func.cyclomatic_complexity),
                )
            self.console.print(hc_table)

    def print_strategy(self, strategy: TestStrategy) -> None:
        """Print adaptation strategy info."""
        table = Table(title="Test Strategy", border_style="magenta")
        table.add_column("Language")
        table.add_column("Test Runner")
        table.add_column("Coverage Tool")
        table.add_column("Security Tool")

        for tc in strategy.toolchains:
            table.add_row(
                tc.language.value,
                tc.test_runner,
                tc.coverage_tool or "—",
                tc.security_tool or "—",
            )

        self.console.print(table)

        if strategy.ai_generation_used:
            stats = strategy.generation_stats
            unit_info = (
                f"Unit Tests - Attempted: {stats.get('attempted', 0)} | "
                f"Valid: [green]{stats.get('valid', 0)}[/] | "
                f"Failed: [red]{stats.get('failed', 0)}[/]"
            )
            integration_info = ""
            if stats.get('integration_valid', 0) > 0:
                integration_info = (
                    f"\nIntegration Tests - Generated: [green]{stats.get('integration_valid', 0)}[/] with mocks"
                )
            self.console.print(
                Panel(
                    unit_info + integration_info,
                    title="AI Test Generation",
                    border_style="magenta",
                )
            )

    def print_execution(self, execution: ExecutionReport) -> None:
        """Print execution results per phase."""
        for phase_result in execution.phases:
            color = "green" if phase_result.failed == 0 else "red"
            status = "PASS" if phase_result.failed == 0 else "FAIL"

            table = Table(
                title=f"Phase: {phase_result.phase.value.upper()} [{status}]",
                border_style=color,
            )
            table.add_column("Test", style="bold")
            table.add_column("Status")
            table.add_column("Duration", justify="right")
            table.add_column("Error")

            for test in phase_result.test_results:
                status_text = Text("PASS", style="green") if test.passed else Text("FAIL", style="red")
                table.add_row(
                    test.name,
                    status_text,
                    f"{test.duration_ms:.0f}ms",
                    (test.error_message or "")[:80],
                )

            self.console.print(table)

        # Overall summary
        total = sum(p.total_tests for p in execution.phases)
        passed = sum(p.passed for p in execution.phases)
        failed = sum(p.failed for p in execution.phases)

        summary_color = "green" if failed == 0 else "red"
        self.console.print(
            Panel(
                f"Total: {total} | "
                f"[green]Passed: {passed}[/] | "
                f"[red]Failed: {failed}[/] | "
                f"Pass Rate: {execution.overall_pass_rate * 100:.1f}%",
                title="Execution Summary",
                border_style=summary_color,
            )
        )

    def print_quality_summary(self, quality: QualitySummary) -> None:
        """Print quality score and recommendations."""
        score = quality.overall_score
        if score >= 80:
            score_style = "bold green"
        elif score >= 60:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        self.console.print(
            Panel(
                Text(f"{score:.0f}/100", style=score_style, justify="center"),
                title=f"Quality Score: {quality.test_health.upper()}",
                border_style=score_style.split()[-1],
            )
        )

        # Print detailed failed tests info
        if quality.failed_tests:
            self.console.print()
            table = Table(
                title="[bold red]Tests Fallidos - Detalle[/]",
                border_style="red",
                show_lines=True,
            )
            table.add_column("Test", style="bold", max_width=30)
            table.add_column("Categoría", justify="center", max_width=12)
            table.add_column("Recomendación", max_width=60)

            for test in quality.failed_tests[:10]:  # Show top 10
                category_colors = {
                    "import": "yellow",
                    "mock": "magenta",
                    "assertion": "red",
                    "syntax": "red",
                    "type": "cyan",
                    "attribute": "cyan",
                    "network": "blue",
                    "environment": "yellow",
                }
                cat_color = category_colors.get(test.category, "white")

                table.add_row(
                    test.test_name.split(":")[-1],  # Short name
                    f"[{cat_color}]{test.category.upper()}[/]",
                    test.recommendation[:100],
                )

            self.console.print(table)

            if len(quality.failed_tests) > 10:
                self.console.print(
                    f"[dim]... y {len(quality.failed_tests) - 10} tests más. "
                    "Ver reporte HTML para detalles completos.[/]"
                )

        if quality.risk_areas:
            self.console.print()
            tree = Tree("[bold red]Áreas de Riesgo[/]")
            for risk in quality.risk_areas:
                tree.add(f"[red]⚠ {risk}[/]")
            self.console.print(tree)

        if quality.recommendations:
            self.console.print()
            tree = Tree("[bold blue]Plan de Acción[/]")
            for rec in quality.recommendations[:15]:  # Limit to avoid spam
                # Handle markdown bold
                rec_formatted = rec.replace("**", "[bold]").replace("**", "[/bold]")
                tree.add(f"[blue]→ {rec_formatted}[/]")
            self.console.print(tree)
