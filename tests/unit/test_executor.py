"""Tests for the executor module."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from autotest.executor.runners.subprocess_runner import run_command, SubprocessResult
from autotest.executor.sandbox import TestSandbox as SandboxManager
from autotest.models.adaptation import GeneratedTest
from autotest.models.project import Language


class TestSubprocessRunner:

    def test_command_not_found(self) -> None:
        result = asyncio.run(
            run_command(["nonexistent_command_xyz"])
        )
        assert result.return_code == 127
        assert "not found" in result.stderr.lower()

    def test_successful_command(self) -> None:
        result = asyncio.run(
            run_command(["echo", "hello"])
        )
        assert result.return_code == 0
        assert "hello" in result.stdout

    def test_timeout(self) -> None:
        result = asyncio.run(
            run_command(["sleep", "10"], timeout=1)
        )
        assert result.timed_out is True


class TestSandbox:

    def test_sandbox_creates_temp_dir(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("content")

        async def run():
            async with SandboxManager(tmp_path) as sandbox:
                assert sandbox.path.exists()
                assert (sandbox.path / "file.txt").exists()
                sandbox_path = sandbox.path
            # After exit, temp dir should be cleaned up
            assert not sandbox_path.exists()

        asyncio.run(run())

    def test_sandbox_writes_generated_tests(self, tmp_path: Path) -> None:
        tests = [
            GeneratedTest(
                target_function="add",
                file_path=tmp_path / "tests" / "test_add.py",
                source_code="def test_add(): assert True",
                language=Language.PYTHON,
                framework="pytest",
                is_valid=True,
            ),
        ]

        async def run():
            async with SandboxManager(tmp_path) as sandbox:
                written = sandbox.write_generated_tests(tests)
                assert len(written) == 1
                assert written[0].exists()

        asyncio.run(run())
