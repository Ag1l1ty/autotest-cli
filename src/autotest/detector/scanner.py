"""Project scanner - orchestrates detection across all languages."""

from __future__ import annotations

from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.project import ProjectInfo
from autotest.utils.git_utils import get_current_branch, is_git_repo

# Import language detectors to trigger registration
from autotest.detector.languages import python, javascript, java, go, rust, csharp  # noqa: F401
from autotest.detector.registry import get_all_detectors


class ProjectScanner:
    """Scans a project directory and identifies all technologies."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def scan(self, root: Path) -> ProjectInfo:
        """Scan project and return comprehensive project info."""
        root = root.resolve()
        detectors = get_all_detectors()
        
        languages = []
        config_files: list[Path] = []
        total_loc = 0
        total_files = 0

        for _name, detector_cls in detectors.items():
            detector = detector_cls()
            lang_info = detector.detect(root)
            if lang_info is not None and lang_info.files:
                lang_info.frameworks = detector.detect_frameworks(root)
                lang_info.existing_test_tools = detector.detect_test_tools(root)
                languages.append(lang_info)
                total_loc += lang_info.total_loc
                total_files += len(lang_info.files)

        # Calculate percentages
        for lang in languages:
            if total_loc > 0:
                lang.percentage = round((lang.total_loc / total_loc) * 100, 1)

        # Sort by LOC descending
        languages.sort(key=lambda l: l.total_loc, reverse=True)
        primary = languages[0].language if languages else None

        # Collect config files
        for pattern in ["pyproject.toml", "package.json", "pom.xml", "go.mod", "Cargo.toml", "*.csproj", "*.sln"]:
            config_files.extend(root.glob(pattern))

        return ProjectInfo(
            root_path=root,
            name=root.name,
            languages=languages,
            primary_language=primary,
            has_git=is_git_repo(root),
            git_branch=get_current_branch(root) if is_git_repo(root) else None,
            total_files=total_files,
            total_loc=total_loc,
            config_files_found=config_files,
        )
