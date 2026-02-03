"""Phase 3: Integration Tests - Test cross-module interactions with mocks."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import run_command
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import Language, TestPhase


def _get_python_cmd() -> str:
    """Get the correct Python command for the current system."""
    if sys.executable:
        return sys.executable
    if shutil.which("python3"):
        return "python3"
    return "python"


PYTHON = _get_python_cmd()


class IntegrationPhaseExecutor(BasePhaseExecutor):

    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.INTEGRATION

    async def execute(self, strategy: TestStrategy, project_root: Path) -> PhaseResult:
        started = datetime.now()
        test_results: list[TestResult] = []

        # 1. Run existing integration tests (marked with @pytest.mark.integration)
        for toolchain in strategy.toolchains:
            cmd = self._get_integration_command(toolchain.language, toolchain)
            if not cmd:
                continue

            result = await run_command(cmd, cwd=project_root, timeout=300)

            # Only add if tests were found
            if "no tests ran" not in result.stdout.lower() and result.return_code != 5:
                test_results.append(TestResult(
                    name=f"integration:{toolchain.language.value}:existing",
                    passed=result.return_code == 0,
                    duration_ms=result.duration_ms,
                    error_message=result.stderr[:2000] if result.return_code != 0 else None,
                    stdout=result.stdout[:3000],
                    stderr=result.stderr[:2000],
                ))

        # 2. Run generated integration tests
        generated_integration_tests = [
            t for t in strategy.generated_tests
            if t.is_valid and "integration" in str(t.file_path).lower()
        ]

        if generated_integration_tests:
            # Write tests to temp location and run them
            # Set up PYTHONPATH to include project root for imports
            env_with_path = {"PYTHONPATH": str(project_root)}

            for test in generated_integration_tests:
                test_dir = project_root / "tests" / "integration"
                test_dir.mkdir(parents=True, exist_ok=True)

                # Create __init__.py files to make it a proper package
                (project_root / "tests").mkdir(parents=True, exist_ok=True)
                (project_root / "tests" / "__init__.py").touch()
                (test_dir / "__init__.py").touch()

                test_file = test_dir / test.file_path.name
                test_file.write_text(test.source_code, encoding="utf-8")

                # Run the specific test file with PYTHONPATH set
                cmd = [PYTHON, "-m", "pytest", str(test_file), "-v", "--tb=short"]
                result = await run_command(cmd, cwd=project_root, timeout=120, env=env_with_path)

                test_results.append(TestResult(
                    name=f"integration:generated:{test.target_function}",
                    passed=result.return_code == 0,
                    duration_ms=result.duration_ms,
                    error_message=result.stderr[:2000] if result.return_code != 0 else None,
                    stdout=result.stdout[:3000],
                    stderr=result.stderr[:2000],
                    is_generated=True,
                ))

        # If no tests at all, add a placeholder result
        if not test_results:
            test_results.append(TestResult(
                name="integration:no-tests",
                passed=True,
                duration_ms=0,
                stdout="No integration tests found or generated",
            ))

        finished = datetime.now()
        passed = sum(1 for t in test_results if t.passed)

        return PhaseResult(
            phase=TestPhase.INTEGRATION,
            started_at=started,
            finished_at=finished,
            duration=finished - started,
            total_tests=len(test_results),
            passed=passed,
            failed=len(test_results) - passed,
            success_rate=passed / len(test_results) if test_results else 0.0,
            test_results=test_results,
        )

    def _get_integration_command(self, language: Language, toolchain) -> list[str] | None:
        cmds = {
            Language.PYTHON: [PYTHON, "-m", "pytest", "-v", "-m", "integration", "--tb=short", "-q"],
            Language.JAVASCRIPT: ["npx", toolchain.test_runner, "run", "--testPathPattern=integration"],
            Language.JAVA: toolchain.test_command[:1] + ["verify"],
            Language.GO: ["go", "test", "./...", "-v", "-run", "Integration"],
            Language.RUST: ["cargo", "test", "--test", "*"],
            Language.CSHARP: ["dotnet", "test", "--filter", "Category=Integration"],
        }
        return cmds.get(language)
