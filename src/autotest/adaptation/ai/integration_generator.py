"""AI-powered integration test generator with automatic mock detection."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.adaptation import GeneratedTest
from autotest.models.analysis import FunctionMetrics
from autotest.models.project import Language
from autotest.constants import MAX_CONCURRENT_AI_REQUESTS

# Patrones para detectar servicios externos
EXTERNAL_SERVICE_PATTERNS = {
    "airtable": [r"airtable", r"pyairtable", r"Airtable\("],
    "supabase": [r"supabase", r"create_client", r"supabase\."],
    "firebase": [r"firebase", r"firestore", r"firebase_admin"],
    "aws_s3": [r"boto3", r"s3\.client", r"s3\.resource"],
    "aws_dynamodb": [r"dynamodb", r"boto3.*dynamodb"],
    "mongodb": [r"pymongo", r"MongoClient", r"mongodb"],
    "postgresql": [r"psycopg2", r"asyncpg", r"postgresql"],
    "mysql": [r"mysql\.connector", r"pymysql", r"MySQLdb"],
    "redis": [r"redis\.Redis", r"aioredis", r"redis\.from_url"],
    "http_requests": [r"requests\.(get|post|put|delete)", r"httpx\.", r"aiohttp\."],
    "onedrive": [r"onedrive", r"microsoft.*graph", r"msgraph"],
    "google_sheets": [r"gspread", r"google.*sheets", r"googleapiclient"],
    "slack": [r"slack_sdk", r"SlackClient", r"WebClient"],
    "twilio": [r"twilio", r"Client.*twilio"],
    "stripe": [r"stripe\.", r"stripe\.api"],
    "sendgrid": [r"sendgrid", r"SendGridAPIClient"],
    "openai": [r"openai\.", r"OpenAI\("],
    "anthropic": [r"anthropic\.", r"Anthropic\("],
}

# Mock templates por servicio
MOCK_TEMPLATES = {
    "airtable": '''
@pytest.fixture
def mock_airtable(mocker):
    """Mock Airtable API responses."""
    mock = mocker.patch("{module}.Airtable")
    mock_instance = mock.return_value
    mock_instance.get_all.return_value = [{"id": "rec123", "fields": {"Name": "Test"}}]
    mock_instance.insert.return_value = {"id": "rec456", "fields": {"Name": "New"}}
    mock_instance.update.return_value = {"id": "rec123", "fields": {"Name": "Updated"}}
    mock_instance.delete.return_value = {"deleted": True, "id": "rec123"}
    return mock_instance
''',
    "supabase": '''
@pytest.fixture
def mock_supabase(mocker):
    """Mock Supabase client."""
    mock = mocker.patch("{module}.create_client")
    mock_client = mocker.MagicMock()
    mock.return_value = mock_client
    mock_client.table.return_value.select.return_value.execute.return_value.data = [{"id": 1, "name": "test"}]
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": 2, "name": "new"}]
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": 1, "name": "updated"}]
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = []
    return mock_client
''',
    "http_requests": '''
@pytest.fixture
def mock_requests(mocker):
    """Mock HTTP requests."""
    mock = mocker.patch("{module}.requests")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "data": []}
    mock_response.text = "OK"
    mock.get.return_value = mock_response
    mock.post.return_value = mock_response
    mock.put.return_value = mock_response
    mock.delete.return_value = mock_response
    return mock
''',
    "onedrive": '''
@pytest.fixture
def mock_onedrive(mocker):
    """Mock OneDrive/Microsoft Graph API."""
    mock = mocker.patch("{module}.requests")
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "value": [{"id": "file1", "name": "test.txt", "size": 1024}]
    }
    mock.get.return_value = mock_response
    mock.post.return_value = mock_response
    return mock
''',
    "openai": '''
@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI API."""
    mock = mocker.patch("{module}.OpenAI")
    mock_client = mock.return_value
    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock(message=mocker.MagicMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client
''',
    "anthropic": '''
@pytest.fixture
def mock_anthropic(mocker):
    """Mock Anthropic API."""
    mock = mocker.patch("{module}.Anthropic")
    mock_client = mock.return_value
    mock_response = mocker.MagicMock()
    mock_response.content = [mocker.MagicMock(text="Test response")]
    mock_client.messages.create.return_value = mock_response
    return mock_client
''',
}


def detect_external_services(source_code: str) -> list[str]:
    """Detect which external services are used in the code."""
    services = []
    source_lower = source_code.lower()

    for service, patterns in EXTERNAL_SERVICE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, source_code, re.IGNORECASE):
                services.append(service)
                break

    return list(set(services))


def get_integration_prompt(
    function_source: str,
    function_name: str,
    module_name: str,
    services: list[str],
    language: Language,
    file_path: str = "",
) -> str:
    """Generate prompt for integration test with mocks."""

    services_str = ", ".join(services) if services else "external APIs"

    return f"""Generate integration tests with mocks for the following Python function.

## Function to test:
```python
{function_source}
```

## Module name: {module_name}
## File location: {file_path}

## External services detected: {services_str}

## CRITICAL - Path Setup:
The test file will be in `tests/integration/` directory. You MUST add this at the very top of the file:
```python
import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
```

## Requirements:
1. Use pytest and pytest-mock
2. Create fixture(s) that mock the external service calls
3. Test the function's integration behavior (how it interacts with external services)
4. Include tests for:
   - Successful API responses
   - Error handling (API failures, timeouts, invalid responses)
   - Edge cases (empty responses, malformed data)
5. Use `mocker.patch()` to mock external calls
6. Mark tests with `@pytest.mark.integration`
7. Import the module using: `from {module_name} import {function_name}` (after the sys.path setup)

## Important:
- Mock at the right level (usually the requests/client library)
- Don't make real API calls
- Test the function's logic for handling different API responses
- Include docstrings explaining what each test verifies
- The sys.path setup MUST be at the very top, before any other imports

## Output format:
Return ONLY valid Python test code with:
- sys.path setup at the very top (REQUIRED)
- Required imports (pytest, unittest.mock, etc.)
- Import of the function being tested
- Mock fixtures
- Test functions marked with @pytest.mark.integration
- No explanations, just code
"""


class AIIntegrationTestGenerator:
    """Generates integration tests with mocks using Claude API."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_AI_REQUESTS)

    async def generate_integration_tests(
        self,
        functions: list[FunctionMetrics],
    ) -> list[GeneratedTest]:
        """Generate integration tests for functions that use external services."""
        if not self.config.ai_api_key:
            return []

        # Filter functions that have external service calls
        functions_with_services = []
        for func in functions:
            services = detect_external_services(func.source_code)
            if services:
                functions_with_services.append((func, services))

        if not functions_with_services:
            return []

        # Limit to max functions
        functions_to_process = functions_with_services[:self.config.ai_max_functions]

        tasks = [
            self._generate_single(func, services)
            for func, services in functions_to_process
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
        services: list[str],
    ) -> GeneratedTest | None:
        async with self.semaphore:
            try:
                import anthropic

                client = anthropic.AsyncAnthropic(api_key=self.config.ai_api_key)

                # Get module name from file path
                module_name = func.file_path.stem

                prompt = get_integration_prompt(
                    function_source=func.source_code,
                    function_name=func.name,
                    module_name=module_name,
                    services=services,
                    language=func.language,
                    file_path=str(func.file_path),
                )

                message = await client.messages.create(
                    model=self.config.ai_model,
                    max_tokens=3000,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = message.content[0].text
                test_code = self._extract_code(response_text)

                # Create test file path
                test_dir = func.file_path.parent / "tests" / "integration"
                file_name = f"test_{func.name}_integration.py"
                test_path = test_dir / file_name

                test = GeneratedTest(
                    target_function=func.qualified_name,
                    file_path=test_path,
                    source_code=test_code,
                    language=func.language,
                    framework="pytest",
                    confidence=0.75,
                    requires_mocks=services,
                )

                # Validate
                self._validate_integration_test(test)
                return test

            except Exception:
                return None

    def _extract_code(self, response: str) -> str:
        """Extract code from markdown response."""
        code = ""
        if "```" in response:
            blocks = response.split("```")
            for i, block in enumerate(blocks):
                if i % 2 == 1:
                    lines = block.splitlines()
                    if lines and lines[0].strip().lower() in ("python", "py", ""):
                        lines = lines[1:]
                    code = "\n".join(lines).strip()
                    break
        else:
            code = response.strip()

        # Ensure sys.path setup is present
        code = self._ensure_path_setup(code)
        return code

    def _ensure_path_setup(self, code: str) -> str:
        """Ensure the test code has proper sys.path setup for imports."""
        path_setup = '''import sys
import os
# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
'''
        # Check if sys.path setup already exists
        if "sys.path.insert" in code or "sys.path.append" in code:
            return code

        # Find where to insert (after any initial comments/docstrings)
        lines = code.split("\n")
        insert_idx = 0

        # Skip initial comments and docstrings
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_idx = i
                break
            elif stripped:
                insert_idx = i
                break

        # Insert path setup before first import
        lines.insert(insert_idx, path_setup)
        return "\n".join(lines)

    def _validate_integration_test(self, test: GeneratedTest) -> bool:
        """Validate integration test syntax and requirements."""
        import ast

        try:
            ast.parse(test.source_code)
        except SyntaxError:
            test.is_valid = False
            return False

        # Check for required elements
        code_lower = test.source_code.lower()
        has_pytest_import = "import pytest" in code_lower or "from pytest" in code_lower
        has_mock = "mock" in code_lower or "mocker" in code_lower
        has_integration_mark = "pytest.mark.integration" in code_lower
        has_test_function = "def test_" in code_lower

        test.is_valid = all([
            has_pytest_import,
            has_mock,
            has_test_function,
        ])

        return test.is_valid
