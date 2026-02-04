"""Diagnosis engine - orchestrates static analysis, security scanning, and AI review."""

from __future__ import annotations

import logging
from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport
from autotest.models.diagnosis import DiagnosisReport, Finding, Severity
from autotest.models.project import ProjectInfo
from autotest.diagnosis.static_findings import generate_static_findings
from autotest.diagnosis.security_scanner import scan_for_secrets
from autotest.diagnosis.ai_reviewer import AICodeReviewer, prioritize_functions

logger = logging.getLogger(__name__)


class DiagnosisEngine:
    """Orchestrates all diagnosis phases: static, security, and AI review."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def diagnose(
        self,
        project: ProjectInfo,
        analysis: AnalysisReport,
    ) -> DiagnosisReport:
        """Run full diagnosis pipeline.

        1. Static findings (always, free, fast)
        2. Security scan (always, no subprocess)
        3. AI review (only if ai_enabled and api_key exists)
        """
        all_findings: list[Finding] = []
        ai_tokens = 0
        functions_analyzed = 0

        # 1. Static findings from analysis data
        static = generate_static_findings(analysis)
        all_findings.extend(static)
        logger.info("Static analysis: %d findings", len(static))

        # 2. Security scan
        security = scan_for_secrets(project.root_path)
        all_findings.extend(security)
        logger.info("Security scan: %d findings", len(security))

        # 3. AI review (optional)
        if self.config.ai_enabled and self.config.ai_api_key:
            try:
                reviewer = AICodeReviewer(self.config)
                prioritized = prioritize_functions(analysis)
                functions_analyzed = min(
                    len(prioritized), self.config.ai_max_functions
                )
                ai_findings, ai_tokens = await reviewer.review_functions(
                    prioritized, analysis.modules
                )
                all_findings.extend(ai_findings)
                logger.info(
                    "AI review: %d findings from %d functions (%d tokens)",
                    len(ai_findings),
                    functions_analyzed,
                    ai_tokens,
                )
            except Exception as e:
                logger.warning("AI review failed, continuing with static findings: %s", e)

        # Normalize file paths to relative
        self._relativize_paths(all_findings, project.root_path)

        # Deduplicate overlapping findings (e.g. static + AI on same location)
        all_findings = self._deduplicate(all_findings)

        # Sort: severity (critical first), then file+line
        severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
        all_findings.sort(
            key=lambda f: (
                severity_order.get(f.severity, 2),
                f.file_path,
                f.line_start,
            )
        )

        # Assign sequential IDs
        for i, finding in enumerate(all_findings, start=1):
            finding.id = f"CD-{i:03d}"

        # Count by severity
        critical_count = sum(1 for f in all_findings if f.severity == Severity.CRITICAL)
        warning_count = sum(1 for f in all_findings if f.severity == Severity.WARNING)
        info_count = sum(1 for f in all_findings if f.severity == Severity.INFO)

        # Calculate health score
        health_score = self._calculate_health_score(
            critical_count, warning_count, info_count, analysis
        )

        # Determine health label
        health_label = self._health_label(health_score)

        # Generate summary
        summary = self._generate_summary(
            all_findings, critical_count, warning_count, info_count, health_score
        )

        return DiagnosisReport(
            findings=all_findings,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            health_score=round(health_score, 1),
            health_label=health_label,
            summary=summary,
            ai_tokens_used=ai_tokens,
            functions_analyzed=functions_analyzed,
        )

    def _calculate_health_score(
        self,
        critical: int,
        warning: int,
        info: int,
        analysis: AnalysisReport,
    ) -> float:
        """Calculate health score (0-100) based on findings.

        Start: 100
        CRITICAL: -10 each, capped at -40
        WARNING: -3 each, capped at -30
        INFO: -1 each, capped at -10
        Coverage gap penalty: (1 - estimated_coverage/100) * 15
        """
        score = 100.0
        score -= min(critical * 10, 40)
        score -= min(warning * 3, 30)
        score -= min(info * 1, 10)

        # Coverage gap penalty
        if analysis.estimated_coverage < 100:
            coverage_penalty = (1 - analysis.estimated_coverage / 100) * 15
            score -= coverage_penalty

        return max(0.0, min(100.0, score))

    def _health_label(self, score: float) -> str:
        if score >= 80:
            return "healthy"
        elif score >= 60:
            return "moderate"
        elif score >= 40:
            return "at-risk"
        else:
            return "critical"

    def _generate_summary(
        self,
        findings: list[Finding],
        critical: int,
        warning: int,
        info: int,
        score: float,
    ) -> str:
        """Generate a human-readable summary."""
        parts: list[str] = []

        if critical > 0:
            parts.append(f"{critical} problema{'s' if critical > 1 else ''} critico{'s' if critical > 1 else ''}")
        if warning > 0:
            parts.append(f"{warning} advertencia{'s' if warning > 1 else ''}")
        if info > 0:
            parts.append(f"{info} nota{'s' if info > 1 else ''}")

        if not parts:
            return "No se encontraron problemas. Codigo saludable."

        summary = ", ".join(parts) + "."

        # Add top critical finding detail
        criticals = [f for f in findings if f.severity == Severity.CRITICAL]
        if criticals:
            top = criticals[0]
            if top.file_path and top.line_start:
                summary += (
                    f" Prioridad: {top.title} en "
                    f"{top.file_path}:{top.line_start}."
                )

        return summary

    @staticmethod
    def _deduplicate(findings: list[Finding]) -> list[Finding]:
        """Remove duplicate findings that refer to the same issue.

        Two findings are duplicates if they share the same file_path,
        similar line range (within 3 lines), and same category.
        Keeps the finding with highest confidence (prefers AI source over static).
        """
        if not findings:
            return findings

        kept: list[Finding] = []
        seen: list[Finding] = []

        for f in findings:
            is_dup = False
            for i, existing in enumerate(seen):
                if (
                    f.file_path
                    and f.file_path == existing.file_path
                    and f.category == existing.category
                    and abs(f.line_start - existing.line_start) <= 3
                ):
                    # Duplicate found — keep the one with higher confidence
                    # Prefer AI findings (more detailed) over static
                    if f.confidence > existing.confidence or (
                        f.source == "ai" and existing.source != "ai"
                    ):
                        idx = kept.index(existing)
                        kept[idx] = f
                        seen[i] = f
                    is_dup = True
                    break
            if not is_dup:
                kept.append(f)
                seen.append(f)

        return kept

    @staticmethod
    def _relativize_paths(findings: list[Finding], root: Path) -> None:
        """Convert absolute file paths to relative paths."""
        root_str = str(root)
        for finding in findings:
            if finding.file_path and finding.file_path.startswith(root_str):
                try:
                    finding.file_path = str(
                        Path(finding.file_path).relative_to(root)
                    )
                except ValueError:
                    pass
