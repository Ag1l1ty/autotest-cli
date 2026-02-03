"""Rust regex-based code parser."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


class RustParser:
    """Parse Rust files using regex patterns."""

    FUNC_PATTERN = re.compile(
        r"(?:pub(?:\(crate\))?\s+)?(?:async\s+)?fn\s+(\w+)\s*(?:<[^>]+>)?\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    USE_PATTERN = re.compile(r"use\s+([\w:]+)", re.MULTILINE)

    def parse_functions(self, file_path: Path) -> list[FunctionMetrics]:
        source = safe_read(file_path)
        if not source:
            return []

        functions: list[FunctionMetrics] = []
        lines = source.splitlines()

        for match in self.FUNC_PATTERN.finditer(source):
            name = match.group(1)
            params = match.group(2)
            param_count = len([p for p in params.split(",") if p.strip()]) if params.strip() else 0
            line_start = source[:match.start()].count("\n") + 1
            line_end = min(line_start + 25, len(lines))

            # Check if pub
            prefix = source[max(0, match.start() - 20):match.start()]
            is_public = "pub" in prefix

            functions.append(FunctionMetrics(
                name=name,
                qualified_name=name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                language=Language.RUST,
                source_code="\n".join(lines[line_start - 1:line_end]),
                parameters_count=param_count,
                is_public=is_public,
            ))

        return functions

    def parse_imports(self, file_path: Path) -> list[str]:
        source = safe_read(file_path)
        if not source:
            return []
        return [m.group(1) for m in self.USE_PATTERN.finditer(source)]
