# CLAUDE.md - Contexto del Proyecto AutoTest CLI

## Version Actual
**v0.1.0** - Release inicial

## Repositorio
- **URL:** https://github.com/Ag1l1ty/autotest-cli
- **Branch principal:** main
- **Licencia:** MIT

---

## Descripcion del Proyecto

AutoTest CLI es una herramienta de linea de comandos que automatiza el analisis y testing de proyectos de software. Detecta tecnologias, analiza codigo, genera tests con IA (Claude API) y ejecuta pruebas en multiples fases.

### Lenguajes Soportados
- Python (pytest, coverage.py, pytest-mock)
- JavaScript/TypeScript (jest, vitest, c8)
- Java (JUnit 5, JaCoCo, Mockito)
- Go (go test, go cover, testify)
- Rust (cargo test, tarpaulin, mockall)
- C# (dotnet test, coverlet, Moq)

### Fases de Ejecucion
1. **Smoke** - Compilacion, dependencias, puntos de entrada
2. **Unit** - Tests unitarios existentes + generados por IA
3. **Integration** - Tests de integracion con mocks automaticos
4. **Security** - Vulnerabilidades, secretos hardcodeados
5. **Quality** - Linting, tipos, complejidad

---

## Estructura del Proyecto

```
TestingApp/
├── pyproject.toml              # Configuracion del proyecto y dependencias
├── README.md                   # Documentacion principal
├── CLAUDE.md                   # Este archivo - contexto para Claude
├── .gitignore
├── .autotest.yaml.example      # Ejemplo de configuracion
├── src/
│   └── autotest/
│       ├── __init__.py         # Version: 0.1.0
│       ├── __main__.py         # Entry point: python -m autotest
│       ├── cli.py              # Comandos Typer: scan, detect, analyze, generate, execute
│       ├── config.py           # AutoTestConfig (Pydantic Settings)
│       ├── constants.py        # Extensiones, mappings, defaults
│       ├── exceptions.py       # Jerarquia de excepciones
│       ├── models/             # Contratos Pydantic v2
│       │   ├── project.py      # ProjectInfo, LanguageInfo, enums
│       │   ├── analysis.py     # FunctionMetrics, AnalysisReport
│       │   ├── adaptation.py   # ToolChainConfig, GeneratedTest, TestStrategy
│       │   ├── execution.py    # TestResult, PhaseResult, ExecutionReport
│       │   └── report.py       # ReportData, QualitySummary
│       ├── detector/           # Modulo 1: Deteccion de tecnologias
│       │   ├── base.py         # BaseLanguageDetector (ABC)
│       │   ├── scanner.py      # ProjectScanner (orquestador)
│       │   ├── registry.py     # @register decorator
│       │   └── languages/      # Detectores por lenguaje
│       ├── analyzer/           # Modulo 2: Analisis de codigo
│       │   ├── engine.py       # AnalysisEngine (async)
│       │   ├── complexity.py   # Complejidad ciclomatica
│       │   ├── coupling.py     # Grafo de imports
│       │   ├── coverage_gap.py # Funciones sin tests
│       │   ├── dead_code.py    # Codigo muerto
│       │   └── parsers/        # Parsers por lenguaje
│       ├── adaptation/         # Modulo 3: Generacion de tests
│       │   ├── engine.py       # AdaptationEngine
│       │   ├── toolchains/     # Configuracion por lenguaje
│       │   └── ai/
│       │       ├── generator.py           # AITestGenerator (unit tests)
│       │       ├── integration_generator.py # AIIntegrationTestGenerator
│       │       ├── prompts.py             # Templates por lenguaje
│       │       └── validator.py           # Validacion de tests
│       ├── executor/           # Modulo 4: Ejecucion de pruebas
│       │   ├── engine.py       # ExecutionEngine
│       │   ├── sandbox.py      # TestSandbox (temp dir)
│       │   ├── runners/        # SubprocessRunner async
│       │   └── phases/         # Ejecutores por fase
│       ├── reporter/           # Modulo 5: Reportes
│       │   ├── engine.py       # ReportEngine
│       │   ├── terminal.py     # Rich tables/panels
│       │   ├── json_reporter.py
│       │   ├── html_reporter.py
│       │   └── templates/      # Jinja2 templates
│       └── utils/              # Utilidades
├── tests/
│   ├── conftest.py
│   ├── fixtures/               # Proyectos de ejemplo
│   ├── unit/                   # Tests unitarios
│   └── integration/            # Tests E2E
└── docs/
    ├── architecture.md
    ├── configuration.md
    └── plugin-guide.md
```

---

## Flujo de Datos

```
CLI: autotest scan /path/to/project --open
  │
  ▼
[1] ProjectScanner.scan(path) ─────────────► ProjectInfo
  │                                          (lenguajes, frameworks, archivos)
  ▼
[2] AnalysisEngine.analyze(ProjectInfo) ───► AnalysisReport
  │                                          (complejidad, acoplamiento, gaps)
  ▼
[3] AdaptationEngine.adapt(ProjectInfo, AnalysisReport)
  │   ├── Selecciona toolchain por lenguaje
  │   ├── AITestGenerator genera unit tests
  │   └── AIIntegrationTestGenerator genera integration tests con mocks
  │                                        ▼
  │                                   TestStrategy
  │                                   (tests generados, comandos)
  ▼
[4] ExecutionEngine.execute(TestStrategy)
  │   ├── Escribe tests en proyecto (tests/, tests/integration/)
  │   ├── Crea sandbox temporal
  │   └── Ejecuta fases: smoke → unit → integration → quality
  │                                        ▼
  │                                   ExecutionReport
  ▼
[5] ReportEngine.report(...)
    ├── Terminal (Rich)
    ├── JSON (CI/CD)
    └── HTML (interactivo con ID unico)
         ▼
    {proyecto}/reports/autotest-report-AT-YYYYMMDD-XXXXXX.html
```

---

## Ajustes y Fixes Realizados

### 1. Integracion de Tests de Integracion
**Problema:** Los tests de integracion no se generaban en el pipeline completo.
**Causa:** `cli.py` tenia hardcodeado `phases="smoke,unit,quality"` sin "integration".
**Solucion:** Actualizado a `phases="smoke,unit,integration,quality"` en cli.py:50.

### 2. Generacion de Mocks Automaticos
**Implementado:** `AIIntegrationTestGenerator` detecta automaticamente:
- Conexiones a Supabase, Airtable, Firebase
- Llamadas HTTP (requests, httpx, aiohttp)
- Accesos a OneDrive, Google Drive, AWS S3
- Base de datos (SQLAlchemy, psycopg2, pymongo)

Los tests generados incluyen mocks con `unittest.mock.patch`.

### 3. Persistencia de Tests Generados
**Problema:** Tests se perdian al terminar el sandbox.
**Solucion:** `ExecutionEngine._write_tests_to_project()` guarda tests en:
- `{proyecto}/tests/` - unit tests
- `{proyecto}/tests/integration/` - integration tests

### 4. Reportes HTML con ID Unico
**Implementado:** Cada reporte tiene codigo `AT-YYYYMMDD-XXXXXX`:
- Aparece en nombre de archivo
- Aparece en header y footer del HTML
- Formato: `autotest-report-AT-20260203-A1B2C3.html`

### 5. UX de Reportes Mejorada
**Cambios:**
- Reportes se guardan en `{proyecto}/reports/`
- Output por defecto: `terminal,html`
- Flag `--open` abre HTML en navegador
- Panel final muestra rutas de reportes generados

### 6. Soporte de API Key Dual
**Config:** Acepta `ANTHROPIC_API_KEY` o `AUTOTEST_AI_API_KEY`.

### 7. PYTHONPATH para Tests Generados
**Fix:** Tests generados incluyen `sys.path.insert()` para importar modulos del proyecto.

---

## Comandos CLI

```bash
# Pipeline completo con reporte HTML
autotest scan ./proyecto --open

# Solo detectar tecnologias
autotest detect ./proyecto

# Analizar codigo
autotest analyze ./proyecto

# Generar estrategia + tests IA
autotest generate ./proyecto

# Ejecutar pruebas
autotest execute ./proyecto

# Opciones
autotest scan ./proyecto \
  --output terminal,json,html \
  --phases smoke,unit,integration,quality \
  --no-ai \
  --verbose \
  --fail-fast \
  --open
```

---

## Instalacion

```bash
# Desde GitHub
pip install git+https://github.com/Ag1l1ty/autotest-cli.git

# Desarrollo local
git clone https://github.com/Ag1l1ty/autotest-cli.git
cd autotest-cli
pip install -e ".[dev]"

# Configurar API key
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

---

## Dependencias Principales

| Paquete | Version | Uso |
|---------|---------|-----|
| typer | >=0.15 | CLI framework |
| rich | >=13.9 | Terminal formatting |
| pydantic | >=2.10 | Data models |
| pydantic-settings | >=2.6 | Config loading |
| radon | >=6.0 | Complejidad Python |
| anthropic | >=0.40 | Claude API |
| jinja2 | >=3.1 | HTML templates |
| pyyaml | >=6.0 | Config YAML |

---

## Modelo de IA

- **Modelo:** claude-sonnet-4-20250514
- **Uso:** Generacion de unit tests e integration tests
- **Tokens:** ~2000 por funcion (unit), ~3000 por modulo (integration)
- **Validacion:** Sintaxis Python, imports peligrosos bloqueados

---

## Archivos de Configuracion

### .autotest.yaml
```yaml
phases:
  - smoke
  - unit
  - integration
  - quality
output_formats:
  - terminal
  - html
ai_enabled: true
ai_model: claude-sonnet-4-20250514
complexity_threshold: 10
timeout_seconds: 300
```

### pyproject.toml
```toml
[tool.autotest]
phases = ["smoke", "unit", "integration", "quality"]
output_formats = ["terminal", "html"]
```

---

## Changelog

### v0.1.0 (2026-02-03)
- Release inicial
- Detector de 6 lenguajes
- Analizador de complejidad, acoplamiento, coverage gaps
- Generador de tests con Claude API (unit + integration)
- Ejecutor de 5 fases con sandbox
- Reportes: Terminal, JSON, HTML con ID unico
- CLI: scan, detect, analyze, generate, execute
- Publicado en GitHub: Ag1l1ty/autotest-cli

---

## Proximos Pasos Sugeridos

1. **Cache de analisis** - `.autotest_cache/` para re-ejecutar solo archivos cambiados
2. **Modo incremental** - `--changed-only` con git diff
3. **Watch mode** - `--watch` para re-ejecutar al cambiar archivos
4. **JUnit XML** - Formato nativo para GitHub Actions/Jenkins
5. **Docker sandbox** - Aislamiento completo para tests IA
6. **Estimacion de costo** - Mostrar tokens/costo antes de llamar a Claude
7. **Perfiles** - `.autotest.yaml` con perfiles (ci, thorough, security-only)

---

## Notas para Claude

Cuando trabajes en este proyecto:

1. **Arquitectura modular** - Cada modulo tiene su engine orquestador
2. **Contratos Pydantic** - Todos los datos pasan por modelos validados
3. **Async first** - Engines usan async/await
4. **Registry pattern** - Detectores y fases usan decorador @register
5. **Tests generados** - Se guardan en el proyecto, no solo en sandbox
6. **API key** - Busca ANTHROPIC_API_KEY o AUTOTEST_AI_API_KEY
7. **Reportes** - Siempre en `{proyecto}/reports/` con ID unico
