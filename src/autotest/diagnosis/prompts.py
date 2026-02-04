"""Prompts and tool schemas for AI code review."""

from __future__ import annotations

REVIEW_SYSTEM_PROMPT = """\
Eres un revisor de codigo senior. Tu trabajo es encontrar bugs REALES, problemas \
de seguridad y errores de manejo de excepciones. Enfocate en problemas que causen \
fallos en runtime, corrupcion de datos o vulnerabilidades de seguridad.

IMPORTANTE: Responde SIEMPRE en español. Los campos title, description y \
fix_description deben estar en español.

Reglas:
- Solo reporta problemas con confianza >= 0.6.
- NO reportes problemas de estilo (nombres, formato) a menos que oculten un bug.
- NO reportes documentacion faltante.
- Para cada problema, da un fix concreto con code_before y code_after.
- Se especifico: incluye los numeros de linea exactos.
- Prefiere pocos hallazgos de alta calidad sobre muchos de baja confianza.
"""


def build_review_prompt(
    source_code: str,
    qualified_name: str,
    language: str,
    docstring: str | None,
    imports: list[str],
    parent_class_source: str,
    sibling_functions: list[str],
) -> str:
    """Build the user prompt for reviewing a function."""
    parts = [f"Revisa la siguiente funcion {language}: `{qualified_name}`\n"]

    if docstring:
        parts.append(f"Docstring: {docstring}\n")

    if imports:
        parts.append("Imports del modulo:\n```\n" + "\n".join(imports[:30]) + "\n```\n")

    if parent_class_source:
        parts.append(
            "Clase padre (contexto):\n```"
            + language
            + "\n"
            + parent_class_source
            + "\n```\n"
        )

    if sibling_functions:
        parts.append(
            "Otras funciones en el mismo modulo: "
            + ", ".join(sibling_functions[:15])
            + "\n"
        )

    parts.append(f"Codigo fuente de la funcion:\n```{language}\n{source_code}\n```\n")

    parts.append(
        "Encuentra bugs, problemas de seguridad, edge cases no manejados y "
        "problemas de manejo de errores. Usa la herramienta report_findings "
        "para reportar tus hallazgos. Responde en español."
    )

    return "\n".join(parts)


# Tool schema for structured output via Claude tool_use
REPORT_FINDINGS_TOOL = {
    "name": "report_findings",
    "description": (
        "Reportar hallazgos de la revision de codigo. "
        "Cada hallazgo debe ser un problema real con un fix concreto. "
        "Todos los textos deben estar en español."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "description": "Lista de problemas encontrados en el codigo",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "warning", "info"],
                            "description": "Severidad del problema",
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "bug",
                                "security",
                                "error_handling",
                                "complexity",
                                "style",
                            ],
                            "description": "Categoria del problema",
                        },
                        "title": {
                            "type": "string",
                            "description": "Titulo corto en español (una linea)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripcion detallada del problema en español",
                        },
                        "line_start": {
                            "type": "integer",
                            "description": "Numero de linea en la funcion donde inicia el problema",
                        },
                        "fix_description": {
                            "type": "string",
                            "description": "Que cambiar para arreglar el problema (en español)",
                        },
                        "code_before": {
                            "type": "string",
                            "description": "El fragmento de codigo problematico",
                        },
                        "code_after": {
                            "type": "string",
                            "description": "El fragmento de codigo corregido",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confianza en este hallazgo (0.0 a 1.0)",
                        },
                    },
                    "required": [
                        "severity",
                        "category",
                        "title",
                        "description",
                        "confidence",
                    ],
                },
            },
        },
        "required": ["findings"],
    },
}
