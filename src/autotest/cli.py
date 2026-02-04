"""AutoTest CLI - Main entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from autotest import __version__
from autotest.config import load_config

app = typer.Typer(
    name="autotest",
    help="Code Doctor - Diagnostico inteligente de proyectos de software.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold]Code Doctor[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Mostrar version.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Code Doctor - Encuentra problemas reales y da fixes concretos."""


@app.command()
def diagnose(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto a diagnosticar."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Archivo de configuracion."),
    output: str = typer.Option("terminal,html", "--output", "-o", help="Formatos de salida: terminal,json,html,markdown"),
    severity: str = typer.Option("critical,warning", "--severity", "-s", help="Severidades a mostrar: critical,warning,info"),
    top: int = typer.Option(5, "--top", "-t", help="Numero maximo de findings por grupo de severidad."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Desactivar revision con IA."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
    open_report: bool = typer.Option(False, "--open", help="Abrir reporte HTML en navegador."),
    fix: bool = typer.Option(False, "--fix", help="Aplicar fixes automaticamente al codigo fuente."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Mostrar que fixes se aplicarian sin modificar archivos."),
) -> None:
    """Diagnosticar proyecto: detectar, analizar, diagnosticar, reportar."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    output_dir = target / "reports"

    cfg = load_config(
        target_path=target,
        config_file=config,
        output_formats=output.split(","),
        ai_enabled=not no_ai,
        verbose=verbose,
        output_dir=output_dir,
        severity_filter=severity.split(","),
        top_findings=top,
    )

    exit_code = asyncio.run(_run_diagnosis(
        cfg, open_report=open_report, apply_fix=fix, dry_run=dry_run
    ))
    raise typer.Exit(exit_code)


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto a analizar."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Archivo de configuracion."),
    output: str = typer.Option("terminal,html", "--output", "-o", help="Formatos de salida: terminal,json,html,markdown"),
    severity: str = typer.Option("critical,warning", "--severity", "-s", help="Severidades a mostrar."),
    top: int = typer.Option(5, "--top", "-t", help="Numero maximo de findings por grupo de severidad."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Desactivar revision con IA."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
    open_report: bool = typer.Option(False, "--open", help="Abrir reporte HTML en navegador."),
    fix: bool = typer.Option(False, "--fix", help="Aplicar fixes automaticamente al codigo fuente."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Mostrar que fixes se aplicarian sin modificar archivos."),
) -> None:
    """Ejecutar diagnostico completo (alias de diagnose)."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    output_dir = target / "reports"

    cfg = load_config(
        target_path=target,
        config_file=config,
        output_formats=output.split(","),
        ai_enabled=not no_ai,
        verbose=verbose,
        output_dir=output_dir,
        severity_filter=severity.split(","),
        top_findings=top,
    )

    exit_code = asyncio.run(_run_diagnosis(
        cfg, open_report=open_report, apply_fix=fix, dry_run=dry_run
    ))
    raise typer.Exit(exit_code)


@app.command()
def detect(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
) -> None:
    """Detectar tecnologias del proyecto."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    cfg = load_config(target_path=target, verbose=verbose)
    asyncio.run(_run_detect(cfg))


@app.command()
def analyze(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
) -> None:
    """Analizar codigo del proyecto."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    cfg = load_config(target_path=target, verbose=verbose)
    asyncio.run(_run_analyze(cfg))


# ── Pipeline runners ──


async def _run_diagnosis(
    cfg: "AutoTestConfig",
    open_report: bool = False,
    apply_fix: bool = False,
    dry_run: bool = False,
) -> int:
    """Run the diagnosis pipeline: Detect -> Analyze -> Diagnose -> Report.

    Returns:
        Exit code: 0 = healthy, 1 = critical findings found.
    """
    import webbrowser
    from autotest.detector.scanner import ProjectScanner
    from autotest.analyzer.engine import AnalysisEngine
    from autotest.diagnosis.engine import DiagnosisEngine
    from autotest.reporter.engine import ReportEngine

    console.print(Panel.fit(
        f"[bold cyan]Code Doctor v{__version__}[/bold cyan]\n"
        f"Proyecto: [green]{cfg.target_path}[/green]",
        title="Code Doctor",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Phase 1: Detect
        task = progress.add_task("Detectando tecnologias...", total=None)
        scanner = ProjectScanner(cfg)
        project_info = await scanner.scan(cfg.target_path)
        progress.update(task, completed=True, description="[green]Deteccion completada[/green]")

        if not project_info.languages:
            console.print("[yellow]No se detectaron lenguajes soportados.[/yellow]")
            return 0

        # Phase 2: Analyze
        task = progress.add_task("Analizando codigo...", total=None)
        analyzer = AnalysisEngine(cfg)
        analysis = await analyzer.analyze(project_info)
        progress.update(task, completed=True, description="[green]Analisis completado[/green]")

        # Phase 3: Diagnose
        ai_label = "" if cfg.ai_enabled and cfg.ai_api_key else " (sin IA)"
        task = progress.add_task(f"Diagnosticando{ai_label}...", total=None)
        diagnoser = DiagnosisEngine(cfg)
        diagnosis = await diagnoser.diagnose(project_info, analysis)
        progress.update(task, completed=True, description="[green]Diagnostico completado[/green]")

        # Phase 4: Report
        task = progress.add_task("Generando reportes...", total=None)
        reporter = ReportEngine(cfg)
        report_data, generated_files = await reporter.report_diagnosis(
            project_info, analysis, diagnosis
        )
        progress.update(task, completed=True, description="[green]Reportes generados[/green]")

    # Show generated report files
    if generated_files:
        console.print()
        console.print(Panel(
            "\n".join([
                f"[bold]{fmt.upper()}:[/bold] [link=file://{path}]{path}[/link]"
                for fmt, path in generated_files.items()
            ]) + f"\n\n[dim]Report ID: {report_data.report_id}[/dim]",
            title="[green]Reportes Generados[/green]",
            border_style="green",
        ))

        # Open HTML report in browser if requested
        if open_report and "html" in generated_files:
            html_path = generated_files["html"]
            console.print(f"\n[cyan]Abriendo reporte en navegador...[/cyan]")
            webbrowser.open(f"file://{html_path}")

    # Auto-fix mode
    if apply_fix or dry_run:
        from autotest.diagnosis.auto_fixer import apply_fixes

        mode_label = "[yellow]DRY RUN[/yellow] " if dry_run else ""
        console.print(f"\n{mode_label}[bold]Aplicando fixes...[/bold]")

        fix_report = apply_fixes(
            diagnosis.findings, cfg.target_path, dry_run=dry_run
        )

        if fix_report.applied:
            console.print(f"[green]Fixes aplicados: {fix_report.applied_count}[/green]")
            for r in fix_report.applied:
                console.print(f"  [green]OK[/green] {r.finding_id} {r.file_path} — {r.message}")

        if fix_report.skipped:
            console.print(f"[yellow]Fixes omitidos: {fix_report.skipped_count}[/yellow]")
            for r in fix_report.skipped:
                console.print(f"  [dim]--[/dim] {r.finding_id} {r.file_path} — {r.message}")

        if fix_report.failed:
            console.print(f"[red]Fixes fallidos: {len(fix_report.failed)}[/red]")
            for r in fix_report.failed:
                console.print(f"  [red]!![/red] {r.finding_id} {r.file_path} — {r.message}")

    # Exit code: 1 if critical findings found (useful for CI/CD)
    if diagnosis.critical_count > 0:
        console.print(
            f"\n[bold red]Exit 1:[/bold red] {diagnosis.critical_count} problema(s) critico(s) encontrado(s)."
        )
        return 1
    return 0


async def _run_detect(cfg: "AutoTestConfig") -> None:
    """Run only the detection phase."""
    from autotest.detector.scanner import ProjectScanner
    from autotest.reporter.terminal import TerminalReporter

    scanner = ProjectScanner(cfg)
    project_info = await scanner.scan(cfg.target_path)
    reporter = TerminalReporter(cfg)
    reporter.print_project_info(project_info)


async def _run_analyze(cfg: "AutoTestConfig") -> None:
    """Run detection + analysis."""
    from autotest.detector.scanner import ProjectScanner
    from autotest.analyzer.engine import AnalysisEngine
    from autotest.reporter.terminal import TerminalReporter

    scanner = ProjectScanner(cfg)
    project_info = await scanner.scan(cfg.target_path)
    analyzer = AnalysisEngine(cfg)
    analysis = await analyzer.analyze(project_info)
    reporter = TerminalReporter(cfg)
    reporter.print_project_info(project_info)
    reporter.print_analysis(analysis)
