"""File utilities for safe reading and scanning."""

from __future__ import annotations

from pathlib import Path

from autotest.constants import SKIP_DIRS


def should_skip_dir(dir_name: str) -> bool:
    """Check if a directory should be skipped during scanning."""
    return dir_name in SKIP_DIRS or dir_name.startswith(".")


def count_lines(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        content = safe_read(file_path)
        return len([line for line in content.splitlines() if line.strip()])
    except Exception:
        return 0


def safe_read(file_path: Path, encoding: str = "utf-8") -> str:
    """Safely read a file, handling encoding errors."""
    try:
        return file_path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        try:
            return file_path.read_text(encoding="latin-1")
        except Exception:
            return ""
    except Exception:
        return ""


def collect_files(root: Path, extensions: set[str] | None = None) -> list[Path]:
    """Collect all files under root, respecting skip directories."""
    files: list[Path] = []
    if not root.is_dir():
        return files

    for item in root.iterdir():
        if item.is_dir():
            if not should_skip_dir(item.name):
                files.extend(collect_files(item, extensions))
        elif item.is_file():
            if extensions is None or item.suffix in extensions:
                files.append(item)
    return files


def find_files_by_pattern(root: Path, patterns: list[str]) -> list[Path]:
    """Find files matching glob patterns under root."""
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.rglob(pattern))
    return list(set(found))
