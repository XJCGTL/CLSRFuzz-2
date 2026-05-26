from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from clsr_fuzz.evaluator import evaluate
from clsr_fuzz.minimizer import minimize
from clsr_fuzz.mutator import mutate
from clsr_fuzz.simulator import run_simulation
from clsr_fuzz.testcase import TestCase


def fuzz(
    seeds: List[TestCase],
    config: Dict[str, Any],
    iterations: int,
    sim_cmd: Optional[str],
    timeout: Optional[int],
    out_path: Path,
    workdir: Path,
    minimize_findings: bool,
    rng_seed: Optional[int],
) -> Dict[str, Any]:
    rng = random.Random(rng_seed)
    findings: List[Dict[str, Any]] = []
    stats = {"iterations": iterations, "triggered": 0}
    run_dir = workdir / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)

    for iteration in range(iterations):
        base = rng.choice(seeds)
        mutated = mutate(base, config, rng)
        iteration_dir = run_dir / f"iter_{iteration:04d}"
        simulation_result = run_simulation(mutated, sim_cmd, timeout, iteration_dir)
        triggered, detail = evaluate(mutated, simulation_result, config)

        entry = {
            "iteration": iteration,
            "triggered": triggered,
            "detail": detail,
            "simulation": simulation_result.get("source"),
        }

        if triggered:
            stats["triggered"] += 1
            if minimize_findings:
                minimized = minimize(
                    mutated,
                    lambda case: run_simulation(case, sim_cmd, timeout, iteration_dir),
                    lambda case, result: evaluate(case, result, config),
                )
                entry["testcase"] = minimized.to_dict()
            else:
                entry["testcase"] = mutated.to_dict()
            findings.append(entry)
        _write_iteration(iteration_dir, mutated, entry)

    report = {"stats": stats, "findings": findings}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def _write_iteration(path: Path, testcase: TestCase, entry: Dict[str, Any]) -> None:
    testcase.save(path / "testcase.json")
    with (path / "result.json").open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=2)
