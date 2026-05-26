from __future__ import annotations

from typing import Dict, Iterable

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
