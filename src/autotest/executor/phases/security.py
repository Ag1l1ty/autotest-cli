"""Phase 4: Security Tests - Check for vulnerabilities and exposed secrets."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import run_command
from autotest.models.adaptation import TestStrategy, ToolChainConfig
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import Language, TestPhase

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9]{16,}", "API key"),
    (r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}", "Hardcoded secret"),
    (r"(?i)(aws_access_key_id)\s*[:=]\s*['\"]?AKIA[A-Z0-9]{16}", "AWS access key"),
    (r"(?i)(private[_-]?key)\s*[:=]\s*['\"]-----BEGIN", "Private key"),
    (r"(?i)(token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}", "Token"),
    (r"jdbc:[a-z]+://[^:]+:[^@]+@", "Database connection string"),
]

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build"}


class SecurityPhaseExecutor(BasePhaseExecutor):

    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.SECURITY

    async def execute(self, strategy: TestStrategy, project_root: Path) -> PhaseResult:
        started = datetime.now()
        test_results: list[TestResult] = []

        # 1. Run language-specific security scanners
        for toolchain in strategy.toolchains:
            scanner_results = await self._run_security_scanner(toolchain, project_root)
            test_results.extend(scanner_results)

        # 2. Scan for hardcoded secrets
        secrets_result = self._scan_for_secrets(project_root)
        test_results.append(secrets_result)

        # 3. Check for vulnerable dependency patterns
        for toolchain in strategy.toolchains:
            dep_result = await self._check_dependency_vulnerabilities(toolchain, project_root)
            if dep_result:
                test_results.append(dep_result)

        finished = datetime.now()
        passed = sum(1 for t in test_results if t.passed)

        return PhaseResult(
            phase=TestPhase.SECURITY,
            started_at=started,
            finished_at=finished,
            duration=finished - started,
            total_tests=len(test_results),
            passed=passed,
            failed=len(test_results) - passed,
            success_rate=passed / len(test_results) if test_results else 0.0,
            test_results=test_results,
        )

    async def _run_security_scanner(
        self,
        toolchain: ToolChainConfig,
        project_root: Path,
    ) -> list[TestResult]:
        results: list[TestResult] = []

        if toolchain.security_command:
            result = await run_command(
                toolchain.security_command, cwd=project_root, timeout=120,
            )
            results.append(TestResult(
                name=f"security:{toolchain.language.value}:scanner",
                passed=result.return_code == 0,
                duration_ms=result.duration_ms,
                error_message=result.stderr[:2000] if result.return_code != 0 else None,
                stdout=result.stdout[:3000],
                stderr=result.stderr[:2000],
            ))

        return results

    def _scan_for_secrets(self, project_root: Path) -> TestResult:
        """Scan source files for hardcoded secrets."""
        findings: list[str] = []
        files_scanned = 0

        for path in project_root.rglob("*"):
            if not path.is_file():
                continue
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue
            if path.suffix not in {
                ".py", ".js", ".ts", ".java", ".go", ".rs", ".cs",
                ".yaml", ".yml", ".json", ".toml", ".env", ".cfg", ".ini",
            }:
                continue

            files_scanned += 1
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except (PermissionError, OSError):
                continue

            for pattern, label in SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    relative = path.relative_to(project_root)
                    findings.append(f"{label} found in {relative}")

        passed = len(findings) == 0
        return TestResult(
            name="security:secrets-scan",
            passed=passed,
            error_message="\n".join(findings[:20]) if findings else None,
            stdout=f"Scanned {files_scanned} files, found {len(findings)} potential secrets",
        )

    async def _check_dependency_vulnerabilities(
        self,
        toolchain: ToolChainConfig,
        project_root: Path,
    ) -> TestResult | None:
        audit_cmds = {
            Language.PYTHON: ["pip", "audit"],
            Language.JAVASCRIPT: ["npm", "audit", "--json"],
            Language.GO: ["govulncheck", "./..."],
            Language.RUST: ["cargo", "audit"],
            Language.CSHARP: ["dotnet", "list", "package", "--vulnerable"],
        }

        cmd = audit_cmds.get(toolchain.language)
        if not cmd:
            return None

        result = await run_command(cmd, cwd=project_root, timeout=120)
        return TestResult(
            name=f"security:{toolchain.language.value}:dependency-audit",
            passed=result.return_code == 0,
            duration_ms=result.duration_ms,
            error_message=result.stderr[:2000] if result.return_code != 0 else None,
            stdout=result.stdout[:3000],
            stderr=result.stderr[:2000],
        )
