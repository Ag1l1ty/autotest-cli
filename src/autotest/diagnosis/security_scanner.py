"""Security scanner for hardcoded secrets with exact line numbers."""

from __future__ import annotations

import re
from pathlib import Path

from autotest.models.diagnosis import (
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)

# Reused from executor/phases/security.py with same patterns
SECRET_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9]{16,}",
        "API key hardcodeada",
        "Mover a variable de entorno",
    ),
    (
        r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}",
        "Secreto hardcodeado",
        "Mover a variable de entorno o vault",
    ),
    (
        r"(?i)(aws_access_key_id)\s*[:=]\s*['\"]?AKIA[A-Z0-9]{16}",
        "AWS access key expuesta",
        "Usar IAM roles o AWS Secrets Manager",
    ),
    (
        r"(?i)(private[_-]?key)\s*[:=]\s*['\"]-----BEGIN",
        "Clave privada embebida",
        "Mover a archivo seguro fuera del repositorio",
    ),
    (
        r"(?i)(token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}",
        "Token hardcodeado",
        "Usar variable de entorno",
    ),
    (
        r"jdbc:[a-z]+://[^:]+:[^@]+@",
        "Connection string con credenciales",
        "Usar variables de entorno para credenciales de base de datos",
    ),
]

_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv", "dist", "build", ".tox", ".nox"}

_TEST_INDICATORS = {"tests", "test", "__tests__", "spec", "fixtures", "conftest"}

_SCANNABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cs",
    ".yaml", ".yml", ".json", ".toml", ".env", ".cfg", ".ini",
}


def _is_test_file(path: Path) -> bool:
    """Check if a file is inside a test directory or is a test file."""
    parts = {p.lower() for p in path.parts}
    if parts & _TEST_INDICATORS:
        return True
    name = path.stem.lower()
    return (
        name.startswith("test_")
        or name.endswith("_test")
        or name.endswith(".test")
        or name.endswith(".spec")
    )


def scan_for_secrets(project_root: Path) -> list[Finding]:
    """Scan project files for hardcoded secrets.

    Returns Finding objects with exact file path and line number.
    """
    findings: list[Finding] = []

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in _SKIP_DIRS):
            continue
        if path.suffix not in _SCANNABLE_EXTENSIONS:
            continue

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (PermissionError, OSError):
            continue

        relative = str(path.relative_to(project_root))
        is_test = _is_test_file(path)

        for line_num, line_text in enumerate(lines, start=1):
            for pattern, label, fix_desc in SECRET_PATTERNS:
                if re.search(pattern, line_text):
                    env_var_name = _suggest_env_var(label, line_text)

                    # Test files get INFO severity (mock values, not real secrets)
                    if is_test:
                        severity = Severity.INFO
                        title = f"{label} en test: {Path(relative).name}:{line_num}"
                        description = (
                            f"Posible {label.lower()} en archivo de test "
                            f"{relative} linea {line_num}. "
                            f"Verificar que sea un valor mock y no un secreto real."
                        )
                        confidence = 0.4
                    else:
                        severity = Severity.CRITICAL
                        title = f"{label} en {Path(relative).name}:{line_num}"
                        description = (
                            f"Se encontro un posible {label.lower()} en "
                            f"{relative} linea {line_num}. "
                            f"Los secretos hardcodeados pueden exponerse en el repositorio."
                        )
                        confidence = 0.85

                    if is_test:
                        suggested_fix = SuggestedFix(
                            description="Verificar que sea un valor mock, no un secreto real",
                            explanation=(
                                "En archivos de test es normal usar valores mock hardcodeados. "
                                "Solo asegurate de que no sea un secreto real de produccion."
                            ),
                        )
                    else:
                        suggested_fix = SuggestedFix(
                            description=fix_desc,
                            code_before=line_text.strip(),
                            code_after=f'{env_var_name} = os.environ["{env_var_name}"]',
                            explanation=(
                                "Los secretos nunca deben estar en el codigo fuente. "
                                "Usar variables de entorno o un gestor de secretos."
                            ),
                        )

                    findings.append(Finding(
                        severity=severity,
                        category=FindingCategory.SECURITY,
                        title=title,
                        description=description,
                        file_path=relative,
                        line_start=line_num,
                        line_end=line_num,
                        suggested_fix=suggested_fix,
                        confidence=confidence,
                        source="security",
                    ))
                    break  # One finding per line is enough

    return findings


def _suggest_env_var(label: str, line: str) -> str:
    """Suggest an environment variable name based on the finding."""
    # Try to extract the variable name from the line
    match = re.search(r"(\w+)\s*[:=]", line)
    if match:
        return match.group(1).upper()
    # Fallback based on label
    label_map = {
        "API key hardcodeada": "API_KEY",
        "Secreto hardcodeado": "SECRET_KEY",
        "AWS access key expuesta": "AWS_ACCESS_KEY_ID",
        "Clave privada embebida": "PRIVATE_KEY_PATH",
        "Token hardcodeado": "AUTH_TOKEN",
        "Connection string con credenciales": "DATABASE_URL",
    }
    return label_map.get(label, "SECRET_VALUE")
