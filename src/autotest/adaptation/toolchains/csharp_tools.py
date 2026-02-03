"""C# toolchain adapter."""

from __future__ import annotations

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class CSharpAdapter(BaseAdapter):

    def __init__(self, existing_tools: list[str] | None = None) -> None:
        self.existing_tools = existing_tools or []

    def get_toolchain(self) -> ToolChainConfig:
        return ToolChainConfig(
            language=Language.CSHARP,
            test_runner="dotnet test",
            test_command=["dotnet", "test", "--verbosity", "normal"],
            coverage_tool="coverlet",
            coverage_command=["dotnet", "test", "--collect:\"XPlat Code Coverage\""],
            mock_library="Moq",
            security_tool="dotnet list vulnerable",
            security_command=["dotnet", "list", "package", "--vulnerable", "--format", "json"],
            quality_tools=["dotnet format"],
            quality_commands=[
                ["dotnet", "format", "--verify-no-changes"],
            ],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        match phase:
            case TestPhase.SMOKE:
                return ["dotnet", "build"]
            case TestPhase.UNIT:
                return ["dotnet", "test", "--verbosity", "normal"]
            case TestPhase.INTEGRATION:
                return ["dotnet", "test", "--filter", "Category=Integration"]
            case TestPhase.SECURITY:
                return ["dotnet", "list", "package", "--vulnerable"]
            case TestPhase.QUALITY:
                return ["dotnet", "format", "--verify-no-changes"]
        return ["dotnet", "test"]

    def get_coverage_command(self) -> list[str]:
        return ["dotnet", "test", "--collect:\"XPlat Code Coverage\""]

    def get_lint_commands(self) -> list[list[str]]:
        return [["dotnet", "format", "--verify-no-changes"]]
