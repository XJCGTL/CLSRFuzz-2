from __future__ import annotations

import argparse
import json
from pathlib import Path

from clsr_fuzz.config import load_config
from clsr_fuzz.instruction_stats import estimate_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--testcase", required=True)
    parser.add_argument("--out")
    parser.add_argument("--config")
    args = parser.parse_args()

    with Path(args.testcase).open("r", encoding="utf-8") as handle:
        testcase = json.load(handle)

    instructions = testcase.get("instructions", [])
    config = load_config(args.config)
    limits = config.get("limits", {})
    metrics = estimate_metrics(instructions, limits)

    if args.out:
        Path(args.out).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    else:
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
