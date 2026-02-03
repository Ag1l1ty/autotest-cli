"""Phase 5: Quality Tests - Linting, type checking, and code quality."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import run_command
from autotest.models.adaptation import TestStrategy, ToolChainConfig
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import Language, TestPhase


class QualityPhaseExecutor(BasePhaseExecutor):

    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.QUALITY

    async def execute(self, strategy: TestStrategy, project_root: Path) -> PhaseResult:
        started = datetime.now()
        test_results: list[TestResult] = []

        for toolchain in strategy.toolchains:
            # Run each quality command defined in the toolchain
            for i, cmd in enumerate(toolchain.quality_commands):
                if not cmd:
                    continue

                tool_name = (
                    toolchain.quality_tools[i]
                    if i < len(toolchain.quality_tools)
                    else f"quality-{i}"
                )

                result = await run_command(cmd, cwd=project_root, timeout=120)
                test_results.append(TestResult(
                    name=f"quality:{toolchain.language.value}:{tool_name}",
                    passed=result.return_code == 0,
                    duration_ms=result.duration_ms,
                    error_message=result.stderr[:2000] if result.return_code != 0 else None,
                    stdout=result.stdout[:3000],
                    stderr=result.stderr[:2000],
                ))

            # If no quality commands are configured, try defaults
            if not toolchain.quality_commands:
                fallback_results = await self._run_fallback_quality(
                    toolchain.language, project_root,
                )
                test_results.extend(fallback_results)

        finished = datetime.now()
        passed = sum(1 for t in test_results if t.passed)

        return PhaseResult(
            phase=TestPhase.QUALITY,
            started_at=started,
            finished_at=finished,
            duration=finished - started,
            total_tests=len(test_results),
            passed=passed,
            failed=len(test_results) - passed,
            success_rate=passed / len(test_results) if test_results else 0.0,
            test_results=test_results,
        )

    async def _run_fallback_quality(
        self,
        language: Language,
        project_root: Path,
    ) -> list[TestResult]:
        """Run default quality checks when no toolchain config exists."""
        results: list[TestResult] = []

        fallbacks: dict[Language, list[tuple[str, list[str]]]] = {
            Language.PYTHON: [
                ("ruff", ["ruff", "check", "."]),
                ("mypy", ["mypy", ".", "--ignore-missing-imports"]),
            ],
            Language.JAVASCRIPT: [
                ("eslint", ["npx", "eslint", "."]),
            ],
            Language.TYPESCRIPT: [
                ("eslint", ["npx", "eslint", "."]),
                ("tsc", ["npx", "tsc", "--noEmit"]),
            ],
            Language.JAVA: [
                ("checkstyle", ["mvn", "checkstyle:check"]),
            ],
            Language.GO: [
                ("vet", ["go", "vet", "./..."]),
                ("staticcheck", ["staticcheck", "./..."]),
            ],
            Language.RUST: [
                ("clippy", ["cargo", "clippy", "--", "-D", "warnings"]),
            ],
            Language.CSHARP: [
                ("dotnet-format", ["dotnet", "format", "--verify-no-changes"]),
            ],
        }

        for tool_name, cmd in fallbacks.get(language, []):
            result = await run_command(cmd, cwd=project_root, timeout=120)
            results.append(TestResult(
                name=f"quality:{language.value}:{tool_name}",
                passed=result.return_code == 0,
                duration_ms=result.duration_ms,
                error_message=result.stderr[:2000] if result.return_code != 0 else None,
                stdout=result.stdout[:3000],
                stderr=result.stderr[:2000],
            ))

        return results
