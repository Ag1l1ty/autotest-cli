"""Coverage gap finder - identifies functions without tests."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import LanguageInfo
from autotest.utils.file_utils import safe_read


def find_untested_functions(
    functions: list[FunctionMetrics],
    language_info: LanguageInfo,
) -> list[FunctionMetrics]:
    """Cross-reference functions with test files to find untested ones."""
    if not language_info.existing_test_files:
        # No test files at all - all public functions are untested
        for func in functions:
            if func.is_public:
                func.is_tested = False
        return [f for f in functions if f.is_public]

    # Collect all test content
    test_content = ""
    for test_file in language_info.existing_test_files:
        test_content += safe_read(test_file).lower() + "\n"

    untested: list[FunctionMetrics] = []
    for func in functions:
        if not func.is_public:
            continue

        # Check if function name appears in test content
        name_lower = func.name.lower()
        patterns = [
            f"test_{name_lower}",
            f"test{name_lower}",
            f"{name_lower}_test",
            f"{name_lower}test",
            f"should_{name_lower}",
            f"it.*{name_lower}",
            f"describe.*{name_lower}",
        ]

        is_tested = any(p in test_content for p in patterns)
        
        # Also check for direct references
        if not is_tested:
            is_tested = bool(re.search(
                rf"\b{re.escape(name_lower)}\b.*(?:assert|expect|mock|spy|stub)",
                test_content,
            ))

        func.is_tested = is_tested
        if not is_tested:
            untested.append(func)

    return untested
