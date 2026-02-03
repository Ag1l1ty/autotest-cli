"""JavaScript/TypeScript toolchain adapter."""

from __future__ import annotations

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class JavaScriptAdapter(BaseAdapter):

    def __init__(self, existing_tools: list[str] | None = None, is_typescript: bool = False) -> None:
        self.existing_tools = existing_tools or []
        self.is_typescript = is_typescript
        self.runner = "vitest" if "vitest" in self.existing_tools else "jest"

    def get_toolchain(self) -> ToolChainConfig:
        lang = Language.TYPESCRIPT if self.is_typescript else Language.JAVASCRIPT
        if self.runner == "vitest":
            test_cmd = ["npx", "vitest", "run"]
            cov_cmd = ["npx", "vitest", "run", "--coverage"]
        else:
            test_cmd = ["npx", "jest"]
            cov_cmd = ["npx", "jest", "--coverage"]

        return ToolChainConfig(
            language=lang,
            test_runner=self.runner,
            test_command=test_cmd,
            coverage_tool="c8" if self.runner == "vitest" else "istanbul",
            coverage_command=cov_cmd,
            mock_library=f"{self.runner} mocks",
            security_tool="npm audit",
            security_command=["npm", "audit", "--json"],
            quality_tools=["eslint"] + (["tsc"] if self.is_typescript else []),
            quality_commands=[
                ["npx", "eslint", "."],
            ] + ([["npx", "tsc", "--noEmit"]] if self.is_typescript else []),
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        base = ["npx", self.runner]
        match phase:
            case TestPhase.SMOKE:
                return base + ["--listTests"] if self.runner == "jest" else base + ["--list"]
            case TestPhase.UNIT:
                return base + ["run"] if self.runner == "vitest" else base
            case TestPhase.INTEGRATION:
                return base + ["run", "--testPathPattern=integration"] if self.runner == "vitest" else base + ["--testPathPattern=integration"]
            case TestPhase.SECURITY:
                return ["npm", "audit", "--json"]
            case TestPhase.QUALITY:
                return ["npx", "eslint", "."]
        return base

    def get_coverage_command(self) -> list[str]:
        if self.runner == "vitest":
            return ["npx", "vitest", "run", "--coverage"]
        return ["npx", "jest", "--coverage"]

    def get_lint_commands(self) -> list[list[str]]:
        cmds = [["npx", "eslint", "."]]
        if self.is_typescript:
            cmds.append(["npx", "tsc", "--noEmit"])
        return cmds
