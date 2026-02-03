"""Rust toolchain adapter."""

from __future__ import annotations

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class RustAdapter(BaseAdapter):

    def __init__(self, existing_tools: list[str] | None = None) -> None:
        self.existing_tools = existing_tools or []

    def get_toolchain(self) -> ToolChainConfig:
        return ToolChainConfig(
            language=Language.RUST,
            test_runner="cargo test",
            test_command=["cargo", "test"],
            coverage_tool="tarpaulin",
            coverage_command=["cargo", "tarpaulin", "--out", "json"],
            mock_library="mockall",
            security_tool="cargo audit",
            security_command=["cargo", "audit", "--json"],
            quality_tools=["clippy", "rustfmt"],
            quality_commands=[
                ["cargo", "clippy", "--", "-D", "warnings"],
                ["cargo", "fmt", "--", "--check"],
            ],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        match phase:
            case TestPhase.SMOKE:
                return ["cargo", "check"]
            case TestPhase.UNIT:
                return ["cargo", "test"]
            case TestPhase.INTEGRATION:
                return ["cargo", "test", "--test", "*"]
            case TestPhase.SECURITY:
                return ["cargo", "audit", "--json"]
            case TestPhase.QUALITY:
                return ["cargo", "clippy", "--", "-D", "warnings"]
        return ["cargo", "test"]

    def get_coverage_command(self) -> list[str]:
        return ["cargo", "tarpaulin", "--out", "json"]

    def get_lint_commands(self) -> list[list[str]]:
        return [
            ["cargo", "clippy", "--", "-D", "warnings"],
            ["cargo", "fmt", "--", "--check"],
        ]
