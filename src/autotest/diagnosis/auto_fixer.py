"""Auto-fixer: applies suggested fixes directly to source files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from autotest.models.diagnosis import Finding

logger = logging.getLogger(__name__)


@dataclass
class FixResult:
    finding_id: str
    file_path: str
    applied: bool
    message: str


@dataclass
class AutoFixReport:
    applied: list[FixResult] = field(default_factory=list)
    skipped: list[FixResult] = field(default_factory=list)
    failed: list[FixResult] = field(default_factory=list)

    @property
    def applied_count(self) -> int:
        return len(self.applied)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)


def apply_fixes(
    findings: list[Finding],
    project_root: Path,
    dry_run: bool = False,
) -> AutoFixReport:
    """Apply suggested fixes from findings to source files.

    Only applies fixes that have both code_before and code_after.
    Skips findings without a fix or without file_path.

    Args:
        findings: List of findings with suggested fixes.
        project_root: Root path of the project.
        dry_run: If True, report what would change without modifying files.

    Returns:
        AutoFixReport with results.
    """
    report = AutoFixReport()

    for finding in findings:
        fix = finding.suggested_fix
        if not fix or not fix.code_before or not fix.code_after:
            report.skipped.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=False,
                message="Sin fix aplicable (falta code_before o code_after)",
            ))
            continue

        if not finding.file_path:
            report.skipped.append(FixResult(
                finding_id=finding.id,
                file_path="",
                applied=False,
                message="Sin ruta de archivo",
            ))
            continue

        file_path = project_root / finding.file_path
        if not file_path.exists():
            report.failed.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=False,
                message=f"Archivo no encontrado: {finding.file_path}",
            ))
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (PermissionError, OSError) as e:
            report.failed.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=False,
                message=f"Error leyendo archivo: {e}",
            ))
            continue

        # Check if code_before exists in the file
        if fix.code_before not in content:
            # Try stripped version (whitespace differences)
            stripped_before = fix.code_before.strip()
            found = False
            for line in content.splitlines():
                if stripped_before in line.strip():
                    found = True
                    break
            if not found:
                report.skipped.append(FixResult(
                    finding_id=finding.id,
                    file_path=finding.file_path,
                    applied=False,
                    message="code_before no encontrado en archivo (posible cambio previo)",
                ))
                continue

        if dry_run:
            report.applied.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=True,
                message=f"[dry-run] Se aplicaria fix: {fix.description}",
            ))
            continue

        # Apply the fix
        new_content = content.replace(fix.code_before, fix.code_after, 1)
        if new_content == content:
            report.skipped.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=False,
                message="Reemplazo no produjo cambios",
            ))
            continue

        try:
            file_path.write_text(new_content, encoding="utf-8")
            report.applied.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=True,
                message=f"Fix aplicado: {fix.description}",
            ))
            logger.info("Applied fix %s to %s", finding.id, finding.file_path)
        except (PermissionError, OSError) as e:
            report.failed.append(FixResult(
                finding_id=finding.id,
                file_path=finding.file_path,
                applied=False,
                message=f"Error escribiendo archivo: {e}",
            ))

    return report
