"""Tests for auto fixer."""

from __future__ import annotations

from pathlib import Path

from autotest.diagnosis.auto_fixer import apply_fixes, AutoFixReport
from autotest.models.diagnosis import Finding, FindingCategory, Severity, SuggestedFix


def _make_finding_with_fix(
    file_path: str = "config.py",
    code_before: str = 'secret = "abc123"',
    code_after: str = 'secret = os.environ["SECRET"]',
) -> Finding:
    return Finding(
        id="CD-001",
        severity=Severity.CRITICAL,
        category=FindingCategory.SECURITY,
        title="Hardcoded secret",
        description="Found hardcoded secret",
        file_path=file_path,
        line_start=1,
        suggested_fix=SuggestedFix(
            description="Use env var",
            code_before=code_before,
            code_after=code_after,
        ),
    )


def _make_finding_no_fix() -> Finding:
    return Finding(
        id="CD-002",
        severity=Severity.WARNING,
        category=FindingCategory.COMPLEXITY,
        title="Complex function",
        description="Very complex",
        file_path="module.py",
    )


class TestApplyFixes:

    def test_applies_fix_to_matching_file(self, tmp_path: Path) -> None:
        target = tmp_path / "config.py"
        target.write_text('secret = "abc123"\nother = "safe"\n')

        finding = _make_finding_with_fix()
        report = apply_fixes([finding], tmp_path)

        assert report.applied_count == 1
        content = target.read_text()
        assert 'os.environ["SECRET"]' in content
        assert '"abc123"' not in content

    def test_dry_run_does_not_modify(self, tmp_path: Path) -> None:
        target = tmp_path / "config.py"
        original = 'secret = "abc123"\n'
        target.write_text(original)

        finding = _make_finding_with_fix()
        report = apply_fixes([finding], tmp_path, dry_run=True)

        assert report.applied_count == 1
        assert "[dry-run]" in report.applied[0].message
        assert target.read_text() == original  # File unchanged

    def test_skips_finding_without_fix(self, tmp_path: Path) -> None:
        finding = _make_finding_no_fix()
        report = apply_fixes([finding], tmp_path)
        assert report.skipped_count == 1

    def test_skips_finding_without_file_path(self, tmp_path: Path) -> None:
        finding = _make_finding_with_fix(file_path="")
        report = apply_fixes([finding], tmp_path)
        assert report.skipped_count == 1

    def test_fails_for_missing_file(self, tmp_path: Path) -> None:
        finding = _make_finding_with_fix(file_path="nonexistent.py")
        report = apply_fixes([finding], tmp_path)
        assert len(report.failed) == 1

    def test_skips_when_code_before_not_found(self, tmp_path: Path) -> None:
        target = tmp_path / "config.py"
        target.write_text("# already fixed\nsecret = os.environ['S']\n")

        finding = _make_finding_with_fix()
        report = apply_fixes([finding], tmp_path)
        assert report.skipped_count == 1

    def test_multiple_findings(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.py"
        f1.write_text('password = "hunter2_long_pass"\n')
        f2 = tmp_path / "b.py"
        f2.write_text('token = "tok_12345678901234567890"\n')

        findings = [
            _make_finding_with_fix(
                file_path="a.py",
                code_before='password = "hunter2_long_pass"',
                code_after='password = os.environ["PASSWORD"]',
            ),
            _make_finding_with_fix(
                file_path="b.py",
                code_before='token = "tok_12345678901234567890"',
                code_after='token = os.environ["TOKEN"]',
            ),
        ]
        report = apply_fixes(findings, tmp_path)
        assert report.applied_count == 2
