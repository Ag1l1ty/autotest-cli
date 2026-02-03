# Arquitectura de AutoTest CLI

## Version
v0.1.0

## Vision General

AutoTest CLI es una herramienta de linea de comandos que analiza proyectos de software automaticamente,
identifica tecnologias, analiza calidad del codigo, genera tests con IA, y ejecuta pruebas en fases.

## Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI (Typer + Rich)                          │
│   autotest scan | detect | analyze | generate | execute             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AutoTestConfig (Pydantic)                      │
│   CLI args → ENV vars → .autotest.yaml → pyproject.toml → defaults │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   Detector    │──────►│   Analyzer    │──────►│  Adaptation   │
│               │       │               │       │               │
│ ProjectInfo   │       │ AnalysisReport│       │ TestStrategy  │
└───────────────┘       └───────────────┘       └───────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
              ┌───────────────┐       ┌───────────────┐
              │   Executor    │──────►│   Reporter    │
              │               │       │               │
              │ExecutionReport│       │  ReportData   │
              └───────────────┘       └───────────────┘
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
                  ┌──────────┐         ┌──────────┐         ┌──────────┐
                  │ Terminal │         │   JSON   │         │   HTML   │
                  │  (Rich)  │         │  (CI/CD) │         │(Jinja2)  │
                  └──────────┘         └──────────┘         └──────────┘
```

## Modulos

### 1. Detector de Proyecto (`detector/`)

**Responsabilidad**: Escanear el directorio del proyecto e identificar tecnologias.

**Componentes:**
- `BaseLanguageDetector` (ABC) - Interfaz para detectores
- `DetectorRegistry` - Registro con decorador `@register`
- `ProjectScanner` - Orquestador que ejecuta todos los detectores
- 6 detectores: Python, JavaScript, Java, Go, Rust, C#

**Produce**: `ProjectInfo`
- Lenguajes detectados con archivos y LOC
- Frameworks identificados (Django, React, Spring, etc.)
- Herramientas de testing existentes

**Patron**: Strategy + Registry

### 2. Analizador de Codigo (`analyzer/`)

**Responsabilidad**: Analizar la estructura del codigo para extraer metricas.

**Componentes:**
- `AnalysisEngine` - Orquestador async
- Parsers por lenguaje (AST para Python, regex para otros)
- 4 analizadores:
  - `complexity.py` - Complejidad ciclomatica (radon para Python)
  - `coupling.py` - Grafo de imports, acoplamiento entre modulos
  - `coverage_gap.py` - Funciones sin tests asociados
  - `dead_code.py` - Codigo no referenciado

**Consume**: `ProjectInfo`
**Produce**: `AnalysisReport`
- Metricas por funcion (complejidad, LOC)
- Funciones sin tests
- Modulos con alto acoplamiento
- Codigo muerto detectado

**Patron**: Template Method + Strategy

### 3. Motor de Adaptacion (`adaptation/`)

**Responsabilidad**: Seleccionar herramientas y generar tests con IA.

**Componentes:**
- `AdaptationEngine` - Orquestador
- Toolchains por lenguaje:
  - `python_tools.py` - pytest, coverage.py, pytest-mock
  - `javascript_tools.py` - jest, vitest, c8
  - `java_tools.py` - JUnit 5, JaCoCo, Mockito
  - `go_tools.py` - go test, go cover, testify
  - `rust_tools.py` - cargo test, tarpaulin, mockall
  - `csharp_tools.py` - dotnet test, coverlet, Moq
- `AITestGenerator` - Genera unit tests via Claude API
- `AIIntegrationTestGenerator` - Genera integration tests con mocks
- `GeneratedTestValidator` - Validacion de seguridad y sintaxis

**Consume**: `ProjectInfo` + `AnalysisReport`
**Produce**: `TestStrategy`
- Toolchain seleccionado
- Tests unitarios generados
- Tests de integracion con mocks
- Comandos de ejecucion

**Patron**: Abstract Factory + Adapter

### 4. Ejecutor de Pruebas (`executor/`)

**Responsabilidad**: Ejecutar tests en fases con sandbox aislado.

**Componentes:**
- `ExecutionEngine` - Orquestador con secuenciamiento
- `TestSandbox` - Directorio temporal para ejecucion segura
- `SubprocessRunner` - Ejecucion async de comandos
- 5 fases:
  - `smoke.py` - Compilacion, dependencias, entry points
  - `unit.py` - Tests unitarios existentes + generados
  - `integration.py` - Tests de integracion (APIs, DB, servicios)
  - `security.py` - Vulnerabilidades, secretos hardcodeados
  - `quality.py` - Linting, tipos, complejidad

**Consume**: `TestStrategy`
**Produce**: `ExecutionReport`
- Resultados por fase
- Pass/fail rate
- Coverage (si disponible)
- Duracion

**Patron**: Chain of Responsibility + Template Method

### 5. Generador de Reportes (`reporter/`)

**Responsabilidad**: Generar reportes en multiples formatos.

**Componentes:**
- `ReportEngine` - Orquestador con scoring de calidad
- `TerminalReporter` - Salida Rich con tablas, paneles, arboles
- `JSONReporter` - JSON serializado con Pydantic (para CI/CD)
- `HTMLReporter` - HTML interactivo con Jinja2

**Consume**: Todos los modelos anteriores
**Produce**:
- `ReportData` con `QualitySummary` (score 0-100)
- Archivos: `{proyecto}/reports/autotest-report-AT-YYYYMMDD-XXXXXX.html`

**Patron**: Strategy + Template Method

## Flujo de Datos Detallado

```
CLI: autotest scan /path/to/project --open
  │
  ├── Parse args → AutoTestConfig
  │
  ▼
[1] ProjectScanner.scan(path)
    │
    ├── Para cada detector registrado:
    │   └── detector.detect(path) → LanguageInfo?
    │
    └── Agrega frameworks, test tools detectados
                           │
                           ▼
                      ProjectInfo
                      {
                        name: "mi-proyecto",
                        languages: [Python, JavaScript],
                        frameworks: [FastAPI, React],
                        test_tools: ["pytest", "jest"]
                      }
                           │
                           ▼
[2] AnalysisEngine.analyze(ProjectInfo)
    │
    ├── Para cada lenguaje:
    │   └── parser.parse(files) → funciones, imports
    │
    ├── complexity.analyze() → metricas
    ├── coupling.analyze() → grafo
    ├── coverage_gap.analyze() → gaps
    └── dead_code.analyze() → unused
                           │
                           ▼
                     AnalysisReport
                     {
                       total_functions: 45,
                       avg_complexity: 4.2,
                       untested_functions: ["func_a", "func_b"],
                       coupling_issues: [...],
                       dead_code_functions: [...]
                     }
                           │
                           ▼
[3] AdaptationEngine.adapt(ProjectInfo, AnalysisReport)
    │
    ├── Selecciona toolchain por lenguaje principal
    │
    ├── Si ai_enabled:
    │   ├── AITestGenerator.generate(untested_functions)
    │   │   └── Claude API → unit tests
    │   │
    │   └── AIIntegrationTestGenerator.generate(analysis)
    │       └── Claude API → integration tests con mocks
    │
    └── Valida tests generados (sintaxis, seguridad)
                           │
                           ▼
                     TestStrategy
                     {
                       toolchain: PythonToolchain,
                       unit_tests: [GeneratedTest...],
                       integration_tests: [GeneratedTest...],
                       generation_stats: {attempted: 20, valid: 18}
                     }
                           │
                           ▼
[4] ExecutionEngine.execute(TestStrategy)
    │
    ├── _write_tests_to_project()
    │   ├── tests/*.py (unit)
    │   └── tests/integration/*.py (integration)
    │
    ├── Crea TestSandbox (temp dir con copia)
    │
    └── Para cada fase en orden:
        ├── smoke → compila, verifica deps
        ├── unit → pytest tests/
        ├── integration → pytest tests/integration/
        └── quality → ruff, mypy
                           │
                           ▼
                    ExecutionReport
                    {
                      phases: [PhaseResult...],
                      overall_pass_rate: 0.85,
                      overall_coverage: 72.5
                    }
                           │
                           ▼
[5] ReportEngine.report(project, analysis, strategy, execution)
    │
    ├── _calculate_quality() → QualitySummary (0-100)
    │
    ├── TerminalReporter → consola Rich
    ├── JSONReporter → report.json
    └── HTMLReporter → autotest-report-AT-YYYYMMDD-XXXXXX.html
                           │
                           ▼
                    {proyecto}/reports/
                    └── autotest-report-AT-20260203-A1B2C3.html

    Si --open: webbrowser.open(html_path)
```

## Modelos (Contratos)

Todos los modelos estan en `models/` como Pydantic v2 BaseModel.

```python
# models/project.py
class ProjectInfo(BaseModel):
    name: str
    root_path: Path
    languages: list[LanguageInfo]
    frameworks: list[FrameworkInfo]
    test_tools: list[str]

# models/analysis.py
class AnalysisReport(BaseModel):
    total_functions: int
    avg_complexity: float
    untested_functions: list[str]
    coupling_issues: list[CouplingIssue]
    dead_code_functions: list[str]

# models/adaptation.py
class TestStrategy(BaseModel):
    toolchain: ToolChainConfig
    unit_tests: list[GeneratedTest]
    integration_tests: list[GeneratedTest]
    ai_generation_used: bool
    generation_stats: dict

# models/execution.py
class ExecutionReport(BaseModel):
    phases: list[PhaseResult]
    overall_pass_rate: float
    overall_coverage: float | None

# models/report.py
class ReportData(BaseModel):
    report_id: str  # AT-YYYYMMDD-XXXXXX
    project: ProjectInfo
    analysis: AnalysisReport
    strategy: TestStrategy
    execution: ExecutionReport
    quality: QualitySummary
```

## Extensibilidad

### Agregar un nuevo lenguaje:
1. Crear detector en `detector/languages/nuevo.py`
2. Usar `@register("nuevo")`
3. Crear parser en `analyzer/parsers/nuevo_parser.py`
4. Crear toolchain en `adaptation/toolchains/nuevo_tools.py`
5. Agregar prompts en `adaptation/ai/prompts.py`
6. Agregar al enum `Language` en `models/project.py`

### Agregar una nueva fase:
1. Crear ejecutor en `executor/phases/nueva_fase.py`
2. Implementar `BasePhaseExecutor`
3. Registrar en `executor/engine.py` PHASE_EXECUTORS
4. Agregar a `TestPhase` enum en `models/project.py`

### Agregar un nuevo formato de reporte:
1. Crear reporter en `reporter/nuevo_reporter.py`
2. Implementar `BaseReporter.generate()`
3. Registrar en `reporter/engine.py` reporters dict
