"""AI-powered test generator using Claude API."""

from __future__ import annotations

import asyncio
from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.adaptation import GeneratedTest
from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.adaptation.ai.prompts import get_test_generation_prompt
from autotest.adaptation.ai.validator import validate_generated_test
from autotest.constants import MAX_CONCURRENT_AI_REQUESTS

TEST_FILE_PATTERNS = {
    Language.PYTHON: "test_{name}.py",
    Language.JAVASCRIPT: "{name}.test.js",
    Language.TYPESCRIPT: "{name}.test.ts",
    Language.JAVA: "{name}Test.java",
    Language.GO: "{name}_test.go",
    Language.RUST: "{name}_test.rs",
    Language.CSHARP: "{name}Tests.cs",
}

DEFAULT_FRAMEWORKS = {
    Language.PYTHON: "pytest",
    Language.JAVASCRIPT: "jest",
    Language.TYPESCRIPT: "jest",
    Language.JAVA: "JUnit 5",
    Language.GO: "testing",
    Language.RUST: "built-in",
    Language.CSHARP: "xUnit",
}


class AITestGenerator:
    """Generates tests using Claude API for untested functions."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

    async def generate_tests(
        self,
        functions: list[FunctionMetrics],
        framework_overrides: dict[Language, str] | None = None,
    ) -> list[GeneratedTest]:
        if not self.config.ai_api_key:
            return []

        frameworks = {**DEFAULT_FRAMEWORKS, **(framework_overrides or {})}
        functions_to_process = functions[:self.config.ai_max_functions]

        tasks = [
            self._generate_single(func, frameworks.get(func.language, ""))
            for func in functions_to_process
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        generated: list[GeneratedTest] = []
        for result in results:
            if isinstance(result, GeneratedTest):
                generated.append(result)

        return generated

    async def _generate_single(
        self,
        func: FunctionMetrics,
        framework: str,
    ) -> GeneratedTest | None:
        async with self.semaphore:
            try:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=self.config.ai_api_key)

                prompt = get_test_generation_prompt(
                    function_source=func.source_code,
                    function_name=func.name,
                    language=func.language,
                    framework=framework,
                )

                message = await client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = message.content[0].text
                test_code = self._extract_code(response_text)

                pattern = TEST_FILE_PATTERNS.get(func.language, "test_{name}.txt")
                test_dir = func.file_path.parent / "tests"
                file_name = pattern.format(name=func.name)
                test_path = test_dir / file_name

                test = GeneratedTest(
                    target_function=func.qualified_name,
                    file_path=test_path,
                    source_code=test_code,
                    language=func.language,
                    framework=framework,
                    confidence=0.8,
                )

                validate_generated_test(test)
                return test

            except Exception:
                return None

    def _extract_code(self, response: str) -> str:
        if "```" in response:
            blocks = response.split("```")
            for i, block in enumerate(blocks):
                if i % 2 == 1:
                    lines = block.splitlines()
                    if lines and not lines[0].strip().startswith(
                        ("import", "from", "package", "use", "using", "def", "fn", "func", "public", "#")
                    ):
                        lines = lines[1:]
                    return "\n".join(lines).strip()
        return response.strip()
