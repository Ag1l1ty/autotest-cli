"""Go language detector."""

from __future__ import annotations

from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, find_files_by_pattern, safe_read


@register("go")
class GoDetector(BaseLanguageDetector):

    @property
    def language_name(self) -> str:
        return "go"

    def detect(self, root: Path) -> LanguageInfo | None:
        files = collect_files(root, {".go"})
        if not files:
            return None

        test_files = find_files_by_pattern(root, ["*_test.go"])
        source_files = [f for f in files if not f.name.endswith("_test.go")]

        return LanguageInfo(
            language=Language.GO,
            files=source_files,
            total_loc=sum(count_lines(f) for f in source_files),
            existing_test_files=test_files,
            build_tool="go" if (root / "go.mod").exists() else None,
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        gomod = root / "go.mod"
        if not gomod.exists():
            return frameworks

        content = safe_read(gomod).lower()
        framework_map = {
            "gin-gonic/gin": "Gin",
            "gorilla/mux": "Gorilla Mux",
            "labstack/echo": "Echo",
            "gofiber/fiber": "Fiber",
            "go-chi/chi": "Chi",
            "beego": "Beego",
            "grpc": "gRPC",
        }
        for dep_key, name in framework_map.items():
            if dep_key in content:
                frameworks.append(FrameworkInfo(name=name, config_file=gomod))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = ["go test"]  # Built-in
        gomod = root / "go.mod"
        if gomod.exists():
            content = safe_read(gomod).lower()
            if "testify" in content:
                tools.append("testify")
            if "gomock" in content:
                tools.append("gomock")
            if "gocheck" in content:
                tools.append("gocheck")
        return tools
