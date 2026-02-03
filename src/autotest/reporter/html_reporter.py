"""HTML reporter using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

import jinja2

from autotest.config import AutoTestConfig
from autotest.models.report import ReportData
from autotest.reporter.base import BaseReporter

TEMPLATE_DIR = Path(__file__).parent / "templates"


class HTMLReporter(BaseReporter):
    """Generates interactive HTML reports."""

    def __init__(self, config: AutoTestConfig) -> None:
        self.config = config
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )

    async def generate(self, report_data: ReportData) -> Path:
        """Generate HTML report file with unique ID in filename."""
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use report_id in filename for uniqueness
        output_path = output_dir / f"autotest-report-{report_data.report_id}.html"

        template = self.env.get_template("report.html.j2")

        # Prepare template context
        context = {
            "report": report_data,
            "report_id": report_data.report_id,
            "project": report_data.project,
            "analysis": report_data.analysis,
            "strategy": report_data.strategy,
            "execution": report_data.execution,
            "quality": report_data.quality,
            "generated_at": report_data.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "version": report_data.autotest_version,
        }

        html_content = template.render(**context)
        output_path.write_text(html_content, encoding="utf-8")

        return output_path
