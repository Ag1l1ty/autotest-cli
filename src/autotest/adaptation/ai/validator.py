"""Validator for AI-generated tests."""

from __future__ import annotations

import ast

from autotest.models.adaptation import GeneratedTest
from autotest.models.project import Language

DANGEROUS_PATTERNS = [
    "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir",
    "subprocess.call", "subprocess.run", "exec(", "eval(",
    "__import__", "open(",
]


def validate_generated_test(test: GeneratedTest) -> bool:
    """Validate a generated test for syntax and safety."""
    source_lower = test.source_code.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in source_lower:
            test.is_valid = False
            return False

    validators = {
        Language.PYTHON: _validate_python,
        Language.JAVASCRIPT: _validate_javascript,
        Language.TYPESCRIPT: _validate_javascript,
        Language.JAVA: _validate_java,
        Language.GO: _validate_go,
        Language.RUST: _validate_rust,
        Language.CSHARP: _validate_csharp,
    }

    validator = validators.get(test.language, _validate_generic)
    test.is_valid = validator(test.source_code)
    return test.is_valid


def _validate_python(source: str) -> bool:
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False


def _validate_javascript(source: str) -> bool:
    if source.count("{") != source.count("}"):
        return False
    if source.count("(") != source.count(")"):
        return False
    return any(kw in source for kw in ["describe", "it(", "test(", "expect"])


def _validate_java(source: str) -> bool:
    if source.count("{") != source.count("}"):
        return False
    return "@Test" in source or "@ParameterizedTest" in source


def _validate_go(source: str) -> bool:
    if source.count("{") != source.count("}"):
        return False
    return "func Test" in source and "testing.T" in source


def _validate_rust(source: str) -> bool:
    if source.count("{") != source.count("}"):
        return False
    return "#[test]" in source or "#[cfg(test)]" in source


def _validate_csharp(source: str) -> bool:
    if source.count("{") != source.count("}"):
        return False
    return "[Fact]" in source or "[Theory]" in source or "[Test]" in source


def _validate_generic(source: str) -> bool:
    return source.count("{") == source.count("}")
