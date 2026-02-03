"""Adaptation engine - orchestrates tool selection and test generation."""

from __future__ import annotations

from autotest.config import AutoTestConfig
from autotest.models.adaptation import TestStrategy
from autotest.models.analysis import AnalysisReport
from autotest.models.project import Language, ProjectInfo, TestPhase
from autotest.adaptation.toolchains.python_tools import PythonAdapter
from autotest.adaptation.toolchains.javascript_tools import JavaScriptAdapter
from autotest.adaptation.toolchains.java_tools import JavaAdapter
from autotest.adaptation.toolchains.go_tools import GoAdapter
from autotest.adaptation.toolchains.rust_tools import RustAdapter
from autotest.adaptation.toolchains.csharp_tools import CSharpAdapter
from autotest.adaptation.ai.generator import AITestGenerator
from autotest.adaptation.ai.integration_generator import AIIntegrationTestGenerator

ADAPTER_MAP = {
    Language.PYTHON: lambda tools, bt: PythonAdapter(tools),
    Language.JAVASCRIPT: lambda tools, bt: JavaScriptAdapter(tools, is_typescript=False),
    Language.TYPESCRIPT: lambda tools, bt: JavaScriptAdapter(tools, is_typescript=True),
    Language.JAVA: lambda tools, bt: JavaAdapter(build_tool=bt or "maven", existing_tools=tools),
    Language.GO: lambda tools, bt: GoAdapter(tools),
    Language.RUST: lambda tools, bt: RustAdapter(tools),
    Language.CSHARP: lambda tools, bt: CSharpAdapter(tools),
}


class AdaptationEngine:
    """Selects appropriate tools and optionally generates tests."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def adapt(
        self,
        project: ProjectInfo,
        analysis: AnalysisReport,
    ) -> TestStrategy:
        toolchains = []
        phases_to_run = [TestPhase(p) for p in self.config.phases]

        for lang_info in project.languages:
            adapter_factory = ADAPTER_MAP.get(lang_info.language)
            if adapter_factory:
                adapter = adapter_factory(
                    lang_info.existing_test_tools,
                    lang_info.build_tool,
                )
                toolchains.append(adapter.get_toolchain())

        generated_tests = []
        integration_tests = []
        generation_stats = {
            "attempted": 0,
            "valid": 0,
            "failed": 0,
            "integration_attempted": 0,
            "integration_valid": 0,
        }

        if self.config.ai_enabled and analysis.untested_functions:
            # 1. Generate unit tests
            unit_generator = AITestGenerator(self.config)

            sorted_functions = sorted(
                analysis.untested_functions,
                key=lambda f: f.cyclomatic_complexity,
                reverse=True,
            )

            generation_stats["attempted"] = min(
                len(sorted_functions),
                self.config.ai_max_functions,
            )

            generated_tests = await unit_generator.generate_tests(sorted_functions)
            generation_stats["valid"] = sum(1 for t in generated_tests if t.is_valid)
            generation_stats["failed"] = generation_stats["attempted"] - generation_stats["valid"]

            # 2. Generate integration tests (for functions with external services)
            if TestPhase.INTEGRATION in phases_to_run:
                integration_generator = AIIntegrationTestGenerator(self.config)

                # Use all functions (not just untested) for integration tests
                all_functions = []
                for module in analysis.modules:
                    all_functions.extend(module.functions)

                integration_tests = await integration_generator.generate_integration_tests(
                    all_functions
                )

                generation_stats["integration_attempted"] = len(all_functions)
                generation_stats["integration_valid"] = sum(
                    1 for t in integration_tests if t.is_valid
                )

        # Combine all generated tests
        all_generated = generated_tests + integration_tests

        return TestStrategy(
            toolchains=toolchains,
            generated_tests=all_generated,
            phases_to_run=phases_to_run,
            ai_generation_used=bool(all_generated),
            generation_stats=generation_stats,
        )
