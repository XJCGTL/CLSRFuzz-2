from __future__ import annotations

import heapq
import json
import random
from itertools import count
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from clsr_fuzz.evaluator import evaluate
from clsr_fuzz.minimizer import minimize
from clsr_fuzz.mutator import mutate
from clsr_fuzz.simulator import run_simulation
from clsr_fuzz.testcase import TestCase

MIN_SELECTION_WEIGHT = 1.0

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
    counter = count()
    corpus = _init_corpus(seeds, config, counter)

    for iteration in range(iterations):
        base = _select_seed(corpus, rng)
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
        if _should_add_to_corpus(detail, triggered, config):
            _add_to_corpus(corpus, mutated, detail.get("score", 0.0), config, counter)
        _write_iteration(iteration_dir, mutated, entry)

    stats["corpus_size"] = len(corpus)
    report = {"stats": stats, "findings": findings}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


def _write_iteration(path: Path, testcase: TestCase, entry: Dict[str, Any]) -> None:
    testcase.save(path / "testcase.json")
    with (path / "result.json").open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=2)


def _init_corpus(
    seeds: List[TestCase], config: Dict[str, Any], counter: Iterator[int]
) -> List[Tuple[float, int, TestCase]]:
    corpus: List[Tuple[float, int, TestCase]] = []
    for seed in seeds:
        score = _heuristic_score(seed, config)
        heapq.heappush(corpus, (score, next(counter), seed))
    return corpus


def _heuristic_score(testcase: TestCase, config: Dict[str, Any]) -> float:
    _, detail = evaluate(testcase, {"metrics": {}}, config)
    return float(detail.get("score", 0.0))


def _select_seed(
    corpus: List[Tuple[float, int, TestCase]], rng: random.Random
) -> TestCase:
    if not corpus:
        raise ValueError("Empty fuzzing corpus")
    weights = [max(entry[0], MIN_SELECTION_WEIGHT) for entry in corpus]
    return rng.choices(corpus, weights=weights, k=1)[0][2]


def _should_add_to_corpus(
    detail: Dict[str, Any], triggered: bool, config: Dict[str, Any]
) -> bool:
    fuzzing_cfg = config.get("fuzzing", {})
    if triggered and fuzzing_cfg.get("keep_triggered", True):
        return True
    score_threshold = float(fuzzing_cfg.get("score_threshold", 0.0))
    return float(detail.get("score", 0.0)) >= score_threshold


def _add_to_corpus(
    corpus: List[Tuple[float, int, TestCase]],
    testcase: TestCase,
    score: float,
    config: Dict[str, Any],
    counter: Iterator[int],
) -> None:
    fuzzing_cfg = config.get("fuzzing", {})
    max_size = int(fuzzing_cfg.get("corpus_max_size", 50))
    entry = (score, next(counter), testcase)
    if max_size <= 0:
        heapq.heappush(corpus, entry)
        return
    if len(corpus) < max_size:
        heapq.heappush(corpus, entry)
        return
    if score > corpus[0][0]:
        heapq.heapreplace(corpus, entry)
