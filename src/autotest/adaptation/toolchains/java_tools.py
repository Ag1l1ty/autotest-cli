"""Java toolchain adapter."""

from __future__ import annotations

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class JavaAdapter(BaseAdapter):

    def __init__(self, build_tool: str = "maven", existing_tools: list[str] | None = None) -> None:
        self.build_tool = build_tool
        self.existing_tools = existing_tools or []

    def get_toolchain(self) -> ToolChainConfig:
        if self.build_tool == "gradle":
            test_cmd = ["./gradlew", "test"]
            cov_cmd = ["./gradlew", "test", "jacocoTestReport"]
        else:
            test_cmd = ["mvn", "test"]
            cov_cmd = ["mvn", "test", "jacoco:report"]

        return ToolChainConfig(
            language=Language.JAVA,
            test_runner="JUnit 5",
            test_command=test_cmd,
            coverage_tool="JaCoCo",
            coverage_command=cov_cmd,
            mock_library="Mockito",
            security_tool="OWASP dependency-check",
            security_command=["mvn", "org.owasp:dependency-check-maven:check"] if self.build_tool == "maven" else ["./gradlew", "dependencyCheckAnalyze"],
            quality_tools=["checkstyle", "spotbugs"],
            quality_commands=[
                (["mvn", "checkstyle:check"] if self.build_tool == "maven" else ["./gradlew", "checkstyleMain"]),
            ],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        if self.build_tool == "gradle":
            base = ["./gradlew"]
        else:
            base = ["mvn"]

        match phase:
            case TestPhase.SMOKE:
                return base + ["compile"] if self.build_tool == "maven" else base + ["compileJava"]
            case TestPhase.UNIT:
                return base + ["test"]
            case TestPhase.INTEGRATION:
                return base + ["verify"] if self.build_tool == "maven" else base + ["integrationTest"]
            case TestPhase.SECURITY:
                return base + ["org.owasp:dependency-check-maven:check"] if self.build_tool == "maven" else base + ["dependencyCheckAnalyze"]
            case TestPhase.QUALITY:
                return base + ["checkstyle:check"] if self.build_tool == "maven" else base + ["checkstyleMain"]
        return base + ["test"]

    def get_coverage_command(self) -> list[str]:
        if self.build_tool == "gradle":
            return ["./gradlew", "test", "jacocoTestReport"]
        return ["mvn", "test", "jacoco:report"]

    def get_lint_commands(self) -> list[list[str]]:
        if self.build_tool == "gradle":
            return [["./gradlew", "checkstyleMain"]]
        return [["mvn", "checkstyle:check"]]
