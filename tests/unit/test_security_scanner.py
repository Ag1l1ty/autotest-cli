"""Tests for security scanner."""

from __future__ import annotations

from pathlib import Path

import pytest

from autotest.diagnosis.security_scanner import scan_for_secrets, _is_test_file
from autotest.models.diagnosis import Severity


@pytest.fixture
def project_with_secrets(tmp_path: Path) -> Path:
    """Create a project with hardcoded secrets."""
    # Production file with a real secret
    prod = tmp_path / "config.py"
    prod.write_text(
        'API_KEY = "ABCDEFGHIJKLMNOP1234567890"\n'
        'DATABASE_URL = "postgresql://user:pass@host/db"\n'
        'SAFE_VALUE = "hello world"\n'
    )
    # Test file with mock secret
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    test_file = test_dir / "test_auth.py"
    test_file.write_text(
        'client_secret = "test-fake-secret-value"\n'
    )
    # File with AWS key
    aws_file = tmp_path / "deploy.py"
    aws_file.write_text(
        'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"\n'
    )
    return tmp_path


@pytest.fixture
def clean_project(tmp_path: Path) -> Path:
    """Create a project with no secrets."""
    (tmp_path / "main.py").write_text('print("hello")\n')
    return tmp_path


class TestScanForSecrets:

    def test_finds_secrets_in_production_files(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        prod_findings = [f for f in findings if f.severity == Severity.CRITICAL]
        assert len(prod_findings) >= 2  # API key + AWS key

    def test_test_files_get_info_severity(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        test_findings = [f for f in findings if "test_auth" in f.file_path]
        assert len(test_findings) >= 1
        assert all(f.severity == Severity.INFO for f in test_findings)

    def test_test_files_suggest_verification_not_env_vars(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        test_findings = [f for f in findings if "test_auth" in f.file_path]
        for f in test_findings:
            assert f.suggested_fix is not None
            assert "mock" in f.suggested_fix.description.lower()
            assert f.suggested_fix.code_before == ""  # No code replacement for tests

    def test_production_files_suggest_env_vars(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        prod_findings = [f for f in findings if f.severity == Severity.CRITICAL]
        for f in prod_findings:
            assert f.suggested_fix is not None
            assert f.suggested_fix.code_before != ""
            assert "os.environ" in f.suggested_fix.code_after

    def test_clean_project_no_findings(self, clean_project: Path) -> None:
        findings = scan_for_secrets(clean_project)
        assert len(findings) == 0

    def test_findings_have_line_numbers(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        for f in findings:
            assert f.line_start > 0

    def test_findings_have_relative_paths(self, project_with_secrets: Path) -> None:
        findings = scan_for_secrets(project_with_secrets)
        for f in findings:
            assert not f.file_path.startswith("/")

    def test_skips_git_directory(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text('password = "secretpassword12345"\n')
        findings = scan_for_secrets(tmp_path)
        assert len(findings) == 0


class TestIsTestFile:

    def test_test_directory(self) -> None:
        assert _is_test_file(Path("project/tests/test_auth.py")) is True

    def test_test_prefix(self) -> None:
        assert _is_test_file(Path("project/test_utils.py")) is True

    def test_test_suffix(self) -> None:
        assert _is_test_file(Path("project/utils_test.py")) is True

    def test_production_file(self) -> None:
        assert _is_test_file(Path("project/src/config.py")) is False

    def test_conftest(self) -> None:
        assert _is_test_file(Path("project/conftest/helpers.py")) is True
