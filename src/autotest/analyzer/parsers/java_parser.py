"""Java regex-based code parser."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


class JavaParser:
    """Parse Java files using regex patterns."""

    METHOD_PATTERN = re.compile(
        r"(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?"
        r"(?:synchronized\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*"
        r"(?:throws\s+[\w,\s]+)?\s*\{",
        re.MULTILINE,
    )

    IMPORT_PATTERN = re.compile(r"import\s+([\w.]+);", re.MULTILINE)

    def parse_functions(self, file_path: Path) -> list[FunctionMetrics]:
        source = safe_read(file_path)
        if not source:
            return []

        functions: list[FunctionMetrics] = []
        lines = source.splitlines()

        for match in self.METHOD_PATTERN.finditer(source):
            name = match.group(1)
            if name in {"if", "for", "while", "switch", "catch", "class"}:
                continue

            params = match.group(2)
            param_count = len([p for p in params.split(",") if p.strip()]) if params.strip() else 0
            line_start = source[:match.start()].count("\n") + 1
            line_end = min(line_start + 30, len(lines))

            prefix = source[max(0, match.start() - 50):match.start()]
            is_public = "public" in prefix or "protected" in prefix

            functions.append(FunctionMetrics(
                name=name,
                qualified_name=name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                language=Language.JAVA,
                source_code="\n".join(lines[line_start - 1:line_end]),
                parameters_count=param_count,
                is_public=is_public,
            ))

        return functions

    def parse_imports(self, file_path: Path) -> list[str]:
        source = safe_read(file_path)
        if not source:
            return []
        return [m.group(1) for m in self.IMPORT_PATTERN.finditer(source)]
