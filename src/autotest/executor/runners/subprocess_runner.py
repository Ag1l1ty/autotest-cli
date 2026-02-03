"""Async subprocess runner for executing test commands."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubprocessResult:
    """Result of a subprocess execution."""
    command: list[str]
    stdout: str
    stderr: str
    return_code: int
    duration_ms: float
    timed_out: bool = False


async def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> SubprocessResult:
    """Run a command asynchronously and capture output."""
    import os

    run_env = {**os.environ, **(env or {})}
    start = time.monotonic()
    timed_out = False

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=run_env,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            timed_out = True
            stdout_bytes = b""
            stderr_bytes = b"Command timed out"

    except FileNotFoundError:
        elapsed = (time.monotonic() - start) * 1000
        return SubprocessResult(
            command=cmd,
            stdout="",
            stderr=f"Command not found: {cmd[0]}",
            return_code=127,
            duration_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return SubprocessResult(
            command=cmd,
            stdout="",
            stderr=str(e),
            return_code=1,
            duration_ms=elapsed,
        )

    elapsed = (time.monotonic() - start) * 1000

    return SubprocessResult(
        command=cmd,
        stdout=stdout_bytes.decode("utf-8", errors="replace"),
        stderr=stderr_bytes.decode("utf-8", errors="replace"),
        return_code=process.returncode or 0,
        duration_ms=elapsed,
        timed_out=timed_out,
    )
