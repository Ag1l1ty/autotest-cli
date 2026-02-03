"""Tests for the adaptation engine and AI validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.adaptation.ai.validator import validate_generated_test
from autotest.adaptation.toolchains.python_tools import PythonAdapter
from autotest.models.adaptation import GeneratedTest, ToolChainConfig
from autotest.models.project import Language


class TestPythonAdapter:

    def test_get_toolchain(self) -> None:
        adapter = PythonAdapter(existing_tools=["pytest", "coverage"])
        toolchain = adapter.get_toolchain()
        assert toolchain.language == Language.PYTHON
        assert toolchain.test_runner == "pytest"
        assert len(toolchain.test_command) > 0


class TestValidator:

    def test_valid_python(self) -> None:
        test = GeneratedTest(
            target_function="add",
            file_path=Path("test_add.py"),
            source_code="def test_add():\n    assert 1 + 1 == 2\n",
            language=Language.PYTHON,
            framework="pytest",
        )
        result = validate_generated_test(test)
        assert result is True
        assert test.is_valid is True

    def test_invalid_python_syntax(self) -> None:
        test = GeneratedTest(
            target_function="bad",
            file_path=Path("test_bad.py"),
            source_code="def test_bad(\n    not valid python",
            language=Language.PYTHON,
            framework="pytest",
        )
        result = validate_generated_test(test)
        assert result is False

    def test_dangerous_pattern_rejected(self) -> None:
        test = GeneratedTest(
            target_function="evil",
            file_path=Path("test_evil.py"),
            source_code="import os\nos.remove('/etc/passwd')\n",
            language=Language.PYTHON,
            framework="pytest",
        )
        result = validate_generated_test(test)
        assert result is False

    def test_exec_rejected(self) -> None:
        test = GeneratedTest(
            target_function="exec_test",
            file_path=Path("test_exec.py"),
            source_code='exec("print(1)")\n',
            language=Language.PYTHON,
            framework="pytest",
        )
        result = validate_generated_test(test)
        assert result is False

    def test_valid_javascript(self) -> None:
        test = GeneratedTest(
            target_function="add",
            file_path=Path("add.test.js"),
            source_code="describe('add', () => { it('adds', () => { expect(1+1).toBe(2); }); });",
            language=Language.JAVASCRIPT,
            framework="jest",
        )
        result = validate_generated_test(test)
        assert result is True

    def test_valid_java(self) -> None:
        test = GeneratedTest(
            target_function="add",
            file_path=Path("AddTest.java"),
            source_code='import org.junit.jupiter.api.Test;\npublic class AddTest { @Test void testAdd() { } }',
            language=Language.JAVA,
            framework="JUnit 5",
        )
        result = validate_generated_test(test)
        assert result is True
