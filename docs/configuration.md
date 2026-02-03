# Configuracion de AutoTest CLI

## Fuentes de Configuracion (orden de precedencia)

1. Flags de CLI (mayor precedencia)
2. Variables de entorno (`AUTOTEST_*`)
3. `.autotest.yaml` en raiz del proyecto
4. `pyproject.toml` seccion `[tool.autotest]`
5. Valores por defecto

## Opciones de Configuracion

### Fases

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| phases | list[str] | ["smoke", "unit", "quality"] | Fases a ejecutar |
| fail_fast | bool | false | Detener en primera falla |

### Salida

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| output_formats | list[str] | ["terminal"] | Formatos: terminal, json, html |
| output_dir | Path | ./reports | Directorio de reportes |
| verbose | bool | false | Salida detallada |
| debug | bool | false | Modo debug |

### IA

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| ai_enabled | bool | true | Activar generacion con IA |
| ai_api_key | str | "" | API key de Anthropic |
| ai_model | str | claude-sonnet-4-20250514 | Modelo a usar |
| ai_max_functions | int | 20 | Max funciones a generar |
| ai_max_cost_usd | float | 5.0 | Limite de costo |

### Analisis

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| complexity_threshold | int | 10 | Umbral de complejidad alta |
| coupling_threshold | int | 8 | Umbral de acoplamiento alto |

### Ejecucion

| Opcion | Tipo | Default | Descripcion |
|--------|------|---------|-------------|
| timeout_seconds | int | 300 | Timeout por comando |
| parallel | bool | true | Ejecucion paralela |
| sandbox_enabled | bool | true | Sandbox para tests |
