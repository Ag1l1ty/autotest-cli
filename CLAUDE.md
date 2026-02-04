# CLAUDE.md - Contexto del Proyecto Code Doctor (AutoTest CLI)

## Version Actual
**v0.2.0** - Pivot a Code Doctor (reporte estatico completado)

## Repositorio
- **URL:** https://github.com/Ag1l1ty/autotest-cli
- **Branch principal:** main
- **Licencia:** MIT

---

## Descripcion del Proyecto

Code Doctor (antes AutoTest CLI) es una herramienta de linea de comandos que diagnostica proyectos de software. Detecta tecnologias, analiza codigo, encuentra problemas reales (complejidad, dead code, coupling, missing tests, secretos hardcodeados) y proporciona fixes concretos y accionables.

### Pivot v0.1.0 -> v0.2.0
- **Antes:** Generaba tests con IA que fallaban por errores de la IA misma
- **Ahora:** Encuentra problemas reales en el codigo y da fixes copy-pasteables
- **Pipeline anterior:** Detect -> Analyze -> Generate Tests -> Execute Tests -> Report (5 pasos)
- **Pipeline nuevo:** Detect -> Analyze -> Diagnose -> Report (4 pasos)
- **Eliminados:** `adaptation/`, `executor/`, `error_analyzer.py`, `models/adaptation.py`, `models/execution.py`

### Lenguajes Soportados
- Python, JavaScript/TypeScript, Java, Go, Rust, C#

---

## Estructura del Proyecto

```
TestingApp/
├── pyproject.toml
├── README.md
├── CLAUDE.md                   # Este archivo
├── src/
│   └── autotest/
│       ├── __init__.py         # Version: 0.2.0
│       ├── __main__.py         # Entry point
│       ├── cli.py              # Comandos: diagnose, scan, detect, analyze
│       ├── config.py           # AutoTestConfig (Pydantic Settings)
│       ├── constants.py        # Mappings, defaults, TEST_PATTERNS, thresholds
│       ├── exceptions.py       # AutoTestError, DiagnosisError, AIReviewError
│       ├── models/
│       │   ├── project.py      # ProjectInfo, LanguageInfo, Language enum
│       │   ├── analysis.py     # FunctionMetrics, AnalysisReport, ModuleMetrics
│       │   ├── diagnosis.py    # Finding, DiagnosisReport, Severity, FindingCategory
│       │   └── report.py       # ReportData, QualitySummary
│       ├── detector/           # Modulo 1: Deteccion de tecnologias
│       │   ├── scanner.py      # ProjectScanner
│       │   ├── base.py         # BaseLanguageDetector (ABC)
│       │   ├── registry.py     # @register decorator
│       │   └── languages/      # 6 detectores (python, js, java, go, rust, csharp)
│       ├── analyzer/           # Modulo 2: Analisis de codigo
│       │   ├── engine.py       # AnalysisEngine (con _is_in_test_dir safety net)
│       │   ├── complexity.py   # Complejidad ciclomatica (radon para Python)
│       │   ├── coupling.py     # Grafo de imports, acoplamiento
│       │   ├── coverage_gap.py # Deteccion de funciones sin tests (cross-line regex)
│       │   ├── dead_code.py    # Codigo no referenciado
│       │   └── parsers/        # 6 parsers (python, js, java, go, rust, csharp)
│       ├── diagnosis/          # Modulo 3: Diagnostico
│       │   ├── engine.py       # DiagnosisEngine (orquestador, health score, dedup)
│       │   ├── static_findings.py  # complexity, dead_code, coupling, missing_tests
│       │   ├── security_scanner.py # Secretos hardcodeados con linea exacta
│       │   ├── context_builder.py  # Contexto rico para AI review
│       │   ├── prompts.py      # Prompts y tool schemas para Claude
│       │   ├── ai_reviewer.py  # AICodeReviewer con tool_use (opcional)
│       │   └── auto_fixer.py   # Aplicar fixes automaticamente (--fix)
│       ├── reporter/           # Modulo 4: Reportes
│       │   ├── engine.py       # ReportEngine.report_diagnosis()
│       │   ├── base.py         # BaseReporter (ABC)
│       │   ├── terminal.py     # Rich: findings, health score, category summaries
│       │   ├── json_reporter.py    # JSON completo (CI/CD)
│       │   ├── html_reporter.py    # HTML interactivo (Jinja2)
│       │   ├── markdown_reporter.py # Markdown para PRs
│       │   └── templates/
│       │       └── report.html.j2  # Template HTML con dark theme
│       └── utils/
│           └── file_utils.py   # safe_read, collect_files, find_files_by_pattern
├── tests/
│   ├── conftest.py             # Fixtures: default_config, python_project, etc.
│   ├── unit/                   # 83 tests unitarios
│   └── fixtures/               # Proyectos de ejemplo para tests
├── docs/
│   ├── architecture.md         # Arquitectura detallada v0.2.0
│   ├── plugin-guide.md         # Guia para extender
│   └── feedback-report-quality.md  # 12 puntos de mejora (todos implementados)
└── reports/                    # Reportes generados (gitignored)
```

---

## Flujo de Datos

```
CLI: autotest diagnose /path/to/project --open
  │
  ▼
[1] ProjectScanner.scan(path) ─────────────► ProjectInfo
  │                                          (lenguajes, frameworks, archivos)
  ▼
[2] AnalysisEngine.analyze(ProjectInfo) ───► AnalysisReport
  │   - Parsers extraen funciones por lenguaje
  │   - Calcula complejidad ciclomatica
  │   - Detecta funciones sin tests (cross-line regex)
  │   - Detecta dead code y coupling
  │   - Procesa funciones POR IDIOMA (no acumulativo)
  │   - Excluye archivos en directorios test (_is_in_test_dir)
  ▼
[3] DiagnosisEngine.diagnose(ProjectInfo, AnalysisReport)
  │   ├── static_findings: complejidad, dead code, coupling, missing tests
  │   ├── security_scanner: secretos hardcodeados con linea exacta
  │   └── ai_reviewer: bugs, seguridad, edge cases (opcional, --no-ai para desactivar)
  │   ├── Deduplicacion (mismo archivo + 3 lineas + misma categoria)
  │   └── Health score con desglose transparente
  │                                        ▼
  │                                   DiagnosisReport
  │                                   (findings con fixes, health_score)
  ▼
[4] ReportEngine.report_diagnosis(...)
    ├── Terminal (Rich) - findings priorizados con category summary
    ├── JSON (CI/CD) - datos completos sin filtrar
    ├── HTML (Jinja2) - interactivo con gradient urgencia, highlights, anchors
    └── Markdown - para PRs de GitHub
         ▼
    {proyecto}/reports/autotest-report-AT-YYYYMMDD-XXXXXX.html
```

---

## Comandos CLI

```bash
# Diagnostico completo (pipeline principal)
autotest diagnose ./proyecto --open

# Alias: scan llama internamente a diagnose
autotest scan ./proyecto --open

# Solo detectar tecnologias
autotest detect ./proyecto

# Analizar codigo (sin diagnostico)
autotest analyze ./proyecto

# Opciones de diagnose
autotest diagnose ./proyecto \
  --output terminal,json,html,markdown \
  --severity critical,warning \
  --top 5 \
  --no-ai \
  --verbose \
  --open \
  --fix \
  --dry-run
```

---

## Modelo de Datos: Finding

Cada hallazgo incluye:
- **id:** CD-001, CD-002, ... (secuencial, asignado por DiagnosisEngine)
- **severity:** CRITICAL | WARNING | INFO
- **category:** bug, security, error_handling, dead_code, complexity, coupling, missing_tests, style
- **title:** Descripcion corta (e.g. "Complejidad alta en analyze() — CC=26")
- **description:** Detalle con lineas y qualified name
- **file_path + line_start + line_end:** Ubicacion exacta
- **suggested_fix:** description, code_before, code_after, explanation
- **confidence:** 0.0 a 1.0 (AI findings se filtran por min_finding_confidence)
- **source:** "static" | "ai" | "security"

---

## Health Score

Formula basada en findings reales (no test pass rates):
- Start: 100
- CRITICAL: -10 c/u (cap -40)
- WARNING: -3 c/u (cap -30)
- INFO: -1 c/u (cap -10)
- Coverage gap: (1 - estimated_coverage/100) * 15

Labels: healthy (>=80), moderate (>=60), at-risk (>=40), critical (<40)

El HTML muestra desglose transparente: `100 −30 (24 warnings) −10 (54 notas) −8.7 (coverage gap) = 51`

---

## Reporte HTML: Funcionalidades

El reporte HTML (`report.html.j2`) incluye:

1. **Health Score badge** con desglose de la formula
2. **Overview cards**: Critical, Warnings, Info, Functions (con nombres untested), Languages
3. **Highlights verdes**: metricas positivas (coverage, tested count, 0 criticals, sin vulnerabilities)
4. **Top Acciones Prioritarias**: ordenadas por CC desc, con badges ALTO IMPACTO / MEDIO, anchors a findings
5. **Findings por severidad**: con category mini-summary ("20 complexity, 2 missing tests")
6. **Urgency gradient CSS**: CC>=25 rojo (extreme), CC>=15 naranja (high), default amarillo
7. **Fix box**: code_before (firma de funcion), code_after (fix con boton Copiar), explanation
8. **Leyenda CC colapsable**: explica 1-10 Normal, 11-20 Alta, 21-50 Muy alta, >50 Critica
9. **Filter banner**: muestra cuantos findings ocultos por --severity
10. **Footer accionable**: `autotest diagnose --fix` y `--severity critical,warning,info`
11. **Dark theme** con variables CSS, responsive

---

## Configuracion

### Campos en AutoTestConfig
- `project_path: Path` (requerido)
- `output_formats: list[str] = ["terminal"]`
- `output_dir: Path = Path("reports")`
- `complexity_threshold: int = 10`
- `ai_enabled: bool = True`
- `ai_api_key: str = ""` (de env ANTHROPIC_API_KEY)
- `ai_model: str = "claude-sonnet-4-20250514"`
- `ai_max_functions: int = 10`
- `min_finding_confidence: float = 0.6`
- `severity_filter: list[str] = ["critical", "warning"]`
- `top_findings: int = 5`
- `verbose: bool = False`

### Fuentes de configuracion (orden de prioridad)
1. CLI args (mayor prioridad)
2. ENV vars (AUTOTEST_*)
3. `.autotest.yaml`
4. `pyproject.toml [tool.codedoctor]`
5. Defaults

---

## Dependencias Principales

| Paquete | Version | Uso |
|---------|---------|-----|
| typer | >=0.15 | CLI framework |
| rich | >=13.9 | Terminal formatting |
| pydantic | >=2.10 | Data models (v2) |
| pydantic-settings | >=2.6 | Config loading |
| radon | >=6.0 | Complejidad Python |
| anthropic | >=0.40 | Claude API (AI review) |
| jinja2 | >=3.1 | HTML templates |
| pyyaml | >=6.0 | Config YAML |

---

## Bugs Corregidos en v0.2.0

### Bug: "Tested Functions: 0" (triple bug)
**Sintoma:** El reporte mostraba 0 funciones testeadas aunque el proyecto tenia tests.

**Causa raiz (3 problemas):**
1. **Python detector** usaba patrones restrictivos (`tests/**/test_*.py`) que excluian `conftest.py` y fixtures. Fix: usar `TEST_PATTERNS[Language.PYTHON]` de constants.py que incluye `tests/**/*.py`.
2. **coverage_gap.py** regex no cruzaba lineas — si la funcion y `assert` estaban en lineas diferentes, no matcheaba. Fix: agregar `re.DOTALL` con limite de 500 chars, mas fallback de "funcion llamada en tests" (`name\s*\(`).
3. **engine.py** llamaba `find_untested_functions(all_functions, lang_info)` con TODAS las funciones acumuladas. La segunda iteracion (JavaScript) reseteaba `is_tested=False` para funciones Python ya marcadas. Fix: procesar funciones POR IDIOMA con `lang_functions`.

**Safety net:** `_is_in_test_dir()` en engine.py excluye archivos en directorios test (tests/, test/, __tests__/, spec/, specs/) de source analysis.

### Bug: avg_complexity=0.0 y total_loc=0
**Causa:** AnalysisReport nunca recibia estos valores (defaulteaban a 0).
**Fix:** Calcular agregacion antes del return en engine.py.

### Bug: CC>20 contradecia umbral CC>10
**Causa:** Description en static_findings.py decia "CC>{COMPLEXITY_HIGH}" (20) pero el umbral real es COMPLEXITY_MEDIUM (10).
**Fix:** Usar COMPLEXITY_MEDIUM en descriptions y explanations.

---

## Thresholds de Complejidad

Definidos en `constants.py`:
- `COMPLEXITY_LOW = 5`
- `COMPLEXITY_MEDIUM = 10` — umbral de flagging (CC>10 genera finding)
- `COMPLEXITY_HIGH = 20` — umbral de severity bump
- `COMPLEXITY_VERY_HIGH = 50` — siempre CRITICAL

Thresholds de urgency gradient en HTML:
- CC >= 25 → `urgency-extreme` (borde rojo)
- CC >= 15 → `urgency-high` (borde naranja)
- Default → borde amarillo (warnings) o rojo (criticals)

---

## Tests

83 tests unitarios en `tests/unit/`:
- `test_config.py` - AutoTestConfig defaults y overrides
- `test_models.py` - Pydantic models, Finding, DiagnosisReport
- `test_analyzer.py` - Parser, complexity, dead code
- `test_detector.py` - Deteccion de lenguajes
- `test_diagnosis_engine.py` - Health score, dedup, pipeline
- `test_static_findings.py` - Complexity, dead code, coupling, missing tests
- `test_security_scanner.py` - Secretos hardcodeados, severidad test vs produccion
- `test_auto_fixer.py` - Aplicacion de fixes

Correr tests: `python3 -m pytest tests/ -v`

---

## Estado Actual y Proximos Pasos

### Completado (v0.2.0)
- Pipeline estatico completo: Detect → Analyze → Diagnose → Report
- 4 formatos de reporte: terminal, JSON, HTML, markdown
- Security scanner (secretos hardcodeados)
- Health score con desglose transparente
- Reporte HTML con dark theme, urgency gradient, highlights, anchors
- 83 tests unitarios pasando

### Pendiente (futuro)
- **AI review** (`--no-ai` actualmente activo por default en desarrollo) — requiere ANTHROPIC_API_KEY
- **`--fix`** — auto_fixer.py existe pero necesita findings con `code_after` generados por AI
- **Mas heuristicas de coverage_gap** — actualmente busca nombre de funcion en test content
- **Soporte para monorepos** — multiples proyectos en un directorio
- **CI/CD integration** — GitHub Actions, GitLab CI templates
- **Cache de resultados** — evitar re-analisis de archivos no modificados

---

## Changelog

### v0.2.0 (2026-02-03)
- **PIVOT:** De "generador de tests" a "Code Doctor"
- Nuevo pipeline: Detect -> Analyze -> Diagnose -> Report
- Modulo `diagnosis/` con static findings, security scanner, AI reviewer, auto-fixer
- Modelo `Finding` con severity, category, suggested_fix
- Health score basado en findings reales con caps por severidad y desglose transparente
- Reportes rediseñados: HTML interactivo con dark theme, urgency gradient, highlights, anchors
- Formato Markdown para PRs de GitHub
- Comando `diagnose` como pipeline principal (`scan` es alias)
- `--fix` y `--dry-run` para aplicar fixes automaticamente
- `--severity` filtra findings en terminal, HTML y markdown
- `--top N` limita findings por grupo de severidad
- Exit code 1 cuando hay findings criticos (CI/CD)
- Deduplicacion de findings (mismo archivo + linea cercana + categoria)
- Category mini-summary por grupo de severidad
- Top Acciones con impact badges (ALTO IMPACTO / MEDIO) ordenadas por CC
- Fix: Tested Functions 0 → detecta funciones testeadas correctamente
- Fix: avg_complexity y total_loc calculados correctamente
- Fix: CC>10 consistente con threshold real
- Eliminados modulos `adaptation/`, `executor/`, `error_analyzer.py`
- 83 tests unitarios

### v0.1.0 (2026-02-03)
- Release inicial (prototipo tecnico, descartado por pivot)

---

## Notas para Claude

1. **Pipeline:** Detect -> Analyze -> Diagnose -> Report (4 pasos)
2. **No hay test generation/execution** — se eliminaron adaptation/ y executor/
3. **Finding es el modelo central** - todo se mapea a findings con fixes
4. **AI review usa tool_use** para output estructurado (no free-form text)
5. **Static findings no necesitan AI** - siempre disponibles
6. **Security scanner da line numbers** y distingue archivos test vs produccion
7. **Health score = findings, no test results** (con caps por severidad)
8. **JSON siempre tiene datos completos**, terminal/HTML/markdown se filtran por --severity
9. **Exit code 1** cuando hay findings criticos (para CI/CD)
10. **Engine procesa funciones POR IDIOMA** (lang_functions), no acumulativo — evita reset de is_tested
11. **_is_in_test_dir()** es safety net contra archivos de test en source analysis
12. **coverage_gap.py** usa 3 niveles de matching: patterns, cross-line regex (re.DOTALL), y function call detection
13. **TEST_PATTERNS** en constants.py es la fuente canonica de patrones de test files — los detectores deben usarlos
14. **Urgency gradient** en HTML: CC>=25 extreme (rojo), CC>=15 high (naranja)
15. **83 tests unitarios** cubren diagnosis, security scanner, static findings, auto-fixer, models, config
