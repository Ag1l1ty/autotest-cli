"""Go toolchain adapter."""

from __future__ import annotations

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class GoAdapter(BaseAdapter):

    def __init__(self, existing_tools: list[str] | None = None) -> None:
        self.existing_tools = existing_tools or []

    def get_toolchain(self) -> ToolChainConfig:
        return ToolChainConfig(
            language=Language.GO,
            test_runner="go test",
            test_command=["go", "test", "./...", "-v"],
            coverage_tool="go cover",
            coverage_command=["go", "test", "./...", "-coverprofile=coverage.out"],
            mock_library="testify" if "testify" in self.existing_tools else "gomock",
            security_tool="govulncheck",
            security_command=["govulncheck", "./..."],
            quality_tools=["golangci-lint", "go vet"],
            quality_commands=[
                ["go", "vet", "./..."],
                ["golangci-lint", "run"],
            ],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        match phase:
            case TestPhase.SMOKE:
                return ["go", "build", "./..."]
            case TestPhase.UNIT:
                return ["go", "test", "./...", "-v", "-short"]
            case TestPhase.INTEGRATION:
                return ["go", "test", "./...", "-v", "-run", "Integration"]
            case TestPhase.SECURITY:
                return ["govulncheck", "./..."]
            case TestPhase.QUALITY:
                return ["go", "vet", "./..."]
        return ["go", "test", "./..."]

    def get_coverage_command(self) -> list[str]:
        return ["go", "test", "./...", "-coverprofile=coverage.out"]

    def get_lint_commands(self) -> list[list[str]]:
        return [
            ["go", "vet", "./..."],
            ["golangci-lint", "run"],
        ]
