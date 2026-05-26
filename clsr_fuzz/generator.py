from __future__ import annotations

import random
from typing import Any, Dict, List

from clsr_fuzz.testcase import TestCase


def generate_seed(strategy: str, config: Dict[str, Any], rng: random.Random) -> TestCase:
    strategies = config.get("strategies", {})
    params = dict(strategies.get(strategy, {}))
    if not params:
        raise ValueError(f"Unknown strategy: {strategy}")
    instructions = _build_instructions(params, rng, config)
    memory_map = {
        "base": params.get("base", "0x80000000"),
        "size": params.get("size", 1024 * 1024),
        "stride": params.get("stride", 4096),
    }
    metadata = {"strategy": strategy, "seed": rng.randint(0, 2**32 - 1)}
    return TestCase(instructions=instructions, memory_map=memory_map, params=params, metadata=metadata)


def _build_instructions(params: Dict[str, Any], rng: random.Random, config: Dict[str, Any]) -> List[str]:
    instructions: List[str] = []
    load_count = int(params.get("load_count", 0))
    stride = int(params.get("stride", 4096))
    mul_chain_len = int(params.get("mul_chain_len", 0))
    delay_nops = int(params.get("delay_nops", 0))
    loop_depth = max(1, int(params.get("loop_depth", 1)))

    for _ in range(loop_depth):
        if load_count:
            for i in range(load_count):
                offset = i * stride
                instructions.append(f"lw x12, {offset}(x10)")
        if mul_chain_len:
            for _ in range(mul_chain_len):
                instructions.append("mul x5, x5, x6")
        for _ in range(delay_nops):
            instructions.append("nop")

    max_instructions = int(config.get("generation", {}).get("max_instructions", 256))
    if len(instructions) > max_instructions:
        instructions = instructions[:max_instructions]

    if not instructions:
        instructions.append(rng.choice(config.get("instruction_pool", ["nop"])))

    return instructions
