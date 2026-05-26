from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "instruction_pool": [
        "lw x10, 0(x11)",
        "ld x10, 0(x11)",
        "sw x10, 0(x11)",
        "addi x10, x10, 1",
        "mul x5, x5, x6",
        "beq x10, x11, 16",
        "jal x1, 32",
        "fence",
        "nop",
    ],
    "strategies": {
        "load_storm": {"load_count": 64, "stride": 4096, "loop_depth": 1},
        "mul_chain": {"mul_chain_len": 256, "loop_depth": 1},
        "mixed": {
            "load_count": 32,
            "stride": 4096,
            "mul_chain_len": 128,
            "loop_depth": 1,
            "delay_nops": 2,
        },
    },
    "generation": {"max_instructions": 256},
    "mutation": {
        "insert_prob": 0.3,
        "delete_prob": 0.3,
        "replace_prob": 0.2,
        "offset_mutate_prob": 0.2,
        "delay_prob": 0.2,
        "rename_prob": 0.15,
        "branch_offset_mutate_prob": 0.15,
        "offset_deltas": [-4096, -2048, -64, 64, 2048, 4096],
        "branch_offset_deltas": [-32, -16, -8, -4, 4, 8, 16, 32],
        "max_instructions": 256,
    },
    "thresholds": {
        "rob_full_cycles": 50,
        "mshr_occupancy": 8,
        "lsq_occupancy": 8,
        "stall_cycles": 100,
    },
    "weights": {
        "rob_full_cycles": 1.0,
        "mshr_occupancy": 1.0,
        "lsq_occupancy": 1.0,
        "stall_cycles": 0.5,
    },
    "limits": {"rob_entries": 64, "mshr_entries": 16, "lsq_entries": 16},
}


def load_config(path: str | Path | None) -> Dict[str, Any]:
    config = deepcopy(DEFAULT_CONFIG)
    if not path:
        return config
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return _deep_merge(config, loaded)


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
