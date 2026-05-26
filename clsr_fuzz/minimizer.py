from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from clsr_fuzz.testcase import TestCase


def minimize(
    testcase: TestCase,
    runner: Callable[[TestCase], Dict[str, Any]],
    evaluator: Callable[[TestCase, Dict[str, Any]], Tuple[bool, Dict[str, Any]]],
) -> TestCase:
    triggered, _ = evaluator(testcase, runner(testcase))
    if not triggered:
        return testcase

    instructions = list(testcase.instructions)
    index = 0
    while index < len(instructions):
        candidate_instructions = instructions[:index] + instructions[index + 1 :]
        if not candidate_instructions:
            index += 1
            continue
        candidate = TestCase(
            instructions=candidate_instructions,
            memory_map=dict(testcase.memory_map),
            params=dict(testcase.params),
            metadata=dict(testcase.metadata),
        )
        candidate_triggered, _ = evaluator(candidate, runner(candidate))
        if candidate_triggered:
            instructions = candidate_instructions
        else:
            index += 1

    return TestCase(
        instructions=instructions,
        memory_map=dict(testcase.memory_map),
        params=dict(testcase.params),
        metadata=dict(testcase.metadata),
    )
