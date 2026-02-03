"""JavaScript/TypeScript regex-based code parser."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


class JSParser:
    """Parse JavaScript/TypeScript files using regex patterns."""

    # Patterns for function detection
    FUNCTION_PATTERNS = [
        # function name(params) {
        re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE),
        # const name = (params) => {
        re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>", re.MULTILINE),
        # class methods: name(params) {
        re.compile(r"^\s+(?:async\s+)?(\w+)\s*\(([^)]*)\)\s*\{", re.MULTILINE),
    ]

    IMPORT_PATTERN = re.compile(
        r"(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"]\s*\))",
        re.MULTILINE,
    )

    def parse_functions(self, file_path: Path) -> list[FunctionMetrics]:
        source = safe_read(file_path)
        if not source:
            return []

        is_ts = file_path.suffix in {".ts", ".tsx"}
        language = Language.TYPESCRIPT if is_ts else Language.JAVASCRIPT
        functions: list[FunctionMetrics] = []
        lines = source.splitlines()
        seen_names: set[str] = set()

        for pattern in self.FUNCTION_PATTERNS:
            for match in pattern.finditer(source):
                name = match.group(1)
                if name in seen_names or name in {"if", "for", "while", "switch", "catch"}:
                    continue
                seen_names.add(name)

                params = match.group(2) if match.lastindex and match.lastindex >= 2 else ""
                param_count = len([p for p in params.split(",") if p.strip()]) if params.strip() else 0
                
                line_start = source[:match.start()].count("\n") + 1
                # Estimate end by finding matching brace
                line_end = min(line_start + 20, len(lines))

                functions.append(FunctionMetrics(
                    name=name,
                    qualified_name=name,
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    language=language,
                    source_code="\n".join(lines[line_start - 1:line_end]),
                    parameters_count=param_count,
                    is_public=not name.startswith("_"),
                ))

        return functions

    def parse_imports(self, file_path: Path) -> list[str]:
        source = safe_read(file_path)
        if not source:
            return []

        imports: list[str] = []
        for match in self.IMPORT_PATTERN.finditer(source):
            imp = match.group(1) or match.group(2)
            if imp:
                imports.append(imp)
        return imports
