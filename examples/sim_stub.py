from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--testcase", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()

    with Path(args.testcase).open("r", encoding="utf-8") as handle:
        testcase = json.load(handle)

    instructions = testcase.get("instructions", [])
    load_count = sum(1 for instr in instructions if instr.startswith("lw"))
    store_count = sum(1 for instr in instructions if instr.startswith("sw"))
    mul_count = sum(1 for instr in instructions if instr.startswith("mul"))
    fence_count = sum(1 for instr in instructions if instr in {"fence", "nop"})

    metrics = {
        "rob_full_cycles": (mul_count // 4) + (fence_count // 8),
        "mshr_occupancy": (load_count // 2) + (store_count // 4),
        "lsq_occupancy": (load_count + store_count) // 3,
        "stall_cycles": (load_count + store_count + mul_count) // 2,
    }

    if args.out:
        Path(args.out).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    else:
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
