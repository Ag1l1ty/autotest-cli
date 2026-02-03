"""Models for test execution results."""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from autotest.models.project import TestPhase


class TestResult(BaseModel):
    name: str
    passed: bool
    duration_ms: float = 0.0
    error_message: str | None = None
    stdout: str = ""
    stderr: str = ""
    is_generated: bool = False


class PhaseResult(BaseModel):
    phase: TestPhase
    started_at: datetime
    finished_at: datetime
    duration: timedelta = timedelta()
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    success_rate: float = 0.0
    test_results: list[TestResult] = Field(default_factory=list)
    coverage_percentage: float | None = None
    raw_output: str = ""


class ExecutionReport(BaseModel):
    phases: list[PhaseResult] = Field(default_factory=list)
    total_duration: timedelta = timedelta()
    overall_pass_rate: float = 0.0
    overall_coverage: float | None = None
