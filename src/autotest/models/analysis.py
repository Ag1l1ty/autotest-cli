"""Models for code analysis results."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from autotest.models.project import Language


class FunctionMetrics(BaseModel):
    name: str
    qualified_name: str
    file_path: Path
    line_start: int
    line_end: int
    language: Language
    source_code: str = ""
    cyclomatic_complexity: int = 1
    parameters_count: int = 0
    is_public: bool = True
    is_tested: bool = False
    is_dead_code: bool = False
    docstring: str | None = None


class ModuleMetrics(BaseModel):
    file_path: Path
    language: Language
    loc: int = 0
    functions: list[FunctionMetrics] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)
    imported_by: list[str] = Field(default_factory=list)
    average_complexity: float = 0.0
    max_complexity: int = 0


class CouplingInfo(BaseModel):
    module_path: Path
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    instability: float = 0.0


class AnalysisReport(BaseModel):
    modules: list[ModuleMetrics] = Field(default_factory=list)
    untested_functions: list[FunctionMetrics] = Field(default_factory=list)
    high_complexity_functions: list[FunctionMetrics] = Field(default_factory=list)
    dead_code_functions: list[FunctionMetrics] = Field(default_factory=list)
    coupling_data: list[CouplingInfo] = Field(default_factory=list)
    coupling_issues: list[CouplingInfo] = Field(default_factory=list)
    total_functions: int = 0
    tested_function_count: int = 0
    estimated_coverage: float = 0.0
    avg_complexity: float = 0.0
    total_loc: int = 0
