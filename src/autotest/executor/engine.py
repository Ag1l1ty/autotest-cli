"""Execution engine - orchestrates test phase execution."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.executor.phases.smoke import SmokePhaseExecutor
from autotest.executor.phases.unit import UnitPhaseExecutor
from autotest.executor.phases.integration import IntegrationPhaseExecutor
from autotest.executor.phases.security import SecurityPhaseExecutor
from autotest.executor.phases.quality import QualityPhaseExecutor
from autotest.executor.sandbox import TestSandbox
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import ExecutionReport, PhaseResult
from autotest.models.project import TestPhase

PHASE_EXECUTORS = {
    TestPhase.SMOKE: SmokePhaseExecutor,
    TestPhase.UNIT: UnitPhaseExecutor,
    TestPhase.INTEGRATION: IntegrationPhaseExecutor,
    TestPhase.SECURITY: SecurityPhaseExecutor,
    TestPhase.QUALITY: QualityPhaseExecutor,
}

# Default phase order (smoke first, quality last)
PHASE_ORDER = [
    TestPhase.SMOKE,
    TestPhase.UNIT,
    TestPhase.INTEGRATION,
    TestPhase.SECURITY,
    TestPhase.QUALITY,
]


class ExecutionEngine:
    """Orchestrates the execution of test phases in order."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def execute(
        self,
        strategy: TestStrategy,
        project_root: Path,
    ) -> ExecutionReport:
        """Execute all configured test phases sequentially."""
        started = datetime.now()
        phase_results: list[PhaseResult] = []

        # Write generated tests to project (so they persist after execution)
        if strategy.generated_tests:
            self._write_tests_to_project(strategy.generated_tests, project_root)

        # Determine execution root (sandbox or direct)
        if self.config.sandbox_enabled and strategy.generated_tests:
            async with TestSandbox(project_root) as sandbox:
                sandbox.write_generated_tests(strategy.generated_tests)
                phase_results = await self._run_phases(
                    strategy, sandbox.path,
                )
        else:
            phase_results = await self._run_phases(strategy, project_root)

        finished = datetime.now()

        # Calculate overall metrics
        total_passed = sum(p.passed for p in phase_results)
        total_tests = sum(p.total_tests for p in phase_results)
        overall_pass_rate = total_passed / total_tests if total_tests else 0.0

        # Find coverage from unit phase if available
        overall_coverage = None
        for pr in phase_results:
            if pr.phase == TestPhase.UNIT and pr.coverage_percentage is not None:
                overall_coverage = pr.coverage_percentage
                break

        return ExecutionReport(
            phases=phase_results,
            total_duration=finished - started,
            overall_pass_rate=overall_pass_rate,
            overall_coverage=overall_coverage,
        )

    def _write_tests_to_project(
        self,
        tests: list,
        project_root: Path,
    ) -> None:
        """Write generated tests to the actual project directory (for persistence)."""
        from autotest.models.adaptation import GeneratedTest

        for test in tests:
            if not isinstance(test, GeneratedTest) or not test.is_valid:
                continue

            # Determine the relative path for the test file
            relative = test.file_path
            if relative.is_absolute():
                try:
                    relative = relative.relative_to(project_root)
                except ValueError:
                    # If not relative to project, put in tests/ directory
                    if "integration" in str(test.file_path).lower():
                        relative = Path("tests") / "integration" / test.file_path.name
                    else:
                        relative = Path("tests") / test.file_path.name

            target = project_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(test.source_code, encoding="utf-8")

            # Create __init__.py files for proper Python imports
            for parent in target.parents:
                if parent == project_root:
                    break
                init_file = parent / "__init__.py"
                if not init_file.exists():
                    init_file.touch()

    async def _run_phases(
        self,
        strategy: TestStrategy,
        execution_root: Path,
    ) -> list[PhaseResult]:
        """Run phases in order, optionally stopping on failure."""
        results: list[PhaseResult] = []

        # Filter and order phases
        phases_to_run = [
            p for p in PHASE_ORDER if p in strategy.phases_to_run
        ]

        for phase in phases_to_run:
            executor_cls = PHASE_EXECUTORS.get(phase)
            if not executor_cls:
                continue

            executor = executor_cls()
            result = await executor.execute(strategy, execution_root)
            results.append(result)

            # Fail-fast: stop if a phase has failures and config says so
            if self.config.fail_fast and result.failed > 0:
                break

        return results
