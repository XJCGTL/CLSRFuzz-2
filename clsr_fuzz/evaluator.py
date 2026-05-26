from __future__ import annotations

from typing import Any, Dict, Tuple

from clsr_fuzz.instruction_stats import count_instruction_types
from clsr_fuzz.testcase import TestCase


def evaluate(
    testcase: TestCase, result: Dict[str, Any], config: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    thresholds = config.get("thresholds", {})
    metrics = result.get("metrics", {})
    metrics = _coerce_metrics(metrics, testcase, config)

    triggered = any(
        metrics.get(key, 0) >= thresholds.get(key, float("inf")) for key in thresholds
    )
    score = _score(metrics, config)
    detail = {"metrics": metrics, "score": score, "triggered": triggered}
    return triggered, detail


def _score(metrics: Dict[str, Any], config: Dict[str, Any]) -> float:
    weights = config.get("weights", {})
    score = 0.0
    for key, weight in weights.items():
        score += float(metrics.get(key, 0)) * float(weight)
    return score


def _coerce_metrics(metrics: Dict[str, Any], testcase: TestCase, config: Dict[str, Any]) -> Dict[str, Any]:
    if metrics:
        return metrics

    counts = count_instruction_types(testcase.instructions)
    load_count = counts["load"]
    store_count = counts["store"]
    mul_count = counts["mul"]
    fence_count = counts["fence"] + counts["nop"]

    limits = config.get("limits", {})
    mshr_limit = limits.get("mshr_entries", 16)
    lsq_limit = limits.get("lsq_entries", 16)
    rob_limit = limits.get("rob_entries", 64)

    mshr_occupancy = min(mshr_limit, (load_count // 4) + (store_count // 8))
    lsq_occupancy = min(lsq_limit, (load_count + store_count) // 4)
    rob_full_cycles = min(rob_limit, (mul_count // 8) + (fence_count // 16))
    stall_cycles = (load_count + store_count + mul_count) // 2

    return {
        "rob_full_cycles": rob_full_cycles,
        "mshr_occupancy": mshr_occupancy,
        "lsq_occupancy": lsq_occupancy,
        "stall_cycles": stall_cycles,
    }
