"""Phase 2: Unit Tests - Run existing and generated unit tests."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import run_command
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import TestPhase


class UnitPhaseExecutor(BasePhaseExecutor):

    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.UNIT

    async def execute(self, strategy: TestStrategy, project_root: Path) -> PhaseResult:
        started = datetime.now()
        test_results: list[TestResult] = []
        coverage_pct: float | None = None
        last_result = None

        for toolchain in strategy.toolchains:
            # Run test suite
            result = await run_command(
                toolchain.test_command,
                cwd=project_root,
                timeout=300,
                env=toolchain.env_vars,
            )
            last_result = result

            # Parse test output
            parsed = self._parse_test_output(result.stdout + result.stderr, toolchain.test_runner)
            if parsed:
                test_results.extend(parsed)
            else:
                test_results.append(TestResult(
                    name=f"unit:{toolchain.language.value}:suite",
                    passed=result.return_code == 0,
                    duration_ms=result.duration_ms,
                    error_message=result.stderr[:2000] if result.return_code != 0 else None,
                    stdout=result.stdout[:3000],
                    stderr=result.stderr[:2000],
                ))

            # Run coverage
            if toolchain.coverage_command:
                cov_result = await run_command(
                    toolchain.coverage_command,
                    cwd=project_root,
                    timeout=300,
                    env=toolchain.env_vars,
                )
                coverage_pct = self._parse_coverage(cov_result.stdout + cov_result.stderr)

        finished = datetime.now()
        passed = sum(1 for t in test_results if t.passed)
        failed = sum(1 for t in test_results if not t.passed)

        return PhaseResult(
            phase=TestPhase.UNIT,
            started_at=started,
            finished_at=finished,
            duration=finished - started,
            total_tests=len(test_results),
            passed=passed,
            failed=failed,
            success_rate=passed / len(test_results) if test_results else 0.0,
            test_results=test_results,
            coverage_percentage=coverage_pct,
            raw_output=last_result.stdout[:5000] if last_result else "",
        )

    def _parse_test_output(self, output: str, runner: str) -> list[TestResult] | None:
        """Parse test runner output into individual test results."""
        results: list[TestResult] = []

        if runner in ("pytest", "python -m pytest"):
            # Parse pytest output: test_file.py::test_name PASSED/FAILED
            pattern = r"([\w/]+\.py)::([\w\[\]]+)\s+(PASSED|FAILED|SKIPPED|ERROR)"
            for match in re.finditer(pattern, output):
                file_name, test_name, status = match.groups()
                results.append(TestResult(
                    name=f"{file_name}::{test_name}",
                    passed=status == "PASSED",
                    duration_ms=0,
                    error_message=None if status == "PASSED" else f"Test {status}",
                ))

        elif runner in ("jest", "vitest"):
            # Parse Jest/Vitest output: ✓ test name (duration)
            pass_pattern = r"✓\s+(.+?)\s*(?:\((\d+)\s*ms\))?"
            fail_pattern = r"✕\s+(.+?)\s*(?:\((\d+)\s*ms\))?"

            for match in re.finditer(pass_pattern, output):
                name = match.group(1).strip()
                duration = int(match.group(2)) if match.group(2) else 0
                results.append(TestResult(
                    name=name,
                    passed=True,
                    duration_ms=duration,
                ))

            for match in re.finditer(fail_pattern, output):
                name = match.group(1).strip()
                duration = int(match.group(2)) if match.group(2) else 0
                results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    error_message="Test failed",
                ))

        elif runner == "go test":
            # Parse Go test output: --- PASS: TestName (0.00s)
            pattern = r"---\s+(PASS|FAIL):\s+(\w+)\s+\(([0-9.]+)s\)"
            for match in re.finditer(pattern, output):
                status, name, duration = match.groups()
                results.append(TestResult(
                    name=name,
                    passed=status == "PASS",
                    duration_ms=float(duration) * 1000,
                ))

        return results if results else None

    def _parse_coverage(self, output: str) -> float | None:
        """Extract coverage percentage from output."""
        # pytest-cov format: TOTAL ... 85%
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return float(match.group(1))

        # coverage.py format: Coverage: 85.5%
        match = re.search(r"[Cc]overage[:\s]+(\d+(?:\.\d+)?)\s*%", output)
        if match:
            return float(match.group(1))

        # Jest format: All files | 85.5 |
        match = re.search(r"All files\s*\|\s*(\d+(?:\.\d+)?)", output)
        if match:
            return float(match.group(1))

        # Go format: coverage: 85.5% of statements
        match = re.search(r"coverage:\s*(\d+(?:\.\d+)?)\s*%", output)
        if match:
            return float(match.group(1))

        return None
