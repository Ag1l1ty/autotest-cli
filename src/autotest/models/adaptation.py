"""Models for the adaptation engine."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from autotest.models.project import Language, TestPhase


class ToolChainConfig(BaseModel):
    language: Language
    test_runner: str
    test_command: list[str] = Field(default_factory=list)
    coverage_tool: str = ""
    coverage_command: list[str] = Field(default_factory=list)
    mock_library: str = ""
    security_tool: str | None = None
    security_command: list[str] = Field(default_factory=list)
    quality_tools: list[str] = Field(default_factory=list)
    quality_commands: list[list[str]] = Field(default_factory=list)
    env_vars: dict[str, str] = Field(default_factory=dict)


class GeneratedTest(BaseModel):
    target_function: str
    file_path: Path
    source_code: str
    language: Language
    framework: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    requires_mocks: list[str] = Field(default_factory=list)
    is_valid: bool = False


class TestStrategy(BaseModel):
    toolchains: list[ToolChainConfig] = Field(default_factory=list)
    generated_tests: list[GeneratedTest] = Field(default_factory=list)
    phases_to_run: list[TestPhase] = Field(default_factory=list)
    ai_generation_used: bool = False
    generation_stats: dict[str, int] = Field(default_factory=dict)
