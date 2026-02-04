"""Analysis engine - orchestrates all code analysis."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.analysis import AnalysisReport, FunctionMetrics, ModuleMetrics
from autotest.models.project import Language, ProjectInfo
from autotest.analyzer.complexity import calculate_complexity
from autotest.analyzer.coupling import calculate_coupling
from autotest.analyzer.coverage_gap import find_untested_functions
from autotest.analyzer.dead_code import detect_dead_code
from autotest.analyzer.parsers.python_parser import PythonParser
from autotest.analyzer.parsers.js_parser import JSParser
from autotest.analyzer.parsers.java_parser import JavaParser
from autotest.analyzer.parsers.go_parser import GoParser
from autotest.analyzer.parsers.rust_parser import RustParser
from autotest.analyzer.parsers.csharp_parser import CSharpParser
from autotest.utils.file_utils import count_lines


# Directories that contain test code, not production source
_TEST_DIR_NAMES = {"tests", "test", "__tests__", "spec", "specs"}


# Parser mapping
PARSERS = {
    Language.PYTHON: PythonParser(),
    Language.JAVASCRIPT: JSParser(),
    Language.TYPESCRIPT: JSParser(),
    Language.JAVA: JavaParser(),
    Language.GO: GoParser(),
    Language.RUST: RustParser(),
    Language.CSHARP: CSharpParser(),
}


class AnalysisEngine:
    """Orchestrates code analysis across all detected languages."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def analyze(self, project: ProjectInfo) -> AnalysisReport:
        """Analyze all source files in the project."""
        all_modules: list[ModuleMetrics] = []
        all_functions: list[FunctionMetrics] = []
        all_source_files: list[Path] = []

        for lang_info in project.languages:
            parser = PARSERS.get(lang_info.language)
            if not parser:
                continue

            # Build set for O(1) lookup
            test_files_set = set(lang_info.existing_test_files)

            # Track functions for this language only
            lang_functions: list[FunctionMetrics] = []

            for file_path in lang_info.files:
                # Skip test files in analysis
                if file_path in test_files_set:
                    continue

                # Safety net: skip files inside test directories
                if self._is_in_test_dir(file_path, project.root_path):
                    continue

                all_source_files.append(file_path)
                functions = parser.parse_functions(file_path)
                imports = parser.parse_imports(file_path)

                # Calculate complexity for each function
                for func in functions:
                    func.cyclomatic_complexity = calculate_complexity(func)

                lang_functions.extend(functions)

                # Build module metrics
                avg_complexity = (
                    sum(f.cyclomatic_complexity for f in functions) / len(functions)
                    if functions else 0.0
                )
                max_complexity = (
                    max(f.cyclomatic_complexity for f in functions)
                    if functions else 0
                )

                module = ModuleMetrics(
                    file_path=file_path,
                    language=lang_info.language,
                    loc=count_lines(file_path),
                    functions=functions,
                    imports=imports,
                    average_complexity=round(avg_complexity, 2),
                    max_complexity=max_complexity,
                )
                all_modules.append(module)

            # Find untested functions for this language only
            find_untested_functions(lang_functions, lang_info)
            all_functions.extend(lang_functions)

        # Calculate coupling
        coupling_data = calculate_coupling(all_modules)

        # Find dead code
        detect_dead_code(all_functions, all_source_files)

        # Collect results
        untested = [f for f in all_functions if f.is_public and not f.is_tested]
        high_complexity = [
            f for f in all_functions
            if f.cyclomatic_complexity > self.config.complexity_threshold
        ]
        dead_code = [f for f in all_functions if f.is_dead_code]
        tested_count = sum(1 for f in all_functions if f.is_tested)
        total_public = sum(1 for f in all_functions if f.is_public)
        estimated_coverage = (tested_count / total_public * 100) if total_public > 0 else 0.0

        # Aggregate metrics
        total_loc = sum(m.loc for m in all_modules)
        avg_cc = (
            sum(f.cyclomatic_complexity for f in all_functions) / len(all_functions)
            if all_functions else 0.0
        )

        return AnalysisReport(
            modules=all_modules,
            untested_functions=untested,
            high_complexity_functions=high_complexity,
            dead_code_functions=dead_code,
            coupling_data=coupling_data,
            total_functions=len(all_functions),
            tested_function_count=tested_count,
            estimated_coverage=round(estimated_coverage, 1),
            avg_complexity=round(avg_cc, 1),
            total_loc=total_loc,
        )

    @staticmethod
    def _is_in_test_dir(file_path: Path, root: Path) -> bool:
        """Check if file is inside a test directory."""
        try:
            rel = file_path.relative_to(root)
        except ValueError:
            return False
        # Check directory parts only (exclude filename)
        return any(part in _TEST_DIR_NAMES for part in rel.parts[:-1])
