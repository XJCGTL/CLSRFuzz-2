from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List

from clsr_fuzz.config import load_config
from clsr_fuzz.evaluator import evaluate
from clsr_fuzz.fuzzer import fuzz
from clsr_fuzz.generator import generate_seed
from clsr_fuzz.minimizer import minimize
from clsr_fuzz.simulator import run_simulation
from clsr_fuzz.static_scan import scan_rtl, write_scan_report
from clsr_fuzz.testcase import TestCase


def main() -> None:
    parser = argparse.ArgumentParser(prog="clsr_fuzz", description="CLSRFuzz prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan RTL sources for resource patterns")
    scan_parser.add_argument("--rtl-dir", required=True)
    scan_parser.add_argument("--extensions", default="sv,v,vh,scala")
    scan_parser.add_argument("--out", default="scan_results.json")

    gen_parser = subparsers.add_parser("generate", help="Generate seed testcases")
    gen_parser.add_argument("--strategy", default="all")
    gen_parser.add_argument("--count", type=int, default=3)
    gen_parser.add_argument("--out-dir", default="seeds")
    gen_parser.add_argument("--config")
    gen_parser.add_argument("--seed", type=int)

    fuzz_parser = subparsers.add_parser("fuzz", help="Run fuzzing loop")
    fuzz_parser.add_argument("--seeds", required=True)
    fuzz_parser.add_argument("--iterations", type=int, default=50)
    fuzz_parser.add_argument("--sim-cmd")
    fuzz_parser.add_argument("--timeout", type=int)
    fuzz_parser.add_argument("--out", default="findings.json")
    fuzz_parser.add_argument("--workdir", default="fuzz_runs")
    fuzz_parser.add_argument("--minimize", action="store_true")
    fuzz_parser.add_argument("--config")
    fuzz_parser.add_argument("--seed", type=int)

    minimize_parser = subparsers.add_parser("minimize", help="Minimize a testcase")
    minimize_parser.add_argument("--testcase", required=True)
    minimize_parser.add_argument("--sim-cmd")
    minimize_parser.add_argument("--timeout", type=int)
    minimize_parser.add_argument("--out", default="minimized.json")
    minimize_parser.add_argument("--config")

    args = parser.parse_args()
    if args.command == "scan":
        _handle_scan(args)
    elif args.command == "generate":
        _handle_generate(args)
    elif args.command == "fuzz":
        _handle_fuzz(args)
    elif args.command == "minimize":
        _handle_minimize(args)


def _handle_scan(args: argparse.Namespace) -> None:
    extensions = [ext.strip() for ext in args.extensions.split(",") if ext.strip()]
    hits = scan_rtl(Path(args.rtl_dir), extensions)
    output_path = Path(args.out)
    write_scan_report(hits, output_path)
    print(json.dumps({"matches": len(hits), "output": str(output_path)}, indent=2))


def _handle_generate(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    strategies = config.get("strategies", {})
    if args.strategy == "all":
        selected = list(strategies.keys())
    else:
        selected = [args.strategy]

    index = 0
    for strategy in selected:
        for _ in range(args.count):
            testcase = generate_seed(strategy, config, rng)
            testcase_path = out_dir / f"seed_{index:03d}.json"
            testcase.save(testcase_path)
            index += 1
    print(json.dumps({"seeds": index, "output_dir": str(out_dir)}, indent=2))


def _handle_fuzz(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    seeds = _load_seeds(Path(args.seeds))
    report = fuzz(
        seeds=seeds,
        config=config,
        iterations=args.iterations,
        sim_cmd=args.sim_cmd,
        timeout=args.timeout,
        out_path=Path(args.out),
        workdir=Path(args.workdir),
        minimize_findings=args.minimize,
        rng_seed=args.seed,
    )
    print(json.dumps(report["stats"], indent=2))


def _handle_minimize(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    testcase = TestCase.load(args.testcase)

    def runner(case: TestCase) -> Dict[str, Any]:
        return run_simulation(case, args.sim_cmd, args.timeout, Path("minimize_run"))

    def evaluator(case: TestCase, result: Dict[str, Any]) -> Any:
        return evaluate(case, result, config)

    minimized = minimize(testcase, runner, evaluator)
    minimized.save(args.out)
    print(json.dumps({"output": args.out, "instructions": len(minimized.instructions)}, indent=2))


def _load_seeds(path: Path) -> List[TestCase]:
    if path.is_file():
        return [TestCase.load(path)]
    seeds: List[TestCase] = []
    for seed_file in sorted(path.glob("*.json")):
        seeds.append(TestCase.load(seed_file))
    if not seeds:
        raise FileNotFoundError(f"No seed files found in {path}")
    return seeds
