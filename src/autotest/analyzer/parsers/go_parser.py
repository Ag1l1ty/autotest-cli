"""Go regex-based code parser."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


class GoParser:
    """Parse Go files using regex patterns."""

    FUNC_PATTERN = re.compile(
        r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )

    IMPORT_PATTERN = re.compile(r'"([\w./\-]+)"', re.MULTILINE)

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

            is_public = name[0].isupper() if name else False

            functions.append(FunctionMetrics(
                name=name,
                qualified_name=name,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                language=Language.GO,
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
