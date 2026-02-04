"""Constants and mappings for AutoTest CLI."""

from __future__ import annotations

from autotest.models.project import Language

# File extensions to language mapping
EXTENSION_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".cs": Language.CSHARP,
}

# Directories to skip during scanning
SKIP_DIRS: set[str] = {
    "__pycache__",
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".venv",
    "venv",
    "env",
    ".env",
    ".tox",
    ".nox",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    "target",
    "bin",
    "obj",
    ".idea",
    ".vscode",
    ".autotest_cache",
    "vendor",
    "third_party",
}

# Build/config files per language
BUILD_FILES: dict[Language, list[str]] = {
    Language.PYTHON: [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
    ],
    Language.JAVASCRIPT: [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
    ],
    Language.TYPESCRIPT: [
        "tsconfig.json",
        "package.json",
    ],
    Language.JAVA: [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
    ],
    Language.GO: [
        "go.mod",
        "go.sum",
    ],
    Language.RUST: [
        "Cargo.toml",
        "Cargo.lock",
    ],
    Language.CSHARP: [
        "*.csproj",
        "*.sln",
        "Directory.Build.props",
    ],
}

# Test file patterns per language
TEST_PATTERNS: dict[Language, list[str]] = {
    Language.PYTHON: ["test_*.py", "*_test.py", "tests/**/*.py", "test/**/*.py"],
    Language.JAVASCRIPT: [
        "*.test.js",
        "*.spec.js",
        "*.test.ts",
        "*.spec.ts",
        "*.test.jsx",
        "*.spec.jsx",
        "*.test.tsx",
        "*.spec.tsx",
        "__tests__/**/*",
    ],
    Language.TYPESCRIPT: [
        "*.test.ts",
        "*.spec.ts",
        "*.test.tsx",
        "*.spec.tsx",
        "__tests__/**/*",
    ],
    Language.JAVA: ["*Test.java", "*Tests.java", "*Spec.java", "Test*.java"],
    Language.GO: ["*_test.go"],
    Language.RUST: [],  # Rust tests are inline, detected differently
    Language.CSHARP: ["*Test.cs", "*Tests.cs", "*.Tests/**/*.cs"],
}

# Complexity thresholds
COMPLEXITY_LOW = 5
COMPLEXITY_MEDIUM = 10
COMPLEXITY_HIGH = 20
COMPLEXITY_VERY_HIGH = 50

# Default output formats
DEFAULT_OUTPUT_FORMATS = ["terminal"]

# AI model
DEFAULT_AI_MODEL = "claude-sonnet-4-20250514"

# Diagnosis defaults
DEFAULT_AI_MAX_FUNCTIONS = 10
DEFAULT_MIN_FINDING_CONFIDENCE = 0.6
DEFAULT_SEVERITY_FILTER = ["critical", "warning"]
DEFAULT_TOP_FINDINGS = 5
