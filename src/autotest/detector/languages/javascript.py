"""JavaScript/TypeScript language detector."""

from __future__ import annotations

import json
from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, find_files_by_pattern, safe_read


@register("javascript")
class JavaScriptDetector(BaseLanguageDetector):
    """Detects JavaScript/TypeScript projects."""

    @property
    def language_name(self) -> str:
        return "javascript"

    def detect(self, root: Path) -> LanguageInfo | None:
        js_files = collect_files(root, {".js", ".jsx", ".mjs", ".cjs"})
        ts_files = collect_files(root, {".ts", ".tsx"})
        all_files = js_files + ts_files
        
        if not all_files:
            return None

        test_files = find_files_by_pattern(root, [
            "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts",
            "*.test.jsx", "*.spec.jsx", "*.test.tsx", "*.spec.tsx",
        ])
        # Also check __tests__ directories
        test_files.extend(find_files_by_pattern(root, ["__tests__/**/*.js", "__tests__/**/*.ts"]))

        # Use TypeScript as language if TS files dominate
        ts_loc = sum(count_lines(f) for f in ts_files)
        js_loc = sum(count_lines(f) for f in js_files)
        language = Language.TYPESCRIPT if ts_loc > js_loc else Language.JAVASCRIPT

        return LanguageInfo(
            language=language,
            files=all_files,
            total_loc=ts_loc + js_loc,
            existing_test_files=list(set(test_files)),
            build_tool=self._detect_build_tool(root),
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        pkg = self._load_package_json(root)
        if not pkg:
            return frameworks

        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        framework_map = {
            "react": "React",
            "react-dom": "React",
            "vue": "Vue.js",
            "nuxt": "Nuxt",
            "@angular/core": "Angular",
            "svelte": "Svelte",
            "next": "Next.js",
            "express": "Express",
            "fastify": "Fastify",
            "koa": "Koa",
            "nestjs": "NestJS",
            "@nestjs/core": "NestJS",
            "hapi": "Hapi",
            "gatsby": "Gatsby",
            "remix": "Remix",
            "electron": "Electron",
        }

        seen = set()
        for dep_key, display_name in framework_map.items():
            if dep_key in all_deps and display_name not in seen:
                seen.add(display_name)
                frameworks.append(FrameworkInfo(
                    name=display_name,
                    version=all_deps.get(dep_key),
                    config_file=root / "package.json",
                ))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = []
        pkg = self._load_package_json(root)
        if not pkg:
            return tools

        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        if "jest" in all_deps:
            tools.append("jest")
        if "vitest" in all_deps:
            tools.append("vitest")
        if "mocha" in all_deps:
            tools.append("mocha")
        if "cypress" in all_deps:
            tools.append("cypress")
        if "playwright" in all_deps or "@playwright/test" in all_deps:
            tools.append("playwright")
        if "c8" in all_deps:
            tools.append("c8")
        if "istanbul" in all_deps or "nyc" in all_deps:
            tools.append("istanbul")
        if "testing-library" in str(all_deps):
            tools.append("testing-library")

        return tools

    def _detect_build_tool(self, root: Path) -> str | None:
        if (root / "bun.lockb").exists():
            return "bun"
        if (root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (root / "yarn.lock").exists():
            return "yarn"
        if (root / "package-lock.json").exists():
            return "npm"
        if (root / "package.json").exists():
            return "npm"
        return None

    def _load_package_json(self, root: Path) -> dict | None:
        pkg_path = root / "package.json"
        if not pkg_path.exists():
            return None
        try:
            return json.loads(safe_read(pkg_path))
        except (json.JSONDecodeError, Exception):
            return None
