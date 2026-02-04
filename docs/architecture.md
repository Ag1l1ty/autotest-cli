# Arquitectura de Code Doctor

## Version
v0.2.0

## Vision General

Code Doctor es una herramienta de linea de comandos que diagnostica proyectos de software.
Detecta tecnologias, analiza calidad del codigo, encuentra problemas reales (bugs, seguridad,
complejidad) y proporciona fixes concretos y accionables.

## Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI (Typer + Rich)                          │
│         autotest diagnose | scan | detect | analyze                 │
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
│   Detector    │──────►│   Analyzer    │──────►│   Diagnosis   │
│               │       │               │       │               │
│ ProjectInfo   │       │ AnalysisReport│       │DiagnosisReport│
└───────────────┘       └───────────────┘       └───────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
              ┌───────────────┐
              │   Reporter    │
              │               │
              │  ReportData   │
              └───────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Terminal  │  │   JSON   │  │   HTML   │  │ Markdown │
  │  (Rich)   │  │  (CI/CD) │  │ (Jinja2) │  │  (.md)   │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
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

### 3. Motor de Diagnostico (`diagnosis/`)

**Responsabilidad**: Convertir datos de analisis en hallazgos accionables con fixes concretos.

**Componentes:**
- `DiagnosisEngine` - Orquestador que combina todas las fuentes de findings
- `static_findings.py` - Genera findings de complejidad, dead code, coupling, missing tests
- `security_scanner.py` - Escanea secretos hardcodeados con linea exacta
- `ai_reviewer.py` - Revision de codigo con Claude API (opcional)
- `context_builder.py` - Construye contexto rico para AI review
- `prompts.py` - Prompts y tool schemas para Claude
- `auto_fixer.py` - Aplica fixes automaticamente al codigo fuente

**Consume**: `ProjectInfo` + `AnalysisReport`
**Produce**: `DiagnosisReport`
- Lista de `Finding` con severity, category, suggested_fix
- Health score (0-100) basado en findings reales
- Conteos por severidad (critical, warning, info)

**Patron**: Pipeline + Strategy

#### Fuentes de Findings

| Fuente | Siempre activa | Necesita AI | Findings tipicos |
|--------|---------------|-------------|------------------|
| Static Findings | Si | No | Complejidad alta, dead code, coupling, missing tests |
| Security Scanner | Si | No | Secretos hardcodeados, API keys, passwords |
| AI Reviewer | No | Si | Bugs, edge cases, error handling, seguridad avanzada |

#### Pipeline de Diagnostico

1. **Static findings** - Convierte metricas de `AnalysisReport` en findings
2. **Security scan** - Escanea archivos buscando patrones de secretos
3. **AI review** (opcional) - Envia funciones priorizadas a Claude para revision
4. **Deduplicacion** - Elimina findings duplicados (mismo archivo + linea cercana + categoria)
5. **Relativizar paths** - Convierte paths absolutos a relativos
6. **Ordenar y asignar IDs** - Ordena por severidad, asigna CD-001, CD-002, ...
7. **Calcular health score** - Formula basada en conteos de findings

### 4. Generador de Reportes (`reporter/`)

**Responsabilidad**: Generar reportes en multiples formatos con findings accionables.

**Componentes:**
- `ReportEngine` - Orquestador con filtrado por severidad
- `TerminalReporter` - Salida Rich con findings priorizados y health score
- `JSONReporter` - JSON serializado con Pydantic (para CI/CD, datos completos sin filtrar)
- `HTMLReporter` - HTML interactivo con fixes colapsables y boton "Copiar fix"
- `MarkdownReporter` - Markdown para PRs de GitHub y documentacion

**Consume**: `ProjectInfo` + `AnalysisReport` + `DiagnosisReport`
**Produce**:
- `ReportData` con `QualitySummary` y `DiagnosisReport`
- Archivos: `{proyecto}/reports/autotest-report-AT-YYYYMMDD-XXXXXX.{html,json,md}`

**Patron**: Strategy + Template Method

#### Filtrado de Severidad

- El JSON siempre contiene todos los findings (datos completos para CI/CD)
- Terminal, HTML y Markdown filtran por `--severity` (default: critical,warning)
- `--top N` limita findings por grupo de severidad en la salida visual

## Flujo de Datos Detallado

```
CLI: autotest diagnose /path/to/project --open
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
                       untested_functions: [FunctionMetrics...],
                       coupling_issues: [CouplingInfo...],
                       dead_code_functions: [FunctionMetrics...]
                     }
                           │
                           ▼
[3] DiagnosisEngine.diagnose(ProjectInfo, AnalysisReport)
    │
    ├── static_findings(analysis) → complejidad, dead code, coupling, missing tests
    ├── security_scanner(project_root) → secretos hardcodeados
    ├── ai_reviewer(functions) → bugs, edge cases (si AI habilitado)
    │
    ├── Deduplicar + relativizar paths + ordenar
    │
    └── Calcular health_score y summary
                           │
                           ▼
                    DiagnosisReport
                    {
                      findings: [Finding...],
                      health_score: 72.0,
                      health_label: "moderate",
                      critical_count: 2,
                      warning_count: 3,
                      info_count: 1
                    }
                           │
                           ▼
[4] ReportEngine.report_diagnosis(project, analysis, diagnosis)
    │
    ├── TerminalReporter → consola Rich
    ├── JSONReporter → report.json (datos completos)
    ├── HTMLReporter → autotest-report-AT-YYYYMMDD-XXXXXX.html
    └── MarkdownReporter → autotest-report-AT-YYYYMMDD-XXXXXX.md
                           │
                           ▼
                    {proyecto}/reports/
                    └── autotest-report-AT-20260203-A1B2C3.html

    Si --open: webbrowser.open(html_path)
    Si --fix: apply_fixes(findings, project_root)
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
    tested_function_count: int
    estimated_coverage: float
    high_complexity_functions: list[FunctionMetrics]
    untested_functions: list[FunctionMetrics]
    coupling_issues: list[CouplingInfo]
    dead_code_functions: list[FunctionMetrics]

# models/diagnosis.py
class Finding(BaseModel):
    id: str
    severity: Severity          # CRITICAL | WARNING | INFO
    category: FindingCategory   # bug, security, complexity, etc.
    title: str
    description: str
    file_path: str
    line_start: int
    suggested_fix: SuggestedFix | None
    confidence: float           # 0.0 - 1.0
    source: str                 # "static" | "ai" | "security"

class DiagnosisReport(BaseModel):
    findings: list[Finding]
    health_score: float         # 0 - 100
    health_label: str           # healthy | moderate | at-risk | critical

# models/report.py
class ReportData(BaseModel):
    report_id: str              # AT-YYYYMMDD-XXXXXX
    project: ProjectInfo
    analysis: AnalysisReport
    diagnosis: DiagnosisReport
    quality: QualitySummary
```

## Extensibilidad

### Agregar un nuevo lenguaje:
1. Crear detector en `detector/languages/nuevo.py`
2. Usar `@register("nuevo")`
3. Crear parser en `analyzer/parsers/nuevo_parser.py`
4. Agregar al enum `Language` en `models/project.py`

### Agregar un nuevo generador de findings:
1. Crear modulo en `diagnosis/mi_scanner.py`
2. Implementar funcion que retorne `list[Finding]`
3. Llamar desde `DiagnosisEngine.diagnose()`

### Agregar un nuevo formato de reporte:
1. Crear reporter en `reporter/mi_reporter.py`
2. Implementar `BaseReporter.generate()`
3. Registrar en `reporter/engine.py` reporters dict
