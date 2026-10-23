"""Rebuild every number from the raw CSVs in one command, then check and export them.

    python analysis/run_all.py          (or: python -m analysis.run_all)

Teammates' modules (experiments_f, experiments_h, economics) are picked up when they exist and
reported as `pending` until then. Any error inside a module, a key produced by two modules, or a
failed reproduction check stops the run with a non-zero exit code.
"""
import importlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis import checks, config as C, export, prep  # noqa: E402

MODULES = [
    "analysis.experiments_ml",   # Devansh
    "analysis.closure_model",    # Devansh
    "analysis.segments",         # Devansh
    "analysis.experiments_f",    # Mayank (F12, F15: Shreyash)
    "analysis.experiments_h",    # Mayank
    "analysis.economics",        # Shreyash
]

# Chart modules run after export (they read key_numbers.json); each exposes run() and writes PNGs.
CHART_MODULES = [
    "analysis.charts_ml",        # Devansh: slides 8-9
]


def _merge(numbers, new, source, owner):
    clash = set(numbers) & set(new)
    assert not clash, f"{source} re-defines keys from {[owner[k] for k in clash]}: {sorted(clash)}"
    numbers.update(new)
    owner.update(dict.fromkeys(new, source))


def main():
    t0 = time.time()
    print("prep: loading and validating the case data")
    prep.load()

    numbers, owner, status = {}, {}, {}
    _merge(numbers, checks.foundation(), "checks.foundation", owner)
    _merge(numbers, export.assumed_inputs(), "config.SCENARIOS", owner)
    status["checks.foundation"] = "ok"

    for name in MODULES:
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise                     # the module exists but one of its imports is missing
            status[name] = "pending (module not written yet)"
            print(f"{name}: pending")
            continue
        t = time.time()
        _merge(numbers, module.run(), name, owner)
        status[name] = f"ok ({time.time() - t:.0f}s)"
        print(f"{name}: {status[name]}")

    report = checks.evaluate(numbers)
    legacy = export.guard_public_repo()
    export.write_checks(report)
    export.write_key_numbers(numbers, report, status)
    export.write_experiment_log(numbers)
    export.write_impact_ledger(numbers)

    for name in CHART_MODULES:
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise
            print(f"{name}: pending")
            continue
        paths, _ = module.run()
        print(f"{name}: {len(paths)} charts -> outputs/charts/")

    counts = report.status.value_counts().to_dict()
    print(f"\n{len(numbers)} numbers -> outputs/key_numbers.md | checks: {counts} | {time.time() - t0:.0f}s")
    for p in legacy:
        print(f"WARNING: customer-level file in the public repo: {p}")
    failed = report[report.status == "FAIL"]
    if len(failed):
        print("\nFAILED reproduction checks:\n" + failed.to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
