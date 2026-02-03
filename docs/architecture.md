# Arquitectura de AutoTest CLI

## Vision General

AutoTest CLI es una herramienta de linea de comandos que analiza proyectos de software automaticamente,
identifica tecnologias, analiza calidad del codigo, y ejecuta/genera pruebas.

## Modulos

### 1. Detector de Proyecto (`detector/`)

**Responsabilidad**: Escanear el directorio del proyecto e identificar tecnologias.

- `BaseLanguageDetector` (ABC) - Interfaz para detectores
- `DetectorRegistry` - Registro con decorador `@register`
- `ProjectScanner` - Orquestador que ejecuta todos los detectores
- 6 detectores: Python, JavaScript, Java, Go, Rust, C#

**Produce**: `ProjectInfo`

**Patron**: Strategy + Registry

### 2. Analizador de Codigo (`analyzer/`)

**Responsabilidad**: Analizar la estructura del codigo para entender metricas.

- `AnalysisEngine` - Orquestador async
- Parsers por lenguaje (AST para Python, regex para el resto)
- 4 analizadores: complejidad, acoplamiento, coverage gaps, codigo muerto

**Consume**: `ProjectInfo`
**Produce**: `AnalysisReport`

**Patron**: Template Method + Strategy

### 3. Motor de Adaptacion (`adaptation/`)

**Responsabilidad**: Seleccionar herramientas y generar tests.

- `AdaptationEngine` - Orquestador
- Toolchains por lenguaje (configuran comandos de test/coverage/mock)
- `AITestGenerator` - Generacion de tests via Claude API
- `GeneratedTestValidator` - Validacion de seguridad y sintaxis

**Consume**: `ProjectInfo` + `AnalysisReport`
**Produce**: `TestStrategy`

**Patron**: Abstract Factory + Adapter

### 4. Ejecutor de Pruebas (`executor/`)

**Responsabilidad**: Ejecutar tests en fases con sandbox aislado.

- `ExecutionEngine` - Orquestador con secuenciamiento
- `TestSandbox` - Directorio temporal para ejecucion segura
- `SubprocessRunner` - Ejecucion async de comandos
- 5 fases: Smoke, Unit, Integration, Security, Quality

**Consume**: `TestStrategy`
**Produce**: `ExecutionReport`

**Patron**: Chain of Responsibility + Template Method

### 5. Generador de Reportes (`reporter/`)

**Responsabilidad**: Generar reportes en multiples formatos.

- `ReportEngine` - Orquestador
- `TerminalReporter` - Salida Rich con tablas y paneles
- `JSONReporter` - JSON serializado con Pydantic
- `HTMLReporter` - HTML interactivo con Jinja2

**Consume**: Todos los modelos anteriores
**Produce**: `ReportData` + archivos de reporte

**Patron**: Strategy + Template Method

## Flujo de Datos

```
CLI (Typer)
  -> AutoTestConfig (Pydantic Settings)
  -> ProjectScanner -> ProjectInfo
  -> AnalysisEngine -> AnalysisReport
  -> AdaptationEngine -> TestStrategy
  -> ExecutionEngine -> ExecutionReport
  -> ReportEngine -> ReportData -> Terminal/JSON/HTML
```

## Modelos (Contratos)

Todos los modelos estan en `models/` como Pydantic v2 BaseModel.
Esto garantiza:
- Validacion automatica de datos
- Serializacion JSON nativa
- Inmutabilidad por defecto
- Type safety

## Extensibilidad

### Agregar un nuevo lenguaje:
1. Crear detector en `detector/languages/nuevo.py`
2. Usar `@register("nuevo")` 
3. Crear parser en `analyzer/parsers/nuevo_parser.py`
4. Crear toolchain en `adaptation/toolchains/nuevo_tools.py`
5. Agregar prompts en `adaptation/ai/prompts.py`

### Agregar una nueva fase:
1. Crear ejecutor en `executor/phases/nueva_fase.py`
2. Implementar `BasePhaseExecutor`
3. Registrar en `executor/engine.py` PHASE_EXECUTORS
4. Agregar a `TestPhase` enum
