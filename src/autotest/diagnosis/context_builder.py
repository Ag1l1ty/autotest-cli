"""Build rich context for AI code review from analysis data."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from autotest.models.analysis import FunctionMetrics, ModuleMetrics


@dataclass
class ModuleContext:
    """Rich context about a function's surrounding module."""

    imports: list[str] = field(default_factory=list)
    parent_class_source: str = ""
    sibling_functions: list[str] = field(default_factory=list)
    module_docstring: str = ""


def build_function_context(
    func: FunctionMetrics,
    modules: list[ModuleMetrics],
) -> ModuleContext:
    """Extract rich context for a function from the module data.

    If the function is a method (has "." in qualified_name), attempts to
    extract the parent class source from the file.
    """
    ctx = ModuleContext()

    # Find the module this function belongs to
    module = _find_module(func.file_path, modules)
    if module is None:
        return ctx

    ctx.imports = list(module.imports)

    # Collect sibling function signatures
    for sibling in module.functions:
        if sibling.qualified_name != func.qualified_name:
            sig = sibling.name
            if sibling.docstring:
                sig += f"  # {sibling.docstring[:60]}"
            ctx.sibling_functions.append(sig)

    # If function is a method, try to extract parent class
    if "." in func.qualified_name:
        class_name = func.qualified_name.rsplit(".", 1)[0]
        # The class_name might be like "ClassName.method", we want "ClassName"
        if "." in class_name:
            class_name = class_name.split(".")[-1]
        else:
            class_name = class_name

        ctx.parent_class_source = _extract_class_source(
            func.file_path, class_name
        )

    # Try to extract module docstring
    ctx.module_docstring = _extract_module_docstring(func.file_path)

    return ctx


def _find_module(
    file_path: Path, modules: list[ModuleMetrics]
) -> ModuleMetrics | None:
    """Find the ModuleMetrics for a given file path."""
    for module in modules:
        if module.file_path == file_path:
            return module
    return None


def _extract_class_source(file_path: Path, class_name: str) -> str:
    """Extract the full source of a class from a file."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except (PermissionError, OSError):
        return ""

    lines = source.splitlines()
    class_start = -1
    class_indent = 0

    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(f"class {class_name}"):
            class_start = i
            class_indent = len(line) - len(stripped)
            break

    if class_start == -1:
        return ""

    # Collect lines until we hit a line at the same or lower indentation
    class_lines = [lines[class_start]]
    for i in range(class_start + 1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            class_lines.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= class_indent and line.strip():
            break
        class_lines.append(line)

    # Limit to 200 lines to avoid sending huge classes
    if len(class_lines) > 200:
        class_lines = class_lines[:200]
        class_lines.append("    # ... (truncated)")

    return "\n".join(class_lines)


def _extract_module_docstring(file_path: Path) -> str:
    """Extract the module-level docstring from a Python file."""
    try:
        source = file_path.read_text(encoding="utf-8", errors="ignore")
    except (PermissionError, OSError):
        return ""

    lines = source.splitlines()
    if not lines:
        return ""

    # Check for module docstring (first non-comment, non-empty line)
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # Find the end of the docstring
            quote = stripped[:3]
            if stripped.count(quote) >= 2:
                return stripped.strip(quote).strip()
            # Multi-line docstring
            doc_lines = [stripped.lstrip(quote)]
            for next_line in lines[lines.index(line) + 1:]:
                if quote in next_line:
                    doc_lines.append(next_line.split(quote)[0])
                    break
                doc_lines.append(next_line)
            return "\n".join(doc_lines).strip()
        break  # Not a docstring

    return ""
