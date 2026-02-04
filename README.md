# Code Doctor (AutoTest CLI)

Diagnostico inteligente de proyectos de software. Encuentra problemas reales y da fixes concretos y accionables.

## Que hace

- **Detecta** lenguajes, frameworks y herramientas del proyecto
- **Analiza** complejidad, acoplamiento, funciones sin tests, codigo muerto
- **Diagnostica** bugs, problemas de seguridad, edge cases no manejados
- **Reporta** findings priorizados con fixes copy-pasteables

```
Code Doctor: mi-proyecto
Health Score: 72/100 (MODERATE)

CRITICAL (2)
CD-001  security    config.py:12     API key hardcodeada
                    Fix: Mover a variable de entorno
                    >>> SUPABASE_KEY = os.environ["SUPABASE_KEY"]

CD-002  bug         process.py:45    Posible NullPointerException
                    Fix: Agregar validacion
                    >>> if response is None:
                    >>>     raise ValueError("API returned None")

WARNING (3)
CD-003  complexity  utils.py:80      Complejidad alta en transform_data() — CC=15
CD-004  missing_tests core.py:10     Funcion critica sin tests: calculate_score()

Top 3 acciones:
1. Mover API key a variable de entorno en config.py:12
2. Arreglar NullPointerException en process.py:45
3. Descomponer transform_data() en utils.py:80
```

## Instalacion

```bash
# Desde GitHub
pip install git+https://github.com/Ag1l1ty/autotest-cli.git

# Desarrollo local
git clone https://github.com/Ag1l1ty/autotest-cli.git
cd autotest-cli
pip install -e ".[dev]"
```

## Uso Rapido

```bash
# Diagnostico completo con reporte HTML
autotest diagnose ./mi-proyecto --open

# Solo hallazgos estaticos (sin IA)
autotest diagnose ./mi-proyecto --no-ai

# Solo problemas criticos
autotest diagnose ./mi-proyecto --severity critical

# Alias: scan = diagnose
autotest scan ./mi-proyecto --open

# Solo detectar tecnologias
autotest detect ./mi-proyecto

# Solo analizar codigo
autotest analyze ./mi-proyecto
```

## Opciones

```bash
autotest diagnose ./mi-proyecto \
  --output terminal,json,html \
  --severity critical,warning,info \
  --top 10 \
  --no-ai \
  --verbose \
  --open
```

| Opcion | Descripcion |
|--------|-------------|
| `--output` | Formatos de salida: terminal, json, html (default: terminal,html) |
| `--severity` | Severidades a mostrar: critical, warning, info (default: critical,warning) |
| `--top` | Numero de acciones prioritarias (default: 5) |
| `--no-ai` | Desactivar revision con IA |
| `--verbose` | Salida detallada |
| `--open` | Abrir reporte HTML en navegador |

## Reportes

Los reportes se generan en `{proyecto}/reports/`:

```
mi-proyecto/
├── reports/
│   └── autotest-report-AT-20260203-A1B2C3.html
├── src/
└── ...
```

Cada reporte tiene un codigo unico `AT-YYYYMMDD-XXXXXX`.

## Tipos de Findings

| Categoria | Descripcion |
|-----------|-------------|
| `security` | Secretos hardcodeados, vulnerabilidades |
| `bug` | Bugs potenciales, NullPointer, race conditions |
| `error_handling` | Errores no manejados, excepciones silenciadas |
| `complexity` | Funciones con alta complejidad ciclomatica |
| `coupling` | Modulos con alto acoplamiento |
| `missing_tests` | Funciones criticas sin tests |
| `dead_code` | Funciones no referenciadas |

## Health Score

| Rango | Label | Significado |
|-------|-------|-------------|
| 80-100 | HEALTHY | Codigo en buen estado |
| 60-79 | MODERATE | Algunos problemas a resolver |
| 40-59 | AT-RISK | Problemas significativos |
| 0-39 | CRITICAL | Requiere atencion urgente |

## Configuracion

Crear archivo `.autotest.yaml` en la raiz del proyecto:

```yaml
ai_enabled: true
ai_model: claude-sonnet-4-20250514
ai_max_functions: 10
min_finding_confidence: 0.6
severity_filter:
  - critical
  - warning
top_findings: 5
output_formats:
  - terminal
  - html
```

## Variables de Entorno

| Variable | Descripcion |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Anthropic para revision con IA |
| `AUTOTEST_AI_API_KEY` | Alternativa para API key |
| `AUTOTEST_AI_MODEL` | Modelo de IA (default: claude-sonnet-4-20250514) |

```bash
# Configurar API key para revision con IA
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# O ejecutar sin IA (solo analisis estatico)
autotest diagnose ./mi-proyecto --no-ai
```

## Lenguajes Soportados

Python, JavaScript, TypeScript, Java, Go, Rust, C#

## Arquitectura

```
autotest diagnose ./proyecto
     |
     v
[1] Detector ──> ProjectInfo
     |
     v
[2] Analizador ──> AnalysisReport
     |
     v
[3] Diagnostico
     ├── Static Findings (complejidad, dead code, coupling)
     ├── Security Scanner (secretos con linea exacta)
     └── AI Reviewer (bugs, edge cases) [opcional]
     |
     v
[4] Reportero ──> Terminal + JSON + HTML
```

## Requisitos

- Python 3.11 o superior
- API key de Anthropic (opcional, para revision con IA)

## Licencia

MIT
