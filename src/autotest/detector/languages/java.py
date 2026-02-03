"""Java language detector."""

from __future__ import annotations

from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, find_files_by_pattern, safe_read


@register("java")
class JavaDetector(BaseLanguageDetector):

    @property
    def language_name(self) -> str:
        return "java"

    def detect(self, root: Path) -> LanguageInfo | None:
        files = collect_files(root, {".java"})
        if not files:
            return None

        test_files = find_files_by_pattern(root, [
            "*Test.java", "*Tests.java", "*Spec.java", "Test*.java",
        ])

        return LanguageInfo(
            language=Language.JAVA,
            files=files,
            total_loc=sum(count_lines(f) for f in files),
            existing_test_files=test_files,
            build_tool=self._detect_build_tool(root),
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        
        # Check pom.xml
        pom = root / "pom.xml"
        if pom.exists():
            content = safe_read(pom).lower()
            if "spring-boot" in content:
                frameworks.append(FrameworkInfo(name="Spring Boot", config_file=pom))
            elif "spring" in content:
                frameworks.append(FrameworkInfo(name="Spring", config_file=pom))
            if "hibernate" in content:
                frameworks.append(FrameworkInfo(name="Hibernate"))
            if "quarkus" in content:
                frameworks.append(FrameworkInfo(name="Quarkus"))
            if "micronaut" in content:
                frameworks.append(FrameworkInfo(name="Micronaut"))

        # Check build.gradle
        for gradle in ["build.gradle", "build.gradle.kts"]:
            gf = root / gradle
            if gf.exists():
                content = safe_read(gf).lower()
                if "spring" in content:
                    frameworks.append(FrameworkInfo(name="Spring Boot", config_file=gf))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = []
        
        for config_file in ["pom.xml", "build.gradle", "build.gradle.kts"]:
            path = root / config_file
            if path.exists():
                content = safe_read(path).lower()
                if "junit" in content:
                    tools.append("junit")
                if "mockito" in content:
                    tools.append("mockito")
                if "jacoco" in content:
                    tools.append("jacoco")
                if "testng" in content:
                    tools.append("testng")
                if "assertj" in content:
                    tools.append("assertj")

        return tools

    def _detect_build_tool(self, root: Path) -> str | None:
        if (root / "pom.xml").exists():
            return "maven"
        if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
            return "gradle"
        return None
