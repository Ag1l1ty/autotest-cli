"""Tests for the code analyzer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.analyzer.complexity import calculate_complexity
from autotest.analyzer.parsers.python_parser import PythonParser
from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language


class TestPythonParser:

    def test_parse_functions(self, tmp_path: Path) -> None:
        source = '''
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y

class Calculator:
    def divide(self, a, b):
        return a / b
'''
        f = tmp_path / "sample.py"
        f.write_text(source)
        parser = PythonParser()
        functions = parser.parse_functions(f)
        names = [fn.name for fn in functions]
        assert "add" in names
        assert "multiply" in names
        assert "divide" in names

    def test_parse_imports(self, tmp_path: Path) -> None:
        source = '''
import os
from pathlib import Path
from typing import Optional
'''
        f = tmp_path / "imports.py"
        f.write_text(source)
        parser = PythonParser()
        imports = parser.parse_imports(f)
        assert "os" in imports
        assert "pathlib" in imports


class TestComplexity:

    def test_simple_function(self) -> None:
        func = FunctionMetrics(
            name="add",
            qualified_name="add",
            file_path=Path("test.py"),
            line_start=1,
            line_end=2,
            language=Language.PYTHON,
            source_code="def add(a, b):\n    return a + b\n",
        )
        score = calculate_complexity(func)
        assert score >= 1

    def test_complex_function(self) -> None:
        source = '''def complex_func(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    yield i
        elif x > 5:
            return x * 2
        else:
            return x
    else:
        return 0
'''
        func = FunctionMetrics(
            name="complex_func",
            qualified_name="complex_func",
            file_path=Path("test.py"),
            line_start=1,
            line_end=13,
            language=Language.PYTHON,
            source_code=source,
        )
        score = calculate_complexity(func)
        assert score > 1
