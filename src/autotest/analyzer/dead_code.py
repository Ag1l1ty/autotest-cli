"""Dead code detector - finds potentially unused code."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


def detect_dead_code(
    functions: list[FunctionMetrics],
    all_source_files: list[Path],
) -> list[FunctionMetrics]:
    """Detect potentially dead (unused) functions."""
    # Collect all source content (excluding test files)
    all_content = ""
    for file_path in all_source_files:
        all_content += safe_read(file_path) + "\n"

    dead_functions: list[FunctionMetrics] = []

    for func in functions:
        if not func.is_public:
            continue
        # Skip common entry points and special methods
        if func.name in {"main", "__init__", "__str__", "__repr__", "setup", "teardown"}:
            continue
        if func.name.startswith("__") and func.name.endswith("__"):
            continue

        # Count references to this function (excluding its own definition)
        pattern = rf"\b{re.escape(func.name)}\b"
        matches = re.findall(pattern, all_content)
        
        # Subtract 1 for the definition itself, and 1 for each decorator/type hint usage
        reference_count = len(matches) - 1
        
        if reference_count <= 0:
            func.is_dead_code = True
            dead_functions.append(func)

    return dead_functions
