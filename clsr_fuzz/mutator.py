from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from clsr_fuzz.testcase import TestCase

LOAD_OFFSET_PATTERN = re.compile(
    r"(l(?:b|h|w|d|bu|hu|wu))\s+(x\d+),\s*([+-]?\d+)\((x\d+)\)"
)
REG_PATTERN = re.compile(r"\bx(?:[0-9]|[12][0-9]|3[01])\b")
BRANCH_PATTERN = re.compile(
    r"\b(b(?:eq|ne|lt|ge|ltu|geu))\s+(x\d+),\s*(x\d+),\s*([+-]?\d+)\b"
)
JAL_PATTERN = re.compile(r"\bjal\s+(x\d+),\s*([+-]?\d+)\b")
JALR_PATTERN = re.compile(r"\bjalr\s+(x\d+),\s*([+-]?\d+)\((x\d+)\)\b")
REGISTER_POOL = [f"x{i}" for i in range(1, 32)]


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
        _mutate_load_offset(instructions, rng, mutation_cfg)
    if rng.random() < mutation_cfg.get("delay_prob", 0.2):
        _insert_delay(instructions, rng)
    if rng.random() < mutation_cfg.get("rename_prob", 0.15):
        _rename_register(instructions, rng)
    if rng.random() < mutation_cfg.get("branch_offset_mutate_prob", 0.15):
        _mutate_branch_offset(instructions, rng, mutation_cfg)

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


def _mutate_load_offset(
    instructions: List[str], rng: random.Random, mutation_cfg: Dict[str, Any]
) -> None:
    if not instructions:
        return
    index = rng.randrange(len(instructions))
    match = LOAD_OFFSET_PATTERN.search(instructions[index])
    if not match:
        return
    opcode, dst, offset, base = match.groups()
    deltas = mutation_cfg.get("offset_deltas", [-4096, -2048, -64, 64, 2048, 4096])
    new_offset = int(offset) + rng.choice(deltas)
    instructions[index] = f"{opcode} {dst}, {new_offset}({base})"


def _insert_delay(instructions: List[str], rng: random.Random) -> None:
    index = rng.randint(0, len(instructions))
    instructions.insert(index, rng.choice(["nop", "fence"]))


def _rename_register(instructions: List[str], rng: random.Random) -> None:
    if not instructions:
        return
    index = rng.randrange(len(instructions))
    instruction = instructions[index]
    registers = [reg for reg in REG_PATTERN.findall(instruction) if reg != "x0"]
    if not registers:
        return
    old = rng.choice(registers)
    candidates = [reg for reg in REGISTER_POOL if reg != old]
    if not candidates:
        return
    new = rng.choice(candidates)
    instructions[index] = re.sub(rf"\b{re.escape(old)}\b", new, instruction)


def _mutate_branch_offset(
    instructions: List[str], rng: random.Random, mutation_cfg: Dict[str, Any]
) -> None:
    if not instructions:
        return
    index = rng.randrange(len(instructions))
    instruction = instructions[index]
    deltas = mutation_cfg.get("branch_offset_deltas", [-32, -16, -8, -4, 4, 8, 16, 32])

    match = BRANCH_PATTERN.search(instruction)
    if match:
        opcode, rs1, rs2, offset = match.groups()
        new_offset = int(offset) + rng.choice(deltas)
        instructions[index] = f"{opcode} {rs1}, {rs2}, {new_offset}"
        return

    match = JAL_PATTERN.search(instruction)
    if match:
        rd, offset = match.groups()
        new_offset = int(offset) + rng.choice(deltas)
        instructions[index] = f"jal {rd}, {new_offset}"
        return

    match = JALR_PATTERN.search(instruction)
    if match:
        rd, offset, rs1 = match.groups()
        new_offset = int(offset) + rng.choice(deltas)
        instructions[index] = f"jalr {rd}, {new_offset}({rs1})"
