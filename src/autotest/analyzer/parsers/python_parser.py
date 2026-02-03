"""Python AST-based code parser."""

from __future__ import annotations

import ast
from pathlib import Path

from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.utils.file_utils import safe_read


class PythonParser:
    """Parse Python files using the built-in ast module."""

    def parse_functions(self, file_path: Path) -> list[FunctionMetrics]:
        """Extract all functions and methods from a Python file."""
        source = safe_read(file_path)
        if not source:
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        functions: list[FunctionMetrics] = []
        lines = source.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Determine qualified name
                qualified = self._get_qualified_name(tree, node)

                # Extract source code for this function
                start = node.lineno - 1
                end = node.end_lineno or node.lineno
                func_source = chr(10).join(lines[start:end])

                # Get docstring
                docstring = ast.get_docstring(node)

                # Check if public
                is_public = not node.name.startswith("_")

                functions.append(FunctionMetrics(
                    name=node.name,
                    qualified_name=qualified,
                    file_path=file_path,
                    line_start=node.lineno,
                    line_end=end,
                    language=Language.PYTHON,
                    source_code=func_source,
                    parameters_count=len(node.args.args),
                    is_public=is_public,
                    docstring=docstring,
                ))

        return functions

    def parse_imports(self, file_path: Path) -> list[str]:
        """Extract all imports from a Python file."""
        source = safe_read(file_path)
        if not source:
            return []

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return imports

    def _get_qualified_name(self, tree: ast.Module, target: ast.AST) -> str:
        """Get the fully qualified name of a function (module.Class.method)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in ast.walk(node):
                    if item is target:
                        return f"{node.name}.{target.name}"
        return target.name
