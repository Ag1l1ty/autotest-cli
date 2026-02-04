"""Convert analysis data into structured Finding objects."""

from __future__ import annotations

from autotest.constants import COMPLEXITY_HIGH, COMPLEXITY_MEDIUM, COMPLEXITY_VERY_HIGH
from autotest.models.analysis import AnalysisReport, FunctionMetrics
from autotest.models.diagnosis import (
    Finding,
    FindingCategory,
    Severity,
    SuggestedFix,
)


def generate_static_findings(analysis: AnalysisReport) -> list[Finding]:
    """Convert AnalysisReport data into Finding objects.

    Produces findings from:
    - High complexity functions
    - Dead code functions
    - Coupling issues
    - Untested functions with high complexity
    """
    findings: list[Finding] = []
    findings.extend(_complexity_findings(analysis))
    findings.extend(_dead_code_findings(analysis))
    findings.extend(_coupling_findings(analysis))
    findings.extend(_missing_tests_findings(analysis))
    return findings


def _complexity_findings(analysis: AnalysisReport) -> list[Finding]:
    findings: list[Finding] = []
    for func in analysis.high_complexity_functions:
        cc = func.cyclomatic_complexity
        lines = max(func.line_end - func.line_start + 1, 1)
        severity = Severity.CRITICAL if cc >= COMPLEXITY_VERY_HIGH else (
            Severity.CRITICAL if cc >= COMPLEXITY_HIGH * 2 else Severity.WARNING
        )
        findings.append(Finding(
            severity=severity,
            category=FindingCategory.COMPLEXITY,
            title=f"Complejidad alta en {func.name}() — CC={cc}",
            description=(
                f"La funcion {func.qualified_name} tiene complejidad ciclomatica {cc} "
                f"({lines} lineas, L{func.line_start}-L{func.line_end}). "
                f"Funciones con CC>{COMPLEXITY_MEDIUM} son dificiles de testear y mantener."
            ),
            file_path=str(func.file_path),
            line_start=func.line_start,
            line_end=func.line_end,
            function_name=func.name,
            qualified_name=func.qualified_name,
            language=func.language.value,
            suggested_fix=SuggestedFix(
                description=f"Descomponer {func.name}() ({lines} lineas, CC={cc})",
                code_before=f"def {func.name}(...)  # {lines} lineas, CC={cc}",
                explanation=(
                    f"{func.qualified_name} abarca L{func.line_start}-L{func.line_end}. "
                    f"Extraer bloques logicos en funciones auxiliares para reducir "
                    f"la complejidad de {cc} a menos de {COMPLEXITY_MEDIUM}."
                ),
            ),
            source="static",
        ))
    return findings


def _dead_code_findings(analysis: AnalysisReport) -> list[Finding]:
    findings: list[Finding] = []
    for func in analysis.dead_code_functions:
        # High-complexity dead code is more important to clean up
        severity = (
            Severity.WARNING
            if func.cyclomatic_complexity >= COMPLEXITY_HIGH
            else Severity.INFO
        )
        findings.append(Finding(
            severity=severity,
            category=FindingCategory.DEAD_CODE,
            title=f"Codigo muerto: {func.name}()",
            description=(
                f"La funcion {func.qualified_name} no es referenciada en ningun otro modulo. "
                f"Considerar eliminarla para reducir complejidad del codebase."
            ),
            file_path=str(func.file_path),
            line_start=func.line_start,
            line_end=func.line_end,
            function_name=func.name,
            qualified_name=func.qualified_name,
            language=func.language.value,
            suggested_fix=SuggestedFix(
                description=f"Eliminar {func.name}() si no se usa",
                explanation="Eliminar codigo muerto reduce el costo de mantenimiento.",
            ),
            source="static",
        ))
    return findings


def _coupling_findings(analysis: AnalysisReport) -> list[Finding]:
    findings: list[Finding] = []
    for coupling in analysis.coupling_issues:
        total = coupling.afferent_coupling + coupling.efferent_coupling
        findings.append(Finding(
            severity=Severity.WARNING,
            category=FindingCategory.COUPLING,
            title=f"Acoplamiento alto en {coupling.module_path.name}",
            description=(
                f"El modulo {coupling.module_path} tiene "
                f"acoplamiento aferente={coupling.afferent_coupling}, "
                f"eferente={coupling.efferent_coupling}, "
                f"inestabilidad={coupling.instability:.2f}. "
                f"Alto acoplamiento dificulta refactorizaciones."
            ),
            file_path=str(coupling.module_path),
            line_start=1,
            suggested_fix=SuggestedFix(
                description="Reducir dependencias del modulo",
                explanation=(
                    "Considerar aplicar el principio de inversion de dependencias "
                    "o extraer interfaces para reducir el acoplamiento."
                ),
            ),
            source="static",
        ))
    return findings


def _missing_tests_findings(analysis: AnalysisReport) -> list[Finding]:
    """Generate findings for untested functions with high complexity."""
    findings: list[Finding] = []
    # Only flag untested functions that also have notable complexity
    critical_untested = [
        f for f in analysis.untested_functions
        if f.cyclomatic_complexity >= COMPLEXITY_HIGH
    ]
    important_untested = [
        f for f in analysis.untested_functions
        if f.cyclomatic_complexity >= 5 and f.cyclomatic_complexity < COMPLEXITY_HIGH
        and f.is_public
    ]

    for func in critical_untested:
        findings.append(Finding(
            severity=Severity.WARNING,
            category=FindingCategory.MISSING_TESTS,
            title=f"Funcion critica sin tests: {func.name}()",
            description=(
                f"La funcion {func.qualified_name} tiene complejidad {func.cyclomatic_complexity} "
                f"y no tiene tests. Funciones complejas sin tests son un riesgo alto."
            ),
            file_path=str(func.file_path),
            line_start=func.line_start,
            line_end=func.line_end,
            function_name=func.name,
            qualified_name=func.qualified_name,
            language=func.language.value,
            suggested_fix=SuggestedFix(
                description=f"Agregar tests unitarios para {func.name}()",
                explanation="Priorizar testing de funciones con alta complejidad ciclomatica.",
            ),
            source="static",
        ))

    for func in important_untested:
        findings.append(Finding(
            severity=Severity.INFO,
            category=FindingCategory.MISSING_TESTS,
            title=f"Funcion sin tests: {func.name}()",
            description=(
                f"La funcion publica {func.qualified_name} "
                f"(CC={func.cyclomatic_complexity}) no tiene tests."
            ),
            file_path=str(func.file_path),
            line_start=func.line_start,
            line_end=func.line_end,
            function_name=func.name,
            qualified_name=func.qualified_name,
            language=func.language.value,
            source="static",
        ))

    return findings
