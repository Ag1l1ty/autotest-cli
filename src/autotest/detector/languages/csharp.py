"""C# language detector."""

from __future__ import annotations

from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, find_files_by_pattern, safe_read


@register("csharp")
class CSharpDetector(BaseLanguageDetector):

    @property
    def language_name(self) -> str:
        return "csharp"

    def detect(self, root: Path) -> LanguageInfo | None:
        files = collect_files(root, {".cs"})
        if not files:
            return None

        test_files = find_files_by_pattern(root, [
            "*Test.cs", "*Tests.cs", "*.Tests/**/*.cs",
        ])

        return LanguageInfo(
            language=Language.CSHARP,
            files=files,
            total_loc=sum(count_lines(f) for f in files),
            existing_test_files=test_files,
            build_tool="dotnet" if list(root.rglob("*.csproj")) or list(root.rglob("*.sln")) else None,
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        
        for csproj in root.rglob("*.csproj"):
            content = safe_read(csproj).lower()
            if "microsoft.aspnetcore" in content:
                frameworks.append(FrameworkInfo(name="ASP.NET Core", config_file=csproj))
            if "microsoft.entityframeworkcore" in content:
                frameworks.append(FrameworkInfo(name="Entity Framework Core"))
            if "blazor" in content:
                frameworks.append(FrameworkInfo(name="Blazor"))
            if "maui" in content:
                frameworks.append(FrameworkInfo(name="MAUI"))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = []
        
        for csproj in root.rglob("*.csproj"):
            content = safe_read(csproj).lower()
            if "xunit" in content:
                tools.append("xunit")
            if "nunit" in content:
                tools.append("nunit")
            if "mstest" in content:
                tools.append("mstest")
            if "moq" in content:
                tools.append("moq")
            if "coverlet" in content:
                tools.append("coverlet")
            if "fluentassertions" in content:
                tools.append("fluentassertions")

        return list(set(tools))
