"""Prompt templates for AI test generation per language."""

from __future__ import annotations

from autotest.models.project import Language


def get_test_generation_prompt(
    function_source: str,
    function_name: str,
    language: Language,
    framework: str,
    context: str = "",
) -> str:
    """Generate a prompt for AI test generation."""
    lang_instructions = LANGUAGE_INSTRUCTIONS.get(language, GENERIC_INSTRUCTIONS)

    return f"""Generate comprehensive unit tests for the following function.

## Function to test:
```
{function_source}
```

## Requirements:
- Language: {language.value}
- Test framework: {framework}
{lang_instructions}

## Additional context:
{context if context else "No additional context provided."}

## Instructions:
1. Generate ONLY the test code, no explanations
2. Include edge cases and error conditions
3. Use descriptive test names that explain what is being tested
4. Mock external dependencies if needed
5. Include both positive and negative test cases
6. Ensure all assertions are meaningful

## Output format:
Return ONLY valid {language.value} test code that can be saved directly to a file and executed.
"""


LANGUAGE_INSTRUCTIONS = {
    Language.PYTHON: """
- Use pytest style (not unittest)
- Use pytest fixtures where appropriate
- Use pytest.raises for exception testing
- Use pytest-mock's mocker fixture for mocking
- Add type hints to test functions
""",
    Language.JAVASCRIPT: """
- Use describe/it blocks
- Use expect() for assertions
- Use jest.mock() or vi.mock() for mocking
- Test async functions with async/await
- Use beforeEach/afterEach for setup/teardown
""",
    Language.TYPESCRIPT: """
- Use describe/it blocks with proper TypeScript types
- Use expect() for assertions
- Use jest.mock() or vi.mock() for mocking
- Ensure type safety in test assertions
- Test async functions with async/await
""",
    Language.JAVA: """
- Use JUnit 5 annotations (@Test, @BeforeEach, @DisplayName)
- Use AssertJ for fluent assertions
- Use Mockito for mocking (@Mock, @InjectMocks, when/thenReturn)
- Use @ParameterizedTest for data-driven tests
- Test exception throwing with assertThrows
""",
    Language.GO: """
- Use testing.T for test functions
- Follow Go naming convention: TestFunctionName
- Use table-driven tests where appropriate
- Use testify/assert for cleaner assertions if available
- Test error returns explicitly
""",
    Language.RUST: """
- Use #[cfg(test)] module
- Use #[test] attribute for test functions
- Use assert!, assert_eq!, assert_ne! macros
- Test with should_panic for expected panics
- Use mockall for mocking traits
""",
    Language.CSHARP: """
- Use [Fact] or [Theory] attributes (xUnit style)
- Use FluentAssertions for readable assertions
- Use Moq for mocking interfaces
- Use [InlineData] for parameterized tests
- Test async methods with async Task
""",
}

GENERIC_INSTRUCTIONS = """
- Write idiomatic tests for the target language
- Cver edge cases and error conditions
- Use appropriate mocking patterns
"""
