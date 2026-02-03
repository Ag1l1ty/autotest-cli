# AutoTest CLI

Analizador automatico de proyectos de software. Detecta tecnologias, analiza codigo, genera tests con IA y ejecuta pruebas en multiples lenguajes.

## Caracteristicas

- **Detector de Proyecto**: Identifica automaticamente lenguajes (Python, JavaScript/TypeScript, Java, Go, Rust, C#), frameworks y herramientas de testing existentes
- **Analizador de Codigo**: Complejidad ciclomatica, acoplamiento entre modulos, funciones sin tests, codigo muerto
- **Motor de Adaptacion**: Seleccion automatica de test runners, cobertura y mocking por tecnologia. Generacion de tests con Claude API
- **Ejecutor de Pruebas**: 5 fases (smoke, unitarios, integracion, seguridad, calidad) con sandbox aislado
- **Generador de Reportes**: Terminal interactivo, JSON para CI/CD, HTML interactivo con codigo unico

## Instalacion

### Desde GitHub (recomendado)

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/autotest-cli.git
cd autotest-cli

# Instalar
pip install -e .
```

### Instalacion directa desde GitHub

```bash
pip install git+https://github.com/tu-usuario/autotest-cli.git
```

### Desarrollo local

```bash
# Clonar y entrar al directorio
git clone https://github.com/tu-usuario/autotest-cli.git
cd autotest-cli

# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar con dependencias de desarrollo
pip install -e ".[dev]"
```

## Uso Rapido

```bash
# Pipeline completo (genera reporte HTML automaticamente)
autotest scan ./mi-proyecto

# Pipeline completo y abrir reporte en navegador
autotest scan ./mi-proyecto --open

# Solo detectar tecnologias
autotest detect ./mi-proyecto

# Analizar codigo
autotest analyze ./mi-proyecto

# Generar estrategia + tests con IA
autotest generate ./mi-proyecto

# Ejecutar pruebas
autotest execute ./mi-proyecto
```

## Opciones

```bash
autotest scan ./mi-proyecto \
  --output terminal,json,html \
  --phases smoke,unit,integration,security,quality \
  --no-ai \
  --verbose \
  --fail-fast \
  --open  # Abrir HTML en navegador automaticamente
```

## Reportes

Los reportes se generan en el directorio `reports/` dentro del proyecto analizado:

```
mi-proyecto/
├── reports/
│   └── autotest-report-AT-20260203-A1B2C3.html
├── src/
└── ...
```

Cada reporte tiene un **codigo unico** con formato `AT-YYYYMMDD-XXXXXX` que aparece:
- En el nombre del archivo
- En el encabezado del reporte HTML
- En el footer del reporte

Al finalizar el scan, la terminal muestra la ruta completa del reporte:

```
╭─────────── Reportes Generados ────────────╮
│ HTML: /path/to/mi-proyecto/reports/autotest-report-AT-20260203-A1B2C3.html │
│ Report ID: AT-20260203-A1B2C3             │
╰───────────────────────────────────────────╯
```

## Configuracion

Crear archivo `.autotest.yaml` en la raiz del proyecto:

```yaml
phases:
  - smoke
  - unit
  - quality
output_formats:
  - terminal
  - json
ai_enabled: true
ai_model: claude-sonnet-4-20250514
complexity_threshold: 10
timeout_seconds: 300
```

O en `pyproject.toml`:

```toml
[tool.autotest]
phases = ["smoke", "unit", "quality"]
output_formats = ["terminal"]
```

## Requisitos

- Python 3.11 o superior
- API key de Anthropic (para generacion de tests con IA)

## Variables de Entorno

| Variable | Descripcion |
|----------|-------------|
| `AUTOTEST_AI_API_KEY` | API key de Anthropic para generacion con IA |
| `ANTHROPIC_API_KEY` | Alternativa: API key de Anthropic (si no existe AUTOTEST_AI_API_KEY) |
| `AUTOTEST_AI_MODEL` | Modelo de IA a usar (default: claude-sonnet-4-20250514) |
| `AUTOTEST_PHASES` | Fases a ejecutar separadas por coma |
| `AUTOTEST_VERBOSE` | Activar salida detallada (true/false) |

### Configurar API Key

```bash
# Opcion 1: Variable de entorno (recomendado)
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Opcion 2: Variable especifica de AutoTest
export AUTOTEST_AI_API_KEY="sk-ant-api03-..."

# Opcion 3: Ejecutar sin IA (solo tests existentes)
autotest scan ./mi-proyecto --no-ai
```

## Lenguajes Soportados

| Lenguaje | Test Runner | Cobertura | Mocking |
|----------|-------------|-----------|---------|
| Python | pytest | coverage.py | pytest-mock |
| JavaScript | jest/vitest | c8/istanbul | jest mocks |
| Java | JUnit 5 | JaCoCo | Mockito |
| Go | go test | go cover | testify |
| Rust | cargo test | tarpaulin | mockall |
| C# | dotnet test | coverlet | Moq |

## Fases de Ejecucion

1. **Smoke** - Compilacion, dependencias, puntos de entrada
2. **Unit** - Tests unitarios existentes + generados por IA
3. **Integration** - Tests de integracion (APIs, DB, servicios)
4. **Security** - Vulnerabilidades, secretos hardcodeados, .env files
5. **Quality** - Linting, tipos, complejidad

## Arquitectura

```
autotest scan ./proyecto
     |
     v
[1] Detector ──> ProjectInfo
     |
     v
[2] Analizador ──> AnalysisReport
     |
     v
[3] Motor de Adaptacion ──> TestStrategy
     |
     v
[4] Ejecutor ──> ExecutionReport
     |
     v
[5] Reportero ──> Terminal + JSON + HTML
```

## Desarrollo

```bash
# Instalar con deps de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Linting
ruff check src/

# Type checking
mypy src/
```

## Troubleshooting

### Error: "API key not found"
Asegurate de configurar la variable de entorno `ANTHROPIC_API_KEY` o `AUTOTEST_AI_API_KEY`.

### Error: "No se detectaron lenguajes soportados"
El directorio debe contener archivos de codigo fuente (.py, .js, .ts, .java, etc.)

### Los tests generados no pasan
Los tests generados por IA son un punto de partida. Puede que necesiten ajustes manuales para mocks o configuraciones especificas de tu proyecto.

### No encuentro el reporte HTML
Los reportes se guardan en `{tu-proyecto}/reports/`. Usa `--open` para abrirlo automaticamente en el navegador.

## Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/mi-feature`)
3. Commit tus cambios (`git commit -am 'Agrega mi feature'`)
4. Push a la rama (`git push origin feature/mi-feature`)
5. Abre un Pull Request

## Licencia

MIT
