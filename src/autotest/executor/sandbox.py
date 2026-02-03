"""Test sandbox - manages temporary directory for test execution."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Self

from autotest.models.adaptation import GeneratedTest


class TestSandbox:
    """Context manager that creates a temporary copy for safe test execution."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._temp_dir: Path | None = None

    async def __aenter__(self) -> Self:
        self._temp_dir = Path(tempfile.mkdtemp(prefix="autotest_"))
        # Copy project to temp dir (respecting common ignore patterns)
        self._copy_project()
        return self

    async def __aexit__(self, *args) -> None:
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    @property
    def path(self) -> Path:
        if self._temp_dir is None:
            raise RuntimeError("Sandbox not initialized. Use 'async with' context.")
        return self._temp_dir

    def write_generated_tests(self, tests: list[GeneratedTest]) -> list[Path]:
        """Write generated test files into the sandbox."""
        written: list[Path] = []
        for test in tests:
            if not test.is_valid:
                continue

            # Create the test file path relative to sandbox
            relative = test.file_path
            if relative.is_absolute():
                try:
                    relative = relative.relative_to(self.project_root)
                except ValueError:
                    relative = Path("generated_tests") / test.file_path.name

            target = self.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(test.source_code, encoding="utf-8")
            written.append(target)

        return written

    def _copy_project(self) -> None:
        """Copy project files to sandbox, skipping large/irrelevant dirs."""
        skip_dirs = {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            "dist", "build", ".eggs", "target", ".tox", ".nox",
        }

        for item in self.project_root.iterdir():
            if item.name in skip_dirs:
                continue
            dest = self.path / item.name
            try:
                if item.is_dir():
                    shutil.copytree(
                        item, dest,
                        ignore=shutil.ignore_patterns(*skip_dirs),
                        dirs_exist_ok=True,
                    )
                else:
                    shutil.copy2(item, dest)
            except (PermissionError, OSError):
                continue
