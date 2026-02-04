"""Python language detector."""

from __future__ import annotations

from pathlib import Path

from autotest.constants import TEST_PATTERNS
from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, find_files_by_pattern, safe_read


@register("python")
class PythonDetector(BaseLanguageDetector):
    """Detects Python projects and their characteristics."""

    @property
    def language_name(self) -> str:
        return "python"

    def detect(self, root: Path) -> LanguageInfo | None:
        files = collect_files(root, {".py", ".pyw"})
        if not files:
            return None

        # Find test files using centralized patterns
        test_files = find_files_by_pattern(root, TEST_PATTERNS[Language.PYTHON])

        # Determine build tool
        build_tool = self._detect_build_tool(root)
        total_loc = sum(count_lines(f) for f in files)

        return LanguageInfo(
            language=Language.PYTHON,
            version=self._detect_version(root),
            files=files,
            total_loc=total_loc,
            existing_test_files=test_files,
            build_tool=build_tool,
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        
        # Check requirements files and pyproject.toml for framework indicators
        deps = self._gather_dependencies(root)
        
        framework_map = {
            "django": "Django",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "starlette": "Starlette",
            "tornado": "Tornado",
            "aiohttp": "aiohttp",
            "pyramid": "Pyramid",
            "bottle": "Bottle",
            "sanic": "Sanic",
            "celery": "Celery",
            "sqlalchemy": "SQLAlchemy",
            "pandas": "pandas",
            "numpy": "NumPy",
            "scipy": "SciPy",
            "tensorflow": "TensorFlow",
            "torch": "PyTorch",
            "sklearn": "scikit-learn",
            "scikit-learn": "scikit-learn",
        }

        for dep_key, display_name in framework_map.items():
            if dep_key in deps:
                frameworks.append(FrameworkInfo(name=display_name))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = []
        deps = self._gather_dependencies(root)
        
        if "pytest" in deps or (root / "pytest.ini").exists() or (root / "conftest.py").exists():
            tools.append("pytest")
        if "coverage" in deps or "pytest-cov" in deps:
            tools.append("coverage")
        if "pytest-mock" in deps or "mock" in deps:
            tools.append("pytest-mock")
        if "unittest" in deps:
            tools.append("unittest")
        if "tox" in deps or (root / "tox.ini").exists():
            tools.append("tox")
        if "nox" in deps or (root / "noxfile.py").exists():
            tools.append("nox")
        if "hypothesis" in deps:
            tools.append("hypothesis")
        
        return tools

    def _detect_build_tool(self, root: Path) -> str | None:
        if (root / "pyproject.toml").exists():
            content = safe_read(root / "pyproject.toml")
            if "poetry" in content:
                return "poetry"
            if "hatchling" in content or "hatch" in content:
                return "hatch"
            if "setuptools" in content:
                return "setuptools"
            return "pyproject"
        if (root / "setup.py").exists():
            return "setuptools"
        if (root / "Pipfile").exists():
            return "pipenv"
        if (root / "requirements.txt").exists():
            return "pip"
        return None

    def _detect_version(self, root: Path) -> str | None:
        # Check .python-version
        pv = root / ".python-version"
        if pv.exists():
            return safe_read(pv).strip()
        # Check pyproject.toml requires-python
        pp = root / "pyproject.toml"
        if pp.exists():
            content = safe_read(pp)
            for line in content.splitlines():
                if "requires-python" in line:
                    return line.split("=", 1)[-1].strip().strip('"').strip("'")
        return None

    def _gather_dependencies(self, root: Path) -> set[str]:
        deps: set[str] = set()
        
        # From requirements.txt
        req = root / "requirements.txt"
        if req.exists():
            for line in safe_read(req).splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    name = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip()
                    deps.add(name.lower())

        # From pyproject.toml dependencies
        pp = root / "pyproject.toml"
        if pp.exists():
            content = safe_read(pp).lower()
            # Simple extraction from dependencies list
            in_deps = False
            for line in content.splitlines():
                if "dependencies" in line and "=" in line:
                    in_deps = True
                    continue
                if in_deps:
                    if line.strip().startswith("]"):
                        in_deps = False
                        continue
                    if '"' in line:
                        pkg = line.strip().strip('",').split(">=")[0].split("==")[0].split("<")[0].strip()
                        deps.add(pkg.lower())

        # From setup.py (basic extraction)
        sp = root / "setup.py"
        if sp.exists():
            content = safe_read(sp).lower()
            if "install_requires" in content:
                # Basic regex-free extraction
                for word in ["django", "flask", "fastapi", "pytest", "numpy", "pandas"]:
                    if word in content:
                        deps.add(word)

        return deps
