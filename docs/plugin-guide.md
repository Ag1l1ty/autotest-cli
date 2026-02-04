# Guia de Extensibilidad para Code Doctor

## Version
v0.2.0

## Introduccion

Code Doctor esta disenado con una arquitectura extensible que permite agregar soporte para
nuevos lenguajes, generadores de findings, y formatos de reporte.

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

    EXTENSIONS = {".miext", ".mi"}
    CONFIG_FILES = {"mi.config", "mi.json"}

    @property
    def language_name(self) -> str:
        return "mi_lenguaje"

    def detect(self, root: Path) -> LanguageInfo | None:
        files: list[Path] = []
        for ext in self.EXTENSIONS:
            files.extend(root.rglob(f"*{ext}"))

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
            language=Language.OTHER,
            files=files,
            total_loc=sum(count_lines(f) for f in files),
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        return []

    def detect_test_tools(self, root: Path) -> list[str]:
        return []
```

### Paso 3: Agregar al enum (opcional)

```python
# src/autotest/models/project.py
class Language(str, Enum):
    PYTHON = "python"
    # ... otros
    MI_LENGUAJE = "mi_lenguaje"  # Nuevo
```

### Paso 4: Registrar en __init__.py

```python
# src/autotest/detector/languages/__init__.py
from autotest.detector.languages.mi_lenguaje import MiLenguajeDetector
```

---

## 2. Crear un Generador de Findings

Los generadores de findings analizan el codigo y producen hallazgos accionables.

### Paso 1: Crear el archivo

```bash
# src/autotest/diagnosis/mi_scanner.py
```

### Paso 2: Implementar el scanner

```python
"""Scanner personalizado para Mi Lenguaje."""

from __future__ import annotations

from pathlib import Path

from autotest.models.diagnosis import (
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)


def scan_for_issues(project_root: Path) -> list[Finding]:
    """Escanea el proyecto buscando problemas especificos."""
    findings: list[Finding] = []

    for file_path in project_root.rglob("*.py"):
        # Saltar directorios comunes
        if ".git" in file_path.parts:
            continue

        content = file_path.read_text(errors="ignore")
        for line_num, line in enumerate(content.splitlines(), start=1):
            if _has_issue(line):
                findings.append(
                    Finding(
                        severity=Severity.WARNING,
                        category=FindingCategory.STYLE,
                        title=f"Problema encontrado en linea {line_num}",
                        description="Descripcion detallada del problema.",
                        file_path=str(file_path.relative_to(project_root)),
                        line_start=line_num,
                        suggested_fix=SuggestedFix(
                            description="Como arreglarlo",
                            code_before=line.strip(),
                            code_after=_fix_line(line).strip(),
                        ),
                        source="static",
                    )
                )

    return findings


def _has_issue(line: str) -> bool:
    # Logica de deteccion
    return False


def _fix_line(line: str) -> str:
    # Logica de correccion
    return line
```

### Paso 3: Integrar en DiagnosisEngine

```python
# src/autotest/diagnosis/engine.py - en el metodo diagnose()

from autotest.diagnosis.mi_scanner import scan_for_issues

# Dentro de DiagnosisEngine.diagnose():
custom_findings = scan_for_issues(project.root_path)
all_findings.extend(custom_findings)
```

---

## 3. Crear un Reporter

Los reporters generan la salida en diferentes formatos.

### Paso 1: Crear el archivo

```bash
# src/autotest/reporter/mi_reporter.py
```

### Paso 2: Implementar el reporter

```python
"""Reporter en formato XML (ejemplo)."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter


class XMLReporter(BaseReporter):
    """Genera reportes en formato XML."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def generate(self, report_data: ReportData) -> Path:
        """Genera el reporte XML."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"autotest-report-{report_data.report_id}.xml"

        # Generar XML con findings del diagnosis
        lines = ['<?xml version="1.0" encoding="utf-8"?>']
        lines.append(f'<diagnosis project="{report_data.project.name}">')

        if report_data.diagnosis:
            for f in report_data.diagnosis.findings:
                lines.append(f'  <finding id="{f.id}" severity="{f.severity.value}">')
                lines.append(f'    <title>{f.title}</title>')
                lines.append(f'    <file>{f.file_path}:{f.line_start}</file>')
                if f.suggested_fix:
                    lines.append(f'    <fix>{f.suggested_fix.description}</fix>')
                lines.append(f'  </finding>')

        lines.append('</diagnosis>')

        output_path.write_text("\n".join(lines))
        return output_path
```

### Paso 3: Registrar en engine

```python
# src/autotest/reporter/engine.py
from autotest.reporter.xml_reporter import XMLReporter

# En el dict de reporters:
reporters = {
    "terminal": lambda: TerminalReporter(self.config),
    "json": lambda: JSONReporter(self.config),
    "html": lambda: HTMLReporter(self.config),
    "markdown": lambda: MarkdownReporter(self.config),
    "xml": lambda: XMLReporter(self.config),  # Nuevo
}
```

---

## 4. Testing de Plugins

### Crear tests unitarios

```python
# tests/unit/test_mi_scanner.py
import pytest
from pathlib import Path

from autotest.diagnosis.mi_scanner import scan_for_issues


def test_finds_issues(tmp_path):
    (tmp_path / "main.py").write_text("# codigo con problema\n")
    findings = scan_for_issues(tmp_path)
    assert len(findings) >= 0  # Ajustar segun logica


def test_clean_project(tmp_path):
    (tmp_path / "main.py").write_text('print("hello")\n')
    findings = scan_for_issues(tmp_path)
    assert len(findings) == 0
```

### Ejecutar tests

```bash
pytest tests/unit/test_mi_scanner.py -v
```

---

## Checklist de Extension

- [ ] Implementar la logica del plugin
- [ ] Registrar en el modulo correspondiente (registry, engine, etc.)
- [ ] Agregar a enums si es necesario
- [ ] Escribir tests unitarios
- [ ] Probar integracion con el pipeline completo (`autotest diagnose`)
- [ ] Actualizar documentacion
