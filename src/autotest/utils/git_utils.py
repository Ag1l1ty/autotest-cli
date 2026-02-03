"""Git utilities for project info extraction."""

from __future__ import annotations

import subprocess
from pathlib import Path


def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repository."""
    return (path / ".git").is_dir()


def get_current_branch(path: Path) -> str | None:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_changed_files(path: Path, base_branch: str = "main") -> list[Path]:
    """Get files changed relative to a base branch."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return [path / f for f in result.stdout.strip().splitlines() if f]
    except Exception:
        pass
    return []
