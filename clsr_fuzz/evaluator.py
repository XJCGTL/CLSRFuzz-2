from __future__ import annotations

from typing import Any, Dict, Tuple

from clsr_fuzz.instruction_stats import estimate_metrics
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

    limits = config.get("limits", {})
    heuristics = config.get("heuristics", {})
    return estimate_metrics(testcase.instructions, limits, heuristics)
