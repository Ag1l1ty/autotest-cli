"""JSON reporter for CI/CD integration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from autotest.config import AutoTestConfig
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter


class JSONReporter(BaseReporter):
    """Generates JSON reports compatible with CI/CD pipelines."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config

    async def generate(self, report_data: ReportData) -> Path:
        """Generate JSON report file."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "autotest-report.json"

        # Use Pydantic's JSON serialization
        json_str = report_data.model_dump_json(indent=2)
        output_path.write_text(json_str, encoding="utf-8")

        return output_path
