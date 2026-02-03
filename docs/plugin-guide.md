# Guia de Plugins para AutoTest CLI

## Version
v0.1.0

## Introduccion

AutoTest CLI esta disenado con una arquitectura extensible que permite agregar soporte para nuevos lenguajes, fases de ejecucion y formatos de reporte.

Esta guia cubre como extender cada modulo del sistema.

---

## 1. Crear un Detector de Lenguaje

Los detectores identifican lenguajes de programacion en un proyecto.

### Paso 1: Crear el archivo

```bash
# src/autotest/detector/languages/mi_lenguaje.py
```

### Paso 2: Implementar el detector

```python
"""Detector para Mi Lenguaje."""

from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import (
    FrameworkInfo,
    Language,
    LanguageInfo,
)
from autotest.utils.file_utils import count_lines


@register("mi_lenguaje")
class MiLenguajeDetector(BaseLanguageDetector):
    """Detecta proyectos de Mi Lenguaje."""

    # Extensiones de archivo a buscar
    EXTENSIONS = {".miext", ".mi"}

    # Archivos de configuracion que indican el lenguaje
    CONFIG_FILES = {"mi.config", "mi.json"}

    @property
    def language_name(self) -> str:
        return "mi_lenguaje"

    def detect(self, root: Path) -> LanguageInfo | None:
        """Detecta si el proyecto usa Mi Lenguaje."""
        files: list[Path] = []

        for ext in self.EXTENSIONS:
            files.extend(root.rglob(f"*{ext}"))

        # Excluir directorios comunes
        files = [
            f for f in files
            if not any(
                part in f.parts
                for part in {"node_modules", ".git", "vendor", "dist"}
            )
        ]

        if not files:
            return None

        return LanguageInfo(
            language=Language.OTHER,  # O agregar al enum
            files=files,
            total_loc=sum(count_lines(f) for f in files),
            version=self._detect_version(root),
        )

    def _detect_version(self, root: Path) -> str | None:
        """Detecta la version de Mi Lenguaje."""
        config = root / "mi.config"
        if config.exists():
            # Parsear version del config
            return "1.0"
        return None

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        """Detecta frameworks de Mi Lenguaje."""
        frameworks = []

        # Detectar MiFramework
        if (root / "miframework.json").exists():
            frameworks.append(
                FrameworkInfo(
                    name="MiFramework",
                    version=self._get_framework_version(root),
                    category="web",
                )
            )

        return frameworks

    def _get_framework_version(self, root: Path) -> str | None:
        # Leer version del framework
        return None

    def detect_test_tools(self, root: Path) -> list[str]:
        """Detecta herramientas de testing instaladas."""
        tools = []

        if (root / "mi.test.config").exists():
            tools.append("mi-test")

        return tools
```

### Paso 3: Agregar al enum (opcional)

Si es un lenguaje nuevo, agregarlo a `models/project.py`:

```python
class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    # ... otros
    MI_LENGUAJE = "mi_lenguaje"  # Nuevo
```

### Paso 4: Registrar en __init__.py

```python
# src/autotest/detector/languages/__init__.py
from autotest.detector.languages.mi_lenguaje import MiLenguajeDetector
```

---

## 2. Crear un Toolchain

Los toolchains configuran las herramientas de testing por lenguaje.

### Paso 1: Crear el archivo

```bash
# src/autotest/adaptation/toolchains/mi_lenguaje_tools.py
```

### Paso 2: Implementar el adapter

```python
"""Toolchain para Mi Lenguaje."""

from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig
from autotest.models.project import Language, TestPhase


class MiLenguajeAdapter(BaseAdapter):
    """Configura herramientas de testing para Mi Lenguaje."""

    def get_toolchain(self) -> ToolChainConfig:
        """Retorna la configuracion del toolchain."""
        return ToolChainConfig(
            language=Language.MI_LENGUAJE,
            test_runner="mi-test",
            test_command=["mi-test", "run"],
            coverage_tool="mi-cov",
            coverage_command=["mi-test", "run", "--coverage"],
            mock_library="mi-mock",
            lint_tools=["mi-lint"],
        )

    def get_test_command(self, phase: TestPhase) -> list[str]:
        """Retorna el comando de test para una fase."""
        base = ["mi-test", "run"]

        if phase == TestPhase.UNIT:
            return base + ["--unit"]
        elif phase == TestPhase.INTEGRATION:
            return base + ["--integration"]
        elif phase == TestPhase.SMOKE:
            return ["mi-test", "check"]

        return base

    def get_coverage_command(self) -> list[str]:
        """Retorna el comando para generar coverage."""
        return ["mi-test", "run", "--coverage", "--format=json"]

    def get_lint_commands(self) -> list[list[str]]:
        """Retorna comandos de linting."""
        return [
            ["mi-lint", "check", "."],
            ["mi-format", "--check", "."],
        ]

    def get_type_check_command(self) -> list[str] | None:
        """Retorna comando de type checking."""
        return ["mi-types", "check", "."]
```

### Paso 3: Registrar en engine

```python
# src/autotest/adaptation/engine.py
from autotest.adaptation.toolchains.mi_lenguaje_tools import MiLenguajeAdapter

ADAPTERS = {
    Language.PYTHON: PythonAdapter,
    Language.JAVASCRIPT: JavaScriptAdapter,
    # ...
    Language.MI_LENGUAJE: MiLenguajeAdapter,  # Nuevo
}
```

---

## 3. Crear Prompts de IA

Para que la IA genere tests en tu lenguaje:

### Paso 1: Agregar template

```python
# src/autotest/adaptation/ai/prompts.py

MI_LENGUAJE_UNIT_TEST_TEMPLATE = """
Generate a unit test for the following Mi Lenguaje function.
Use the mi-test framework with mi-mock for mocking.

Function to test:
```mi
{function_code}
```

File: {file_path}
Function name: {function_name}

Requirements:
1. Use mi-test assertions (expect, assert)
2. Mock external dependencies with mi-mock
3. Test edge cases and error conditions
4. Follow Mi Lenguaje testing conventions

Generate ONLY the test code, no explanations.
"""

LANGUAGE_TEMPLATES = {
    Language.PYTHON: PYTHON_UNIT_TEST_TEMPLATE,
    Language.JAVASCRIPT: JS_UNIT_TEST_TEMPLATE,
    # ...
    Language.MI_LENGUAJE: MI_LENGUAJE_UNIT_TEST_TEMPLATE,  # Nuevo
}
```

---

## 4. Crear una Fase de Ejecucion

### Paso 1: Crear el archivo

```bash
# src/autotest/executor/phases/mi_fase.py
```

### Paso 2: Implementar el ejecutor

```python
"""Ejecutor para Mi Fase personalizada."""

from datetime import datetime, timedelta
from pathlib import Path

from autotest.executor.base import BasePhaseExecutor
from autotest.executor.runners.subprocess_runner import SubprocessRunner
from autotest.models.adaptation import TestStrategy
from autotest.models.execution import PhaseResult, TestResult
from autotest.models.project import TestPhase


class MiFaseExecutor(BasePhaseExecutor):
    """Ejecuta Mi Fase personalizada."""

    @property
    def phase_name(self) -> TestPhase:
        # Agregar al enum si es nueva fase
        return TestPhase.CUSTOM

    async def execute(
        self,
        strategy: TestStrategy,
        project_root: Path,
    ) -> PhaseResult:
        """Ejecuta la fase."""
        start = datetime.now()
        results: list[TestResult] = []
        runner = SubprocessRunner(timeout=self.config.timeout_seconds)

        # Ejecutar comandos de mi fase
        commands = self._get_commands(strategy)

        for name, cmd in commands:
            test_start = datetime.now()

            try:
                stdout, stderr, returncode = await runner.run(
                    cmd,
                    cwd=project_root,
                )

                results.append(
                    TestResult(
                        name=name,
                        passed=returncode == 0,
                        duration_ms=(datetime.now() - test_start).total_seconds() * 1000,
                        stdout=stdout,
                        stderr=stderr,
                        error_message=stderr if returncode != 0 else None,
                    )
                )

                if not results[-1].passed and self.config.fail_fast:
                    break

            except Exception as e:
                results.append(
                    TestResult(
                        name=name,
                        passed=False,
                        duration_ms=0,
                        error_message=str(e),
                    )
                )

        return PhaseResult(
            phase=self.phase_name,
            test_results=results,
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed),
            skipped=0,
            duration=datetime.now() - start,
        )

    def _get_commands(self, strategy: TestStrategy) -> list[tuple[str, list[str]]]:
        """Retorna los comandos a ejecutar."""
        return [
            ("Mi Check 1", ["mi-tool", "check", "--option1"]),
            ("Mi Check 2", ["mi-tool", "validate"]),
        ]
```

### Paso 3: Agregar al enum

```python
# src/autotest/models/project.py
class TestPhase(str, Enum):
    SMOKE = "smoke"
    UNIT = "unit"
    INTEGRATION = "integration"
    SECURITY = "security"
    QUALITY = "quality"
    CUSTOM = "custom"  # Nueva fase
```

### Paso 4: Registrar en engine

```python
# src/autotest/executor/engine.py
from autotest.executor.phases.mi_fase import MiFaseExecutor

PHASE_EXECUTORS = {
    TestPhase.SMOKE: SmokePhaseExecutor,
    TestPhase.UNIT: UnitPhaseExecutor,
    # ...
    TestPhase.CUSTOM: MiFaseExecutor,  # Nuevo
}
```

---

## 5. Crear un Reporter

### Paso 1: Crear el archivo

```bash
# src/autotest/reporter/mi_reporter.py
```

### Paso 2: Implementar el reporter

```python
"""Reporter en formato XML (ejemplo)."""

from pathlib import Path
import xml.etree.ElementTree as ET

from autotest.config import AutoTestConfig
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter


class XMLReporter(BaseReporter):
    """Genera reportes en formato XML (JUnit compatible)."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def generate(self, report_data: ReportData) -> Path:
        """Genera el reporte XML."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"autotest-report-{report_data.report_id}.xml"

        # Crear estructura XML
        root = ET.Element("testsuites")
        root.set("name", report_data.project.name)
        root.set("tests", str(self._count_tests(report_data)))

        for phase in report_data.execution.phases:
            testsuite = ET.SubElement(root, "testsuite")
            testsuite.set("name", phase.phase.value)
            testsuite.set("tests", str(phase.total_tests))
            testsuite.set("failures", str(phase.failed))
            testsuite.set("time", str(phase.duration.total_seconds()))

            for test in phase.test_results:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", test.name)
                testcase.set("time", str(test.duration_ms / 1000))

                if not test.passed:
                    failure = ET.SubElement(testcase, "failure")
                    failure.text = test.error_message or "Test failed"

        # Escribir archivo
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="unicode", xml_declaration=True)

        return output_path

    def _count_tests(self, report_data: ReportData) -> int:
        return sum(p.total_tests for p in report_data.execution.phases)
```

### Paso 3: Registrar en engine

```python
# src/autotest/reporter/engine.py
from autotest.reporter.xml_reporter import XMLReporter

reporters = {
    "terminal": lambda: TerminalReporter(self.config),
    "json": lambda: JSONReporter(self.config),
    "html": lambda: HTMLReporter(self.config),
    "xml": lambda: XMLReporter(self.config),  # Nuevo
}
```

---

## 6. Testing de Plugins

### Crear tests unitarios

```python
# tests/unit/test_mi_detector.py
import pytest
from pathlib import Path

from autotest.detector.languages.mi_lenguaje import MiLenguajeDetector


@pytest.fixture
def detector():
    return MiLenguajeDetector()


def test_detect_mi_lenguaje(detector, tmp_path):
    # Crear archivo de prueba
    (tmp_path / "main.miext").write_text("// Mi codigo")

    result = detector.detect(tmp_path)

    assert result is not None
    assert len(result.files) == 1


def test_detect_no_files(detector, tmp_path):
    result = detector.detect(tmp_path)
    assert result is None
```

### Ejecutar tests

```bash
pytest tests/unit/test_mi_detector.py -v
```

---

## Checklist de Plugin

- [ ] Implementar clase base (ABC)
- [ ] Registrar en registry/engine
- [ ] Agregar a enums si es necesario
- [ ] Actualizar __init__.py
- [ ] Agregar prompts de IA (si aplica)
- [ ] Escribir tests unitarios
- [ ] Actualizar documentacion
- [ ] Probar integracion completa
