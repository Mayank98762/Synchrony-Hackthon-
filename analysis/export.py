"""Write the merged numbers to the files the deck reads: key_numbers.md / .json, experiment_log.csv,
impact_ledger.csv, plus the check report. Also guards the public repo against customer-level files.
"""
import json
import re
from datetime import datetime

import numpy as np
import pandas as pd

from analysis import config as C

# Every key gets one label (PROJECT_PLAN §3 rule 7). Economics outputs are simulated; scenario inputs assumed.
SIMULATED = re.compile(r"^(o\d+_|mde_|econ_)")
LABEL_BY_PREFIX = [
    ("assumed_", "Assumed"),
    ("f15_net_margin", "Measured × Assumed"), ("f15_gross", "Measured × Assumed"),
]
GROUPS = [
    (r"^base_", "Cross-check anchors"), (r"^f\d+_", "Findings (F)"), (r"^x\d+_", "Hypotheses tested (X)"),
    (r"^cm_", "Closure model"), (r"^seg_", "Segments"), (r"^(o\d+_|econ_)", "Offers & economics"),
    (r"^mde_", "Pilot design"), (r"^assumed_", "Assumptions"),
]

# X1-X17 for the appendix table: what we expected, and which keys hold the verdict and headline result.
EXPERIMENTS = [
    ("X1", "Clustering customers on SoW reveals low-SoW segments", "x1_verdict", ["x1_variance_ratio_fy25", "x1_split_half_r", "x1_persistence_r"]),
    ("X2", "A detector can flag individual customers whose SoW is declining", "x2_verdict", ["x2_naive_flag_rate_observed", "x2_naive_flag_rate_null"]),
    ("X3", "Silent attrition is concentrated in some cardholders", "x3_verdict", ["x3_excess_time_2026_01_31", "x3_excess_fixed_2026_01_31"]),
    ("X4", "HSIC use decays before a card closes", "x4_verdict", ["x4_slope_pp_per_month"]),
    ("X5", "Recent card usage predicts closure", "x5_verdict", ["x5_usage_roc_auc", "x5_usage_increment_roc"]),
    ("X6", "Gradient boosting beats logistic regression", "x6_verdict", ["x6_hgb_minus_lr", "x6_ci_lo", "x6_ci_hi"]),
    ("X7", "New cards show an onboarding usage cliff", "x7_verdict", ["x7_slope_pp_per_month", "x7_max_abs_excess_pp"]),
    ("X8", "Non-Prime members drop off because 1% is too little", "x8_verdict", []),
    ("X9", "Customers keep Grocery on HSIC and move other categories away", "x9_verdict", []),
    ("X10", "Credit limits bind during sale events", "x10_verdict", []),
    ("X11", "Festive peaks drive switching", "x11_verdict", []),
    ("X12", "MetroMart's Wallet is cannibalising the card", "x12_verdict", []),
    ("X13", "A never-activated segment exists", "x13_verdict", []),
    ("X14", "Ticket-size or category mix makes good segments", "x14_verdict", []),
    ("X15", "Predict an SoW drop in the next 60 days", "x15_verdict", ["x15_rows_per_60d", "x15_sow_undefined_share_last_60d"]),
    ("X16", "Uplift model for offer response", "x16_verdict", ["x16_offer_fields"]),
    ("X17", "Returns behave differently by payment method", "x17_verdict", []),
]

# Impact ledger rows: (metric, key, unit, type). Rows whose key isn't produced yet are left out.
LEDGER = [
    ("SoW FY25", "f1_sow_fy25", "share", "Measured"),
    ("SoW FY26", "f1_sow_fy26", "share", "Measured"),
    ("HSIC spend gap at constant SoW", "f12_gap", "₹", "Measured"),
    ("Post-closure MetroMart spend (closers still shopping)", "f11_post_close_net", "₹", "Measured"),
    ("Prime G+E cashback left on the table, FY26", "f8_prime_ge_left_on_table", "₹", "Measured"),
    ("FY26 effective reward rate on HSIC spend", "f15_reward_rate_fy26", "share", "Measured"),
    ("Net margin lost, no co-funding (low)", "f15_net_margin_lo_nocofund", "₹", "Measured × Assumed"),
    ("Net margin lost, no co-funding (high)", "f15_net_margin_hi_nocofund", "₹", "Measured × Assumed"),
    ("Net margin lost, 50% co-funding (low)", "f15_net_margin_lo_cofund", "₹", "Measured × Assumed"),
    ("Net margin lost, 50% co-funding (high)", "f15_net_margin_hi_cofund", "₹", "Measured × Assumed"),
    ("Segment A spend after closure (5,903 customers)", "seg_A_post_close_net", "₹", "Measured"),
    ("Closers caught in top decile by card age", "cm_b2_top_decile", "share", "Measured"),
]


def label(key):
    if SIMULATED.match(key):
        return "Simulated"
    for prefix, lab in LABEL_BY_PREFIX:
        if key.startswith(prefix):
            return lab
    return "Measured"


def _group(key):
    for pattern, name in GROUPS:
        if re.match(pattern, key):
            return name
    return "Other"


def _fmt(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, (int, np.integer)):
        return f"{v:,}"
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return "NaN"
        return f"{v:,.0f}" if abs(v) >= 1e4 else f"{v:.4g}"
    return str(v)


def _plain(v):
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    return v


def assumed_inputs():
    """The scenario inputs, as numbers, so they appear in key_numbers with the Assumed label."""
    out = {}
    for name, s in C.SCENARIOS.items():
        for k, v in s.items():
            out[f"assumed_{k}_{name}"] = v
    return out


def write_key_numbers(numbers, checks, status):
    C.OUTPUTS.mkdir(parents=True, exist_ok=True)
    failed = (checks.status == "FAIL").sum()
    lines = [
        "# Key numbers",
        "",
        f"Generated by `run_all.py` on {datetime.now():%Y-%m-%d %H:%M}. **Never edit by hand**: rerun the pipeline.",
        "Every number on a slide must come from this file (or `key_numbers.json`, same content).",
        "",
    ]
    if failed:
        lines += [f"> **{failed} reproduction check(s) FAILED. Do not use these numbers.** See `outputs/model_eval/checks.csv`.", ""]
    lines += ["## Modules", "", "| Module | Status |", "|---|---|"]
    lines += [f"| `{m}` | {s} |" for m, s in status.items()]
    lines += ["", f"Checks: {(checks.status == 'pass').sum()} pass · {failed} fail · {(checks.status == 'pending').sum()} pending.", ""]

    by_group = {}
    for k in sorted(numbers):
        by_group.setdefault(_group(k), []).append(k)
    order = [g for _, g in GROUPS] + ["Other"]
    for g in dict.fromkeys(order):
        if g not in by_group:
            continue
        lines += [f"## {g}", "", "| Key | Value | Label |", "|---|---|---|"]
        lines += [f"| `{k}` | {_fmt(numbers[k])} | {label(k)} |" for k in by_group[g]]
        lines.append("")
    (C.OUTPUTS / "key_numbers.md").write_text("\n".join(lines), encoding="utf-8")
    payload = {k: {"value": _plain(v), "label": label(k)} for k, v in sorted(numbers.items())}
    (C.OUTPUTS / "key_numbers.json").write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")


def write_experiment_log(numbers):
    rows = []
    for xid, expected, verdict_key, result_keys in EXPERIMENTS:
        result = "; ".join(f"{k} = {_fmt(numbers[k])}" for k in result_keys if k in numbers)
        rows.append({"id": xid, "expected": expected, "verdict": numbers.get(verdict_key, "pending"),
                     "result": result or ("pending" if verdict_key not in numbers else "")})
    pd.DataFrame(rows).to_csv(C.OUTPUTS / "experiment_log.csv", index=False)


def write_impact_ledger(numbers):
    rows = [{"metric": m, "value": numbers[k], "unit": u, "type": t, "source_key": k}
            for m, k, u, t in LEDGER if k in numbers]
    rows += [{"metric": f"{k.replace('assumed_', '').replace('_', ' ')}", "value": v, "unit": "share",
              "type": "Assumed", "source_key": k} for k, v in numbers.items() if k.startswith("assumed_")]
    # Economics outputs: every o*/mde_* key is a simulated result.
    rows += [{"metric": k, "value": v, "unit": "", "type": "Simulated", "source_key": k}
             for k, v in sorted(numbers.items()) if SIMULATED.match(k)]
    ledger = pd.DataFrame(rows)
    assert ledger["type"].isin(["Measured", "Simulated", "Assumed", "Measured × Assumed"]).all(), "untagged ledger row"
    ledger.to_csv(C.OUTPUTS / "impact_ledger.csv", index=False)


def write_checks(checks):
    C.MODEL_EVAL.mkdir(parents=True, exist_ok=True)
    checks.to_csv(C.MODEL_EVAL / "checks.csv", index=False)


def guard_public_repo():
    """Fail if any CSV under outputs/ looks customer-level (one row per customer). The repo is public.

    outputs/eda/ predates the pipeline and already holds such a file on GitHub, so it is reported, not
    fatal; the team has to remove it from main.
    """
    offenders, legacy = [], []
    for path in C.OUTPUTS.rglob("*.csv"):
        head = pd.read_csv(path, nrows=0)
        cols = {c.lower() for c in head.columns}
        if "customer_id" in cols or "customer id" in cols:
            (legacy if "eda" in path.relative_to(C.OUTPUTS).parts else offenders).append(path.relative_to(C.ROOT))
    assert not offenders, f"customer-level files in outputs/ (public repo): {offenders}"
    return [str(p) for p in legacy]
