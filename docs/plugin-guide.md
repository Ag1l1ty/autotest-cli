# Guia de Plugins para AutoTest CLI

## Crear un Detector de Lenguaje

```python
from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo

@register("mi_lenguaje")
class MiDetector(BaseLanguageDetector):
    
    @property
    def language_name(self) -> str:
        return "mi_lenguaje"
    
    def detect(self, root: Path) -> LanguageInfo | None:
        files = list(root.rglob("*.miext"))
        if not files:
            return None
        return LanguageInfo(
            language=Language.PYTHON,  # o agregar al enum
            files=files,
            total_loc=sum(count_lines(f) for f in files),
        )
    
    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        return []
    
    def detect_test_tools(self, root: Path) -> list[str]:
        return []
```

## Crear un Toolchain

```python
from autotest.adaptation.base import BaseAdapter
from autotest.models.adaptation import ToolChainConfig

class MiAdapter(BaseAdapter):
    
    def get_toolchain(self) -> ToolChainConfig:
        return ToolChainConfig(
            language=Language.PYTHON,
            test_runner="mi_runner",
            test_command=["mi_runner", "test"],
            coverage_tool="mi_cov",
            coverage_command=["mi_runner", "coverage"],
            mock_library="mi_mock",
        )
    
    def get_test_command(self, phase: TestPhase) -> list[str]:
        return ["mi_runner", "test"]
    
    def get_coverage_command(self) -> list[str]:
        return ["mi_runner", "coverage"]
    
    def get_lint_commands(self) -> list[list[str]]:
        return [["mi_linter", "check"]]
```

## Crear un Reportero

```python
from autotest.reporter.base import BaseReporter
from autotest.models.report import ReportData

class MiReporter(BaseReporter):
    
    async def generate(self, report_data: ReportData) -> Path:
        # Generar reporte en formato personalizado
        output_path = Path("mi_reporte.xml")
        # ... logica de generacion
        return output_path
```

## Crear una Fase de Ejecucion

```python
from autotest.executor.base import BasePhaseExecutor
from autotest.models.execution import PhaseResult
from autotest.models.project import TestPhase

class MiFaseExecutor(BasePhaseExecutor):
    
    @property
    def phase_name(self) -> TestPhase:
        return TestPhase.QUALITY  # o agregar al enum
    
    async def execute(self, strategy, project_root) -> PhaseResult:
        # ... logica de ejecucion
        pass
```
