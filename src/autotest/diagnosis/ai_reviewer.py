"""AI-powered code reviewer using Claude API with structured output."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from autotest.config import AutoTestConfig
from autotest.exceptions import AIReviewError
from autotest.models.analysis import AnalysisReport, FunctionMetrics, ModuleMetrics
from autotest.models.diagnosis import (
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)
from autotest.diagnosis.context_builder import build_function_context
from autotest.diagnosis.prompts import (
    REPORT_FINDINGS_TOOL,
    REVIEW_SYSTEM_PROMPT,
    build_review_prompt,
)

logger = logging.getLogger(__name__)

# Map string categories from AI to our enum
_CATEGORY_MAP = {
    "bug": FindingCategory.BUG,
    "security": FindingCategory.SECURITY,
    "error_handling": FindingCategory.ERROR_HANDLING,
    "complexity": FindingCategory.COMPLEXITY,
    "style": FindingCategory.STYLE,
}

_SEVERITY_MAP = {
    "critical": Severity.CRITICAL,
    "warning": Severity.WARNING,
    "info": Severity.INFO,
}


class AICodeReviewer:
    """Reviews code using Claude API and returns structured findings."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self._semaphore = asyncio.Semaphore(3)
        self._total_tokens = 0

    async def review_functions(
        self,
        functions: list[FunctionMetrics],
        modules: list[ModuleMetrics],
    ) -> tuple[list[Finding], int]:
        """Review a list of functions and return findings.

        Args:
            functions: Functions to review, already prioritized.
            modules: All module data for context building.

        Returns:
            Tuple of (findings, total_tokens_used).
        """
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic package not installed, skipping AI review")
            return [], 0

        if not self.config.ai_api_key:
            logger.warning("No API key configured, skipping AI review")
            return [], 0

        client = anthropic.AsyncAnthropic(api_key=self.config.ai_api_key)

        # Limit to configured max
        max_funcs = self.config.ai_max_functions
        functions_to_review = functions[:max_funcs]

        tasks = [
            self._review_single(client, func, modules)
            for func in functions_to_review
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_findings: list[Finding] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("AI review failed for a function: %s", result)
                continue
            all_findings.extend(result)

        # Filter by confidence threshold
        min_confidence = self.config.min_finding_confidence
        filtered = [f for f in all_findings if f.confidence >= min_confidence]

        return filtered, self._total_tokens

    async def _review_single(
        self,
        client: Any,
        func: FunctionMetrics,
        modules: list[ModuleMetrics],
    ) -> list[Finding]:
        """Review a single function using the Claude API."""
        async with self._semaphore:
            ctx = build_function_context(func, modules)

            prompt = build_review_prompt(
                source_code=func.source_code,
                qualified_name=func.qualified_name,
                language=func.language.value,
                docstring=func.docstring,
                imports=ctx.imports,
                parent_class_source=ctx.parent_class_source,
                sibling_functions=ctx.sibling_functions,
            )

            try:
                response = await client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=2000,
                    system=REVIEW_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                    tools=[REPORT_FINDINGS_TOOL],
                    tool_choice={"type": "tool", "name": "report_findings"},
                )

                # Track token usage
                if hasattr(response, "usage"):
                    self._total_tokens += (
                        response.usage.input_tokens + response.usage.output_tokens
                    )

                return self._parse_response(response, func)

            except Exception as e:
                raise AIReviewError(
                    f"AI review failed for {func.qualified_name}: {e}"
                ) from e

    def _parse_response(
        self,
        response: Any,
        func: FunctionMetrics,
    ) -> list[Finding]:
        """Parse Claude's tool_use response into Finding objects."""
        findings: list[Finding] = []

        for block in response.content:
            if block.type != "tool_use" or block.name != "report_findings":
                continue

            raw_findings = block.input.get("findings", [])
            for raw in raw_findings:
                severity = _SEVERITY_MAP.get(
                    raw.get("severity", "info"), Severity.INFO
                )
                category = _CATEGORY_MAP.get(
                    raw.get("category", "bug"), FindingCategory.BUG
                )

                # Calculate absolute line number
                relative_line = raw.get("line_start", 0)
                absolute_line = func.line_start + relative_line - 1 if relative_line > 0 else func.line_start

                suggested_fix = None
                if raw.get("fix_description") or raw.get("code_after"):
                    suggested_fix = SuggestedFix(
                        description=raw.get("fix_description", ""),
                        code_before=raw.get("code_before", ""),
                        code_after=raw.get("code_after", ""),
                    )

                findings.append(Finding(
                    severity=severity,
                    category=category,
                    title=raw.get("title", "Issue found"),
                    description=raw.get("description", ""),
                    file_path=str(func.file_path),
                    line_start=absolute_line,
                    line_end=func.line_end,
                    function_name=func.name,
                    qualified_name=func.qualified_name,
                    language=func.language.value,
                    suggested_fix=suggested_fix,
                    confidence=raw.get("confidence", 0.5),
                    source="ai",
                ))

        return findings


def prioritize_functions(analysis: AnalysisReport) -> list[FunctionMetrics]:
    """Prioritize functions for AI review.

    Order: high complexity + untested first, then high complexity tested,
    then untested public functions.
    """
    scored: list[tuple[float, FunctionMetrics]] = []

    all_functions: list[FunctionMetrics] = []
    for module in analysis.modules:
        all_functions.extend(module.functions)

    for func in all_functions:
        if not func.source_code or not func.source_code.strip():
            continue
        score = 0.0
        # Complexity contributes most
        score += func.cyclomatic_complexity * 2
        # Untested is a big factor
        if not func.is_tested:
            score += 15
        # Public functions matter more
        if func.is_public:
            score += 5
        # Dead code is less interesting
        if func.is_dead_code:
            score -= 20
        scored.append((score, func))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [func for _, func in scored]
