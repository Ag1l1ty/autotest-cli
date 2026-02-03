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
    help="Analizador automatico de proyectos de software.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold]AutoTest CLI[/bold] v{__version__}")
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
    """AutoTest CLI - Analiza proyectos y ejecuta pruebas automaticamente."""


@app.command()
def scan(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto a analizar."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Archivo de configuracion."),
    output: str = typer.Option("terminal,html", "--output", "-o", help="Formatos de salida: terminal,json,html"),
    phases: str = typer.Option("smoke,unit,integration,quality", "--phases", "-p", help="Fases a ejecutar."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Desactivar generacion de tests con IA."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Detener en primera falla."),
    open_report: bool = typer.Option(False, "--open", help="Abrir reporte HTML en navegador."),
) -> None:
    """Ejecutar pipeline completo: detectar, analizar, adaptar, ejecutar, reportar."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    # Por defecto, guardar reportes en el directorio del proyecto
    output_dir = target / "reports"

    cfg = load_config(
        target_path=target,
        config_file=config,
        output_formats=output.split(","),
        phases=phases.split(","),
        ai_enabled=not no_ai,
        verbose=verbose,
        fail_fast=fail_fast,
        output_dir=output_dir,
    )

    asyncio.run(_run_pipeline(cfg, open_report=open_report))


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


@app.command()
def generate(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Desactivar generacion con IA."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
) -> None:
    """Generar estrategia de testing y tests con IA."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    cfg = load_config(target_path=target, ai_enabled=not no_ai, verbose=verbose)
    asyncio.run(_run_generate(cfg))


@app.command()
def execute(
    path: Path = typer.Argument(Path("."), help="Ruta al proyecto."),
    phases: str = typer.Option("smoke,unit,integration,quality", "--phases", "-p", help="Fases a ejecutar."),
    no_ai: bool = typer.Option(False, "--no-ai", help="Desactivar generacion con IA."),
    verbose: bool = typer.Option(False, "--verbose", help="Salida detallada."),
) -> None:
    """Ejecutar pruebas del proyecto."""
    target = path.resolve()
    if not target.exists():
        console.print(f"[red]Error:[/red] La ruta '{target}' no existe.")
        raise typer.Exit(1)

    cfg = load_config(
        target_path=target,
        phases=phases.split(","),
        ai_enabled=not no_ai,
        verbose=verbose,
    )
    asyncio.run(_run_execute(cfg))


# ── Pipeline runners ──


async def _run_pipeline(cfg: "AutoTestConfig", open_report: bool = False) -> None:
    """Run the full autotest pipeline."""
    import webbrowser
    from autotest.detector.scanner import ProjectScanner
    from autotest.analyzer.engine import AnalysisEngine
    from autotest.adaptation.engine import AdaptationEngine
    from autotest.executor.engine import ExecutionEngine
    from autotest.reporter.engine import ReportEngine

    console.print(Panel.fit(
        f"[bold cyan]AutoTest CLI v{__version__}[/bold cyan]\n"
        f"Proyecto: [green]{cfg.target_path}[/green]",
        title="AutoTest",
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
            return

        # Phase 2: Analyze
        task = progress.add_task("Analizando codigo...", total=None)
        analyzer = AnalysisEngine(cfg)
        analysis = await analyzer.analyze(project_info)
        progress.update(task, completed=True, description="[green]Analisis completado[/green]")

        # Phase 3: Adapt
        task = progress.add_task("Configurando estrategia de testing...", total=None)
        adapter = AdaptationEngine(cfg)
        strategy = await adapter.adapt(project_info, analysis)
        progress.update(task, completed=True, description="[green]Estrategia configurada[/green]")

        # Phase 4: Execute
        task = progress.add_task("Ejecutando pruebas...", total=None)
        executor = ExecutionEngine(cfg)
        execution = await executor.execute(strategy, cfg.target_path)
        progress.update(task, completed=True, description="[green]Pruebas completadas[/green]")

        # Phase 5: Report
        task = progress.add_task("Generando reportes...", total=None)
        reporter = ReportEngine(cfg)
        report_data, generated_files = await reporter.report(project_info, analysis, strategy, execution)
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


async def _run_generate(cfg: "AutoTestConfig") -> None:
    """Run detection + analysis + adaptation."""
    from autotest.detector.scanner import ProjectScanner
    from autotest.analyzer.engine import AnalysisEngine
    from autotest.adaptation.engine import AdaptationEngine
    from autotest.reporter.terminal import TerminalReporter

    scanner = ProjectScanner(cfg)
    project_info = await scanner.scan(cfg.target_path)
    analyzer = AnalysisEngine(cfg)
    analysis = await analyzer.analyze(project_info)
    adapter = AdaptationEngine(cfg)
    strategy = await adapter.adapt(project_info, analysis)
    reporter = TerminalReporter(cfg)
    reporter.print_project_info(project_info)
    reporter.print_analysis(analysis)
    reporter.print_strategy(strategy)


async def _run_execute(cfg: "AutoTestConfig") -> None:
    """Run detection + analysis + adaptation + execution."""
    from autotest.detector.scanner import ProjectScanner
    from autotest.analyzer.engine import AnalysisEngine
    from autotest.adaptation.engine import AdaptationEngine
    from autotest.executor.engine import ExecutionEngine
    from autotest.reporter.terminal import TerminalReporter

    scanner = ProjectScanner(cfg)
    project_info = await scanner.scan(cfg.target_path)
    analyzer = AnalysisEngine(cfg)
    analysis = await analyzer.analyze(project_info)
    adapter = AdaptationEngine(cfg)
    strategy = await adapter.adapt(project_info, analysis)
    executor = ExecutionEngine(cfg)
    execution = await executor.execute(strategy, cfg.target_path)
    reporter = TerminalReporter(cfg)
    reporter.print_project_info(project_info)
    reporter.print_analysis(analysis)
    reporter.print_strategy(strategy)
    reporter.print_execution(execution)
