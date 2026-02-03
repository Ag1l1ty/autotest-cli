"""Phase 1: Smoke Tests - Verify project builds and basic functionality."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import run_command
from autotest.models.adaptation import TestStrategy, ToolChainConfig
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import TestPhase


def _get_python_cmd() -> str:
    """Get the correct Python command for the current system."""
    if sys.executable:
        return sys.executable
    if shutil.which("python3"):
        return "python3"
    return "python"


PYTHON = _get_python_cmd()


class SmokePhaseExecutor(BasePhaseExecutor):

    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.SMOKE

    async def execute(self, strategy: TestStrategy, project_root: Path) -> PhaseResult:
        started = datetime.now()
        test_results: list[TestResult] = []

        for toolchain in strategy.toolchains:
            # Get smoke test command
            cmd = self._get_smoke_command(toolchain, project_root)
            if not cmd:
                continue

            result = await run_command(cmd, cwd=project_root, timeout=60)

            test_results.append(TestResult(
                name=f"smoke:{toolchain.language.value}:build",
                passed=result.return_code == 0,
                duration_ms=result.duration_ms,
                error_message=result.stderr if result.return_code != 0 else None,
                stdout=result.stdout[:2000],
                stderr=result.stderr[:2000],
            ))

            # Check if dependencies are available
            dep_result = await self._check_dependencies(toolchain, project_root)
            if dep_result:
                test_results.append(dep_result)

        finished = datetime.now()
        passed = sum(1 for t in test_results if t.passed)
        failed = sum(1 for t in test_results if not t.passed)

        return PhaseResult(
            phase=TestPhase.SMOKE,
            started_at=started,
            finished_at=finished,
            duration=finished - started,
            total_tests=len(test_results),
            passed=passed,
            failed=failed,
            success_rate=passed / len(test_results) if test_results else 0.0,
            test_results=test_results,
        )

    def _get_smoke_command(self, toolchain: ToolChainConfig, project_root: Path) -> list[str] | None:
        """Get the appropriate smoke test command for a toolchain."""
        from autotest.models.project import Language

        # For Python, compile all .py files in the project
        if toolchain.language == Language.PYTHON:
            py_files = list(project_root.glob("**/*.py"))
            if py_files:
                return [PYTHON, "-m", "py_compile"] + [str(f) for f in py_files[:20]]
            return [PYTHON, "--version"]  # fallback

        smoke_cmds = {
            Language.JAVASCRIPT: ["node", "--version"],
            Language.TYPESCRIPT: ["npx", "tsc", "--noEmit"],
            Language.JAVA: toolchain.test_command[:1] + ["compile"] if "mvn" in str(toolchain.test_command) else ["./gradlew", "compileJava"],
            Language.GO: ["go", "build", "./..."],
            Language.RUST: ["cargo", "check"],
            Language.CSHARP: ["dotnet", "build"],
        }
        return smoke_cmds.get(toolchain.language)

    async def _check_dependencies(
        self,
        toolchain: ToolChainConfig,
        project_root: Path,
    ) -> TestResult | None:
        """Check if project dependencies are available."""
        from autotest.models.project import Language
        dep_cmds = {
            Language.PYTHON: [PYTHON, "-m", "pip", "check"],
            Language.JAVASCRIPT: ["npm", "ls", "--all"],
            Language.GO: ["go", "mod", "verify"],
            Language.RUST: ["cargo", "verify-project"],
            Language.CSHARP: ["dotnet", "restore", "--no-build"],
        }
        cmd = dep_cmds.get(toolchain.language)
        if not cmd:
            return None

        result = await run_command(cmd, cwd=project_root, timeout=60)
        return TestResult(
            name=f"smoke:{toolchain.language.value}:dependencies",
            passed=result.return_code == 0,
            duration_ms=result.duration_ms,
            error_message=result.stderr[:500] if result.return_code != 0 else None,
        )
