from __future__ import annotations

from typing import Any, Dict, Iterable

LOAD_OPCODES = {"lb", "lh", "lw", "ld", "lbu", "lhu", "lwu"}
STORE_OPCODES = {"sb", "sh", "sw", "sd"}


def count_instruction_types(instructions: Iterable[str]) -> Dict[str, int]:
    counts = {"load": 0, "store": 0, "mul": 0, "fence": 0, "nop": 0}
    for instr in instructions:
        opcode = instr.strip().split(maxsplit=1)[0] if instr else ""
        if opcode in LOAD_OPCODES:
            counts["load"] += 1
        elif opcode in STORE_OPCODES:
            counts["store"] += 1
        elif opcode == "mul":
            counts["mul"] += 1
        elif opcode == "fence":
            counts["fence"] += 1
        elif opcode == "nop":
            counts["nop"] += 1
    return counts


def estimate_metrics(
    instructions: Iterable[str], limits: Dict[str, Any] | None = None
) -> Dict[str, int]:
    counts = count_instruction_types(instructions)
    limits = limits or {}
    mshr_limit = int(limits.get("mshr_entries", 16))
    lsq_limit = int(limits.get("lsq_entries", 16))
    rob_limit = int(limits.get("rob_entries", 64))

    load_count = counts["load"]
    store_count = counts["store"]
    mul_count = counts["mul"]
    fence_count = counts["fence"] + counts["nop"]

    mshr_load_divisor = 4
    mshr_store_divisor = 8
    lsq_divisor = 4
    rob_mul_divisor = 8
    rob_fence_divisor = 16

    mshr_occupancy = min(
        mshr_limit, (load_count // mshr_load_divisor) + (store_count // mshr_store_divisor)
    )
    lsq_occupancy = min(lsq_limit, (load_count + store_count) // lsq_divisor)
    rob_full_cycles = min(
        rob_limit, (mul_count // rob_mul_divisor) + (fence_count // rob_fence_divisor)
    )
    stall_cycles = (load_count + store_count + mul_count) // 2

    return {
        "rob_full_cycles": rob_full_cycles,
        "mshr_occupancy": mshr_occupancy,
        "lsq_occupancy": lsq_occupancy,
        "stall_cycles": stall_cycles,
    }
