from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from clsr_fuzz.testcase import TestCase

LOAD_OFFSET_PATTERN = re.compile(r"(l[wd])\s+(x\d+),\s*([+-]?\d+)\((x\d+)\)")


def mutate(testcase: TestCase, config: Dict[str, Any], rng: random.Random) -> TestCase:
    mutation_cfg = config.get("mutation", {})
    instructions = list(testcase.instructions)

    if rng.random() < mutation_cfg.get("insert_prob", 0.3):
        _insert_instruction(instructions, config, rng)
    if rng.random() < mutation_cfg.get("delete_prob", 0.3):
        _delete_instruction(instructions, rng)
    if rng.random() < mutation_cfg.get("replace_prob", 0.2):
        _replace_instruction(instructions, config, rng)
    if rng.random() < mutation_cfg.get("offset_mutate_prob", 0.2):
        _mutate_load_offset(instructions, rng)
    if rng.random() < mutation_cfg.get("delay_prob", 0.2):
        _insert_delay(instructions, rng)

    max_instructions = int(mutation_cfg.get("max_instructions", 256))
    if len(instructions) > max_instructions:
        instructions = instructions[:max_instructions]
    if not instructions:
        instructions = ["nop"]

    return TestCase(
        instructions=instructions,
        memory_map=dict(testcase.memory_map),
        params=dict(testcase.params),
        metadata=dict(testcase.metadata),
    )


def _insert_instruction(instructions: List[str], config: Dict[str, Any], rng: random.Random) -> None:
    pool = config.get("instruction_pool", ["nop"])
    index = rng.randint(0, len(instructions))
    instructions.insert(index, rng.choice(pool))


def _delete_instruction(instructions: List[str], rng: random.Random) -> None:
    if not instructions:
        return
    index = rng.randrange(len(instructions))
    instructions.pop(index)


def _replace_instruction(instructions: List[str], config: Dict[str, Any], rng: random.Random) -> None:
    if not instructions:
        return
    pool = config.get("instruction_pool", ["nop"])
    index = rng.randrange(len(instructions))
    instructions[index] = rng.choice(pool)


def _mutate_load_offset(instructions: List[str], rng: random.Random) -> None:
    if not instructions:
        return
    index = rng.randrange(len(instructions))
    match = LOAD_OFFSET_PATTERN.search(instructions[index])
    if not match:
        return
    opcode, dst, offset, base = match.groups()
    new_offset = int(offset) + rng.choice([-4096, -2048, -64, 64, 2048, 4096])
    instructions[index] = f"{opcode} {dst}, {new_offset}({base})"


def _insert_delay(instructions: List[str], rng: random.Random) -> None:
    index = rng.randint(0, len(instructions))
    instructions.insert(index, rng.choice(["nop", "fence"]))
