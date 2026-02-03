"""Cyclomatic complexity analyzer."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language


def calculate_complexity(func: FunctionMetrics) -> int:
    """Calculate cyclomatic complexity for a function."""
    if func.language == Language.PYTHON:
        return _python_complexity(func)
    return _generic_complexity(func)


def _python_complexity(func: FunctionMetrics) -> int:
    """Calculate complexity using radon for Python functions."""
    try:
        from radon.complexity import cc_visit
        blocks = cc_visit(func.source_code)
        if blocks:
            return blocks[0].complexity
    except Exception:
        pass
    return _generic_complexity(func)


def _generic_complexity(func: FunctionMetrics) -> int:
    """Calculate complexity using branch-keyword counting (all languages)."""
    source = func.source_code
    complexity = 1  # Base complexity

    # Common branching keywords across languages
    branch_patterns = [
        r"\bif\b",
        r"\belif\b",
        r"\belse\s+if\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\bcase\b",
        r"\bcatch\b",
        r"\bexcept\b",
        r"\b&&\b",
        r"\b\|\|\b",
        r"\band\b",
        r"\bor\b",
        r"\?\s*[^:]+\s*:",  # ternary operator
    ]

    for pattern in branch_patterns:
        complexity += len(re.findall(pattern, source))

    return complexity
