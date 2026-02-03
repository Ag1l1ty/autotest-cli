"""Rust language detector."""

from __future__ import annotations

from pathlib import Path

from autotest.detector.base import BaseLanguageDetector
from autotest.detector.registry import register
from autotest.models.project import FrameworkInfo, Language, LanguageInfo
from autotest.utils.file_utils import collect_files, count_lines, safe_read


@register("rust")
class RustDetector(BaseLanguageDetector):

    @property
    def language_name(self) -> str:
        return "rust"

    def detect(self, root: Path) -> LanguageInfo | None:
        files = collect_files(root, {".rs"})
        if not files:
            return None

        # Rust tests are inline (#[cfg(test)]), also check for tests/ directory
        test_files = list((root / "tests").rglob("*.rs")) if (root / "tests").is_dir() else []

        return LanguageInfo(
            language=Language.RUST,
            files=files,
            total_loc=sum(count_lines(f) for f in files),
            existing_test_files=test_files,
            build_tool="cargo" if (root / "Cargo.toml").exists() else None,
        )

    def detect_frameworks(self, root: Path) -> list[FrameworkInfo]:
        frameworks: list[FrameworkInfo] = []
        cargo = root / "Cargo.toml"
        if not cargo.exists():
            return frameworks

        content = safe_read(cargo).lower()
        framework_map = {
            "actix-web": "Actix Web",
            "rocket": "Rocket",
            "axum": "Axum",
            "warp": "Warp",
            "tokio": "Tokio",
            "serde": "Serde",
            "diesel": "Diesel",
            "sqlx": "SQLx",
        }
        for dep_key, name in framework_map.items():
            if dep_key in content:
                frameworks.append(FrameworkInfo(name=name, config_file=cargo))

        return frameworks

    def detect_test_tools(self, root: Path) -> list[str]:
        tools: list[str] = ["cargo test"]  # Built-in
        cargo = root / "Cargo.toml"
        if cargo.exists():
            content = safe_read(cargo).lower()
            if "mockall" in content:
                tools.append("mockall")
            if "proptest" in content:
                tools.append("proptest")
            if "tarpaulin" in content or "cargo-tarpaulin" in content:
                tools.append("tarpaulin")
        return tools
