# Configuracion de AutoTest CLI

## Version
v0.1.0

## Fuentes de Configuracion (orden de precedencia)

1. **Flags de CLI** (mayor precedencia)
2. **Variables de entorno** (`AUTOTEST_*` o `ANTHROPIC_API_KEY`)
3. **`.autotest.yaml`** en raiz del proyecto
4. **`pyproject.toml`** seccion `[tool.autotest]`
5. **Valores por defecto**

## Opciones de Configuracion

### Fases de Ejecucion

| Opcion | Tipo | Default | CLI Flag | Descripcion |
|--------|------|---------|----------|-------------|
| phases | list[str] | ["smoke", "unit", "integration", "quality"] | `--phases`, `-p` | Fases a ejecutar |
| fail_fast | bool | false | `--fail-fast` | Detener en primera falla |

**Fases disponibles:**
- `smoke` - Compilacion, dependencias, entry points
- `unit` - Tests unitarios existentes + generados
- `integration` - Tests de integracion con mocks
- `security` - Vulnerabilidades, secretos
- `quality` - Linting, tipos, complejidad

### Salida y Reportes

| Opcion | Tipo | Default | CLI Flag | Descripcion |
|--------|------|---------|----------|-------------|
| output_formats | list[str] | ["terminal", "html"] | `--output`, `-o` | Formatos de reporte |
| output_dir | Path | {proyecto}/reports | - | Directorio de reportes |
| verbose | bool | false | `--verbose` | Salida detallada |
| open_report | bool | false | `--open` | Abrir HTML en navegador |

**Formatos disponibles:**
- `terminal` - Salida Rich en consola
- `json` - JSON para CI/CD
- `html` - HTML interactivo con ID unico

### Inteligencia Artificial

| Opcion | Tipo | Default | ENV | Descripcion |
|--------|------|---------|-----|-------------|
| ai_enabled | bool | true | - | Activar generacion con IA |
| ai_api_key | str | "" | `AUTOTEST_AI_API_KEY` o `ANTHROPIC_API_KEY` | API key de Anthropic |
| ai_model | str | claude-sonnet-4-20250514 | `AUTOTEST_AI_MODEL` | Modelo a usar |
| ai_max_functions | int | 20 | - | Max funciones a generar |
| ai_max_cost_usd | float | 5.0 | - | Limite de costo estimado |

### Analisis de Codigo

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| complexity_threshold | int | 10 | Umbral de complejidad alta |
| coupling_threshold | int | 8 | Umbral de acoplamiento alto |

### Ejecucion

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| timeout_seconds | int | 300 | Timeout por comando |
| parallel | bool | true | Ejecucion paralela |
| sandbox_enabled | bool | true | Sandbox para tests generados |

---

## Ejemplos de Configuracion

### .autotest.yaml (recomendado)

```yaml
# Fases a ejecutar
phases:
  - smoke
  - unit
  - integration
  - quality

# Formatos de salida
output_formats:
  - terminal
  - html

# Configuracion de IA
ai_enabled: true
ai_model: claude-sonnet-4-20250514
ai_max_functions: 30

# Umbrales de analisis
complexity_threshold: 10
coupling_threshold: 8

# Ejecucion
timeout_seconds: 300
fail_fast: false
verbose: false
```

### pyproject.toml

```toml
[tool.autotest]
phases = ["smoke", "unit", "integration", "quality"]
output_formats = ["terminal", "html"]
ai_enabled = true
ai_model = "claude-sonnet-4-20250514"
complexity_threshold = 10
timeout_seconds = 300
```

---

## Variables de Entorno

| Variable | Descripcion | Ejemplo |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key de Anthropic (preferido) | `sk-ant-api03-...` |
| `AUTOTEST_AI_API_KEY` | API key alternativa | `sk-ant-api03-...` |
| `AUTOTEST_AI_MODEL` | Modelo de IA | `claude-sonnet-4-20250514` |
| `AUTOTEST_PHASES` | Fases separadas por coma | `smoke,unit,quality` |
| `AUTOTEST_VERBOSE` | Modo verbose | `true` |
| `AUTOTEST_OUTPUT_FORMATS` | Formatos de salida | `terminal,html,json` |

### Configurar API Key

```bash
# Opcion 1: Variable de entorno permanente (agregar a ~/.bashrc o ~/.zshrc)
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Opcion 2: Solo para la sesion actual
ANTHROPIC_API_KEY="sk-ant-api03-..." autotest scan ./mi-proyecto

# Opcion 3: Sin IA
autotest scan ./mi-proyecto --no-ai
```

---

## Flags de CLI

### Comando `scan` (pipeline completo)

```bash
autotest scan <PATH> [OPTIONS]

Argumentos:
  PATH                    Ruta al proyecto (default: .)

Opciones:
  -c, --config PATH       Archivo de configuracion
  -o, --output TEXT       Formatos: terminal,json,html (default: terminal,html)
  -p, --phases TEXT       Fases: smoke,unit,integration,security,quality
  --no-ai                 Desactivar generacion con IA
  --verbose               Salida detallada
  --fail-fast             Detener en primera falla
  --open                  Abrir reporte HTML en navegador
  -v, --version           Mostrar version
  --help                  Mostrar ayuda
```

### Ejemplos de uso

```bash
# Pipeline completo con defaults
autotest scan ./mi-proyecto

# Abrir reporte automaticamente
autotest scan ./mi-proyecto --open

# Solo fases rapidas, sin IA
autotest scan ./mi-proyecto --phases smoke,unit --no-ai

# Modo verbose con JSON
autotest scan ./mi-proyecto --verbose --output terminal,json

# Usando archivo de configuracion
autotest scan ./mi-proyecto --config .autotest.prod.yaml

# Solo security scan
autotest scan ./mi-proyecto --phases security --no-ai
```

---

## Perfiles de Configuracion (sugerencia)

Puedes crear multiples archivos de configuracion para diferentes contextos:

### .autotest.dev.yaml
```yaml
phases: [smoke, unit]
ai_enabled: true
verbose: true
output_formats: [terminal]
```

### .autotest.ci.yaml
```yaml
phases: [smoke, unit, integration, quality]
ai_enabled: false
fail_fast: true
output_formats: [json]
timeout_seconds: 600
```

### .autotest.thorough.yaml
```yaml
phases: [smoke, unit, integration, security, quality]
ai_enabled: true
ai_max_functions: 50
output_formats: [terminal, html, json]
complexity_threshold: 8
```

Usar con:
```bash
autotest scan ./proyecto --config .autotest.ci.yaml
```

---

## Ubicacion de Reportes

Los reportes se generan en `{proyecto}/reports/`:

```
mi-proyecto/
├── reports/
│   ├── autotest-report-AT-20260203-A1B2C3.html
│   ├── autotest-report-AT-20260203-A1B2C3.json
│   └── ...
├── src/
└── ...
```

Cada reporte tiene un ID unico con formato `AT-YYYYMMDD-XXXXXX` que permite:
- Identificar reportes historicos
- Referenciar en issues/PRs
- Comparar ejecuciones

---

## Integracion con CI/CD

### GitHub Actions

```yaml
name: AutoTest
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install AutoTest
        run: pip install git+https://github.com/Ag1l1ty/autotest-cli.git

      - name: Run AutoTest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: autotest scan . --output json --fail-fast

      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: autotest-report
          path: reports/
```

### GitLab CI

```yaml
autotest:
  image: python:3.11
  script:
    - pip install git+https://github.com/Ag1l1ty/autotest-cli.git
    - autotest scan . --output json --fail-fast
  artifacts:
    paths:
      - reports/
    expire_in: 1 week
```
