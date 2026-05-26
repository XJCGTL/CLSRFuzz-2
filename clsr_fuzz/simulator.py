from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from clsr_fuzz.testcase import TestCase


def run_simulation(
    testcase: TestCase,
    sim_cmd: Optional[str],
    timeout: Optional[int],
    workdir: Path,
) -> Dict[str, Any]:
    if not sim_cmd:
        return {"metrics": {}, "source": "heuristic"}

    workdir.mkdir(parents=True, exist_ok=True)
    testcase_path = workdir / "current_testcase.json"
    testcase.save(testcase_path)
    output_path = workdir / "sim_result.json"

    command = sim_cmd.format(testcase=testcase_path, out=output_path, workdir=workdir)
    result = _run_command(command, timeout)

    if output_path.exists():
        try:
            with output_path.open("r", encoding="utf-8") as handle:
                metrics = json.load(handle)
            return {"metrics": metrics, "source": "file"}
        except json.JSONDecodeError:
            return {
                "metrics": {},
                "source": "file_parse_error",
                "stderr": result.stderr,
            }

    if result.stdout:
        try:
            return {"metrics": json.loads(result.stdout), "source": "stdout"}
        except json.JSONDecodeError:
            return {
                "metrics": {},
                "source": "stdout_parse_error",
                "stderr": result.stderr,
            }

    return {"metrics": {}, "source": "empty", "stderr": result.stderr}


def _run_command(command: str, timeout: Optional[int]) -> subprocess.CompletedProcess[str]:
    args = shlex.split(command)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
