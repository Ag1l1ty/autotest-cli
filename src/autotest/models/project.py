"""Models for project detection results."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"


class TestPhase(str, Enum):
    SMOKE = "smoke"
    UNIT = "unit"
    INTEGRATION = "integration"
    SECURITY = "security"
    QUALITY = "quality"


class FrameworkInfo(BaseModel):
    name: str
    version: str | None = None
    config_file: Path | None = None


class LanguageInfo(BaseModel):
    language: Language
    version: str | None = None
    files: list[Path] = Field(default_factory=list)
    total_loc: int = 0
    percentage: float = 0.0
    frameworks: list[FrameworkInfo] = Field(default_factory=list)
    existing_test_tools: list[str] = Field(default_factory=list)
    existing_test_files: list[Path] = Field(default_factory=list)
    build_tool: str | None = None


class ProjectInfo(BaseModel):
    root_path: Path
    name: str
    languages: list[LanguageInfo] = Field(default_factory=list)
    primary_language: Language | None = None
    has_git: bool = False
    git_branch: str | None = None
    total_files: int = 0
    total_loc: int = 0
    config_files_found: list[Path] = Field(default_factory=list)
