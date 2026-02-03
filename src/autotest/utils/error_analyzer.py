"""Error analyzer - Parses test errors and generates actionable recommendations."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ErrorAnalysis:
    """Analyzed error with category and recommendation."""

    category: str  # import, mock, assertion, syntax, timeout, dependency, unknown
    summary: str  # Short description of the error
    file_path: str | None  # File where error occurred
    line_number: int | None  # Line number
    recommendation: str  # Actionable fix suggestion
    code_snippet: str | None  # Relevant code if available


class TestErrorAnalyzer:
    """Analyzes test failures and provides actionable recommendations."""

    # Error patterns with (regex, category, recommendation_template)
    PATTERNS = [
        # Import errors
        (
            r"ModuleNotFoundError: No module named ['\"](\w+)['\"]",
            "import",
            "Módulo '{0}' no encontrado. Instalar con: pip install {0}",
        ),
        (
            r"ImportError: cannot import name ['\"](\w+)['\"] from ['\"]([^'\"]+)['\"]",
            "import",
            "No se puede importar '{0}' de '{1}'. Verificar que la clase/función existe y está exportada.",
        ),
        (
            r"ModuleNotFoundError: No module named ['\"]([^'\"\.]+)\.([^'\"]+)['\"]",
            "import",
            "Módulo '{0}.{1}' no encontrado. Agregar al PYTHONPATH o verificar estructura de paquetes.",
        ),

        # Mock/Patch errors
        (
            r"AttributeError: <module ['\"]([^'\"]+)['\"].*has no attribute ['\"](\w+)['\"]",
            "mock",
            "El módulo '{0}' no tiene '{1}'. El patch debe usar la ruta donde se IMPORTA, no donde se define. "
            "Cambiar a: @patch('{0}.{1}')",
        ),
        (
            r"assert.*mock.*call|AssertionError.*Expected call|assert_called|call_count",
            "mock",
            "El mock no fue llamado como se esperaba. Verificar: 1) El patch usa la ruta correcta "
            "(donde se importa, no donde se define), 2) La función realmente llama al código mockeado.",
        ),
        (
            r"patch\(['\"]([^'\"]+)['\"]\)",
            "mock",
            "Verificar que el path del patch '{0}' sea donde se IMPORTA el objeto, no donde se define.",
        ),

        # Assertion errors
        (
            r"AssertionError: assert (\S+) == (\S+)",
            "assertion",
            "Valor esperado {1}, pero se recibió {0}. Revisar la lógica de la función o actualizar el test.",
        ),
        (
            r"AssertionError: (\d+) ([!=<>]+) (\d+)",
            "assertion",
            "Comparación falló: {0} {1} {2}. Verificar valores esperados.",
        ),
        (
            r"AssertionError$|AssertionError:",
            "assertion",
            "Aserción falló. Revisar los valores esperados vs los valores actuales en el test.",
        ),

        # Fixture/Setup errors
        (
            r"fixture ['\"](\w+)['\"] not found",
            "fixture",
            "Fixture '{0}' no encontrado. Definirlo en conftest.py o en el mismo archivo de test.",
        ),
        (
            r"ScopeMismatch.*fixture ['\"](\w+)['\"]",
            "fixture",
            "Conflicto de scope en fixture '{0}'. Verificar que los scopes sean compatibles.",
        ),

        # Type errors
        (
            r"TypeError: (\w+)\(\) got an unexpected keyword argument ['\"](\w+)['\"]",
            "type",
            "La función '{0}' no acepta el argumento '{1}'. Verificar la firma de la función.",
        ),
        (
            r"TypeError: (\w+)\(\) missing (\d+) required positional argument",
            "type",
            "La función '{0}' requiere {1} argumento(s) más. Agregar los parámetros faltantes.",
        ),
        (
            r"TypeError: (\w+)\(\) takes (\d+) positional arguments? but (\d+) (?:was|were) given",
            "type",
            "La función '{0}' espera {1} argumento(s) pero recibió {2}. Ajustar la llamada.",
        ),

        # Attribute errors
        (
            r"AttributeError: ['\"]?(\w+)['\"]? object has no attribute ['\"](\w+)['\"]",
            "attribute",
            "El objeto '{0}' no tiene el atributo '{1}'. Verificar que el mock retorna el tipo correcto.",
        ),
        (
            r"AttributeError: ['\"]NoneType['\"] object has no attribute ['\"](\w+)['\"]",
            "attribute",
            "Se recibió None cuando se esperaba un objeto con '{0}'. Verificar que el mock retorna un valor.",
        ),

        # Connection/Network errors
        (
            r"ConnectionError|ConnectionRefusedError|requests\.exceptions\.",
            "network",
            "Error de conexión. El test intenta conectar a un servicio real. Agregar mock para las llamadas HTTP.",
        ),
        (
            r"socket\.timeout|TimeoutError|ReadTimeout",
            "timeout",
            "Timeout de conexión. Mockear las llamadas de red o aumentar el timeout.",
        ),

        # Syntax errors
        (
            r"SyntaxError: (.+)",
            "syntax",
            "Error de sintaxis: {0}. Revisar el código generado.",
        ),
        (
            r"IndentationError: (.+)",
            "syntax",
            "Error de indentación: {0}. Verificar espacios/tabs en el código.",
        ),

        # File errors
        (
            r"FileNotFoundError: \[Errno 2\] No such file or directory: ['\"]([^'\"]+)['\"]",
            "file",
            "Archivo no encontrado: '{0}'. Crear el archivo o mockear la lectura.",
        ),
        (
            r"PermissionError: \[Errno 13\] Permission denied",
            "file",
            "Sin permisos para acceder al archivo. Mockear las operaciones de archivo.",
        ),

        # Environment errors
        (
            r"KeyError: ['\"](\w+)['\"].*environ|os\.environ\[['\"](\w+)['\"]\]",
            "environment",
            "Variable de entorno '{0}' no definida. Agregar al mock o definir en el test.",
        ),

        # Database errors
        (
            r"OperationalError.*connect|psycopg2|sqlite3|mysql",
            "database",
            "Error de conexión a base de datos. Mockear las conexiones en los tests.",
        ),

        # API/HTTP errors
        (
            r"HTTPError|status.code.*[45]\d\d|response\.status_code",
            "api",
            "Error de respuesta HTTP. Verificar que el mock retorna el status code esperado.",
        ),
    ]

    @classmethod
    def analyze(cls, error_text: str, stdout: str = "") -> ErrorAnalysis:
        """Analyze error text and return structured analysis."""
        combined = f"{error_text}\n{stdout}"

        # Try to extract file and line info
        file_path, line_number = cls._extract_location(combined)

        # Match against patterns
        for pattern, category, rec_template in cls.PATTERNS:
            match = re.search(pattern, combined, re.IGNORECASE | re.MULTILINE)
            if match:
                # Format recommendation with captured groups
                try:
                    recommendation = rec_template.format(*match.groups())
                except (IndexError, KeyError):
                    recommendation = rec_template

                return ErrorAnalysis(
                    category=category,
                    summary=cls._extract_summary(combined, category),
                    file_path=file_path,
                    line_number=line_number,
                    recommendation=recommendation,
                    code_snippet=cls._extract_code_snippet(combined),
                )

        # Default unknown error
        return ErrorAnalysis(
            category="unknown",
            summary=cls._extract_summary(combined, "unknown"),
            file_path=file_path,
            line_number=line_number,
            recommendation="Revisar el error completo en los logs. Puede requerir depuración manual.",
            code_snippet=cls._extract_code_snippet(combined),
        )

    @classmethod
    def _extract_location(cls, text: str) -> tuple[str | None, int | None]:
        """Extract file path and line number from error text."""
        # Pattern: File "path/to/file.py", line 123
        match = re.search(r'File ["\']([^"\']+)["\'], line (\d+)', text)
        if match:
            return match.group(1), int(match.group(2))

        # Pattern: path/to/file.py:123
        match = re.search(r'([\w/\\_.-]+\.py):(\d+)', text)
        if match:
            return match.group(1), int(match.group(2))

        return None, None

    @classmethod
    def _extract_summary(cls, text: str, category: str) -> str:
        """Extract a short summary of the error."""
        # Get first meaningful error line
        for line in text.split('\n'):
            line = line.strip()
            if any(err in line for err in ['Error:', 'Error', 'FAILED', 'assert']):
                return line[:150]

        # Fallback to category-based summary
        summaries = {
            "import": "Error de importación de módulo",
            "mock": "Error en configuración de mock",
            "assertion": "Aserción de test falló",
            "fixture": "Error en fixture de pytest",
            "type": "Error de tipo de datos",
            "attribute": "Atributo no encontrado",
            "network": "Error de conexión de red",
            "timeout": "Timeout en operación",
            "syntax": "Error de sintaxis",
            "file": "Error de acceso a archivo",
            "environment": "Variable de entorno faltante",
            "database": "Error de base de datos",
            "api": "Error de respuesta HTTP",
            "unknown": "Error no categorizado",
        }
        return summaries.get(category, "Error desconocido")

    @classmethod
    def _extract_code_snippet(cls, text: str) -> str | None:
        """Extract relevant code snippet from error."""
        # Look for code blocks with > or E markers (pytest style)
        lines = []
        in_code = False

        for line in text.split('\n'):
            if line.strip().startswith('>') or line.strip().startswith('E '):
                in_code = True
                lines.append(line)
            elif in_code and line.strip() and not line.startswith(' '):
                break

        if lines:
            return '\n'.join(lines[:5])  # Max 5 lines
        return None

    @classmethod
    def get_fix_priority(cls, category: str) -> int:
        """Return fix priority (lower = fix first)."""
        priorities = {
            "syntax": 1,
            "import": 2,
            "environment": 3,
            "mock": 4,
            "fixture": 5,
            "type": 6,
            "attribute": 7,
            "assertion": 8,
            "network": 9,
            "database": 10,
            "api": 11,
            "file": 12,
            "timeout": 13,
            "unknown": 99,
        }
        return priorities.get(category, 50)


def analyze_test_results(test_results: list) -> list[dict]:
    """Analyze a list of test results and return detailed analysis."""
    analyses = []

    for test in test_results:
        if not test.passed and (test.error_message or test.stderr or test.stdout):
            error_text = test.error_message or test.stderr or ""
            analysis = TestErrorAnalyzer.analyze(error_text, test.stdout)

            analyses.append({
                "test_name": test.name,
                "analysis": analysis,
                "priority": TestErrorAnalyzer.get_fix_priority(analysis.category),
            })

    # Sort by priority
    analyses.sort(key=lambda x: x["priority"])
    return analyses


def generate_actionable_recommendations(analyses: list[dict]) -> list[str]:
    """Generate unique, actionable recommendations from analyses."""
    seen = set()
    recommendations = []

    # Group by category for better organization
    by_category: dict[str, list] = {}
    for item in analyses:
        cat = item["analysis"].category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    # Category descriptions
    category_headers = {
        "import": "Problemas de Importación",
        "mock": "Configuración de Mocks",
        "assertion": "Aserciones Fallidas",
        "fixture": "Fixtures de Pytest",
        "type": "Errores de Tipo",
        "attribute": "Atributos No Encontrados",
        "network": "Conexiones de Red",
        "database": "Base de Datos",
        "api": "Respuestas HTTP",
        "syntax": "Errores de Sintaxis",
        "file": "Acceso a Archivos",
        "environment": "Variables de Entorno",
    }

    # Priority order
    priority_order = ["syntax", "import", "environment", "mock", "fixture",
                      "type", "attribute", "assertion", "network", "database",
                      "api", "file", "timeout", "unknown"]

    for category in priority_order:
        if category not in by_category:
            continue

        items = by_category[category]
        header = category_headers.get(category, category.title())

        # Add category header
        if len(items) >= 1:
            recommendations.append(f"**{header}** ({len(items)} tests):")

        # Add unique recommendations
        for item in items:
            rec = item["analysis"].recommendation
            if rec not in seen:
                seen.add(rec)
                test_name = item["test_name"].split(":")[-1]  # Short name
                recommendations.append(f"  • [{test_name}] {rec}")

    return recommendations
