"""Reproduction checks (PROJECT_PLAN §14, selection_log §10), evaluated by run_all.py on the merged numbers.

Each check names the key it reads. A check whose key no module has produced yet is `pending`, not a
failure, so the pipeline runs before every teammate's module exists. A failed check stops the run:
find the cause, never widen the tolerance.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from analysis import config as C, prep

# (key, expected, absolute tolerance, what it reproduces)
EXACT3 = 0.0005          # "rates must match to 3 decimals"
CHECKS = [
    # Exact cross-checks against both EDAs: counts identical, rates to 3 decimals.
    ("base_sow_fy25", 0.289, EXACT3, "Pooled SoW FY25"),
    ("base_sow_fy26", 0.195, EXACT3, "Pooled SoW FY26"),
    ("base_mix_fy25_debit", 0.088, EXACT3, "FY25 mix: Debit"),
    ("base_mix_fy25_other_cc", 0.090, EXACT3, "FY25 mix: Other CC"),
    ("base_mix_fy25_cash_upi", 0.189, EXACT3, "FY25 mix: Cash/UPI"),
    ("base_mix_fy25_wallet", 0.344, EXACT3, "FY25 mix: Wallet"),
    ("base_mix_fy26_debit", 0.107, EXACT3, "FY26 mix: Debit"),
    ("base_mix_fy26_other_cc", 0.108, EXACT3, "FY26 mix: Other CC"),
    ("base_mix_fy26_cash_upi", 0.234, EXACT3, "FY26 mix: Cash/UPI"),
    ("base_mix_fy26_wallet", 0.357, EXACT3, "FY26 mix: Wallet"),
    ("cm_train_cards", 26749, 0, "Open cards at 2025-07-31"),
    ("cm_test_cards", 29198, 0, "Open cards at 2026-01-31"),
    ("cm_train_closers", 1281, 0, "Closers in 6m after 2025-07-31 (rule 9)"),
    ("cm_test_closers", 1799, 0, "Closers in 6m after 2026-01-31"),
    ("base_card_age_auc_train", 0.611, EXACT3, "Card-age AUC at 2025-07-31"),
    ("cm_b2_roc_auc", 0.672, EXACT3, "Card-age AUC at 2026-01-31"),
    ("f14_aug24_cards", 21514, 0, "Cards active in Aug 2024"),
    ("f14_aug24_net_per_card", 1036.8, 0.05, "Net spend per card, Aug 2024"),
    ("f14_aug24_hsic_per_card", 356.2, 0.05, "HSIC spend per card, Aug 2024"),
    ("f14_aug24_sow", 0.344, EXACT3, "SoW Aug 2024"),
    ("f14_may26_cards", 30742, 0, "Cards active in May 2026"),
    ("f14_may26_net_per_card", 1028.9, 0.05, "Net spend per card, May 2026"),
    ("f14_may26_hsic_per_card", 166.7, 0.05, "HSIC spend per card, May 2026"),
    ("f14_may26_sow", 0.162, EXACT3, "SoW May 2026"),
    # 23 Oct exploratory numbers: ±0.2pp unless stated.
    ("f1_sow_fy25", 0.2891, 0.002, "F1 SoW FY25"),
    ("f1_sow_fy26", 0.1948, 0.002, "F1 SoW FY26"),
    ("f2_leaver_pp", 0.26, 0.2, "Bridge: leaver effect (pp)"),
    ("f2_stayer_pp", -9.54, 0.2, "Bridge: stayer change (pp)"),
    ("f2_joiner_pp", -0.15, 0.2, "Bridge: joiner effect (pp)"),
    ("f3_cash_upi_share_of_loss", 0.47, 0.01, "Cash/UPI share of HSIC's loss"),
    ("x1_variance_ratio_fy25", 1.00, 0.02, "Variance ratio FY25"),
    ("x1_variance_ratio_fy26", 1.00, 0.02, "Variance ratio FY26"),
    ("x3_excess_time_2025_01_31", 0.0, 0.015, "Time-aware silent-attrition excess, 2025-01-31"),
    ("x3_excess_time_2025_07_31", 0.0, 0.015, "Time-aware silent-attrition excess, 2025-07-31"),
    ("x3_excess_time_2026_01_31", 0.0, 0.015, "Time-aware silent-attrition excess, 2026-01-31"),
    ("f11_post_close_net", 91.2e6, 0.05e6, "Post-closure net spend"),
    ("f8_prime_ge_left_on_table", 1.60e6, 0.005e6, "Prime G+E cashback left on the table, FY26"),
    ("f15_reward_rate_fy26", 0.01399, 0.0001, "FY26 effective reward rate on HSIC spend"),
    ("f12_gap", 33.4e6, 0.5e6, "HSIC spend gap at constant SoW"),
]


def foundation():
    """Anchor numbers computed straight from prep, so the cross-checks don't depend on any one module."""
    d = prep.load()
    act = prep.active(d.txn)
    out = {}
    for fy in C.FISCAL_YEARS:
        rows = act[act.fy == fy]
        out[f"base_sow_fy{fy % 100}"] = float(prep.sow(rows))
        mix = rows.groupby("payment_short").net.sum() / rows.net.sum()
        for method, share in mix.items():
            key = method.lower().replace("/", "_").replace(" ", "_")
            out[f"base_mix_fy{fy % 100}_{key}"] = float(share)
    u = prep.snapshot_universe(C.CUTOFF_TRAIN)
    out["base_card_age_auc_train"] = float(roc_auc_score(u.closed_6m.astype(int), -u.card_age_years))
    return out


def evaluate(numbers):
    rows = []
    for key, expected, tol, what in CHECKS:
        if key not in numbers:
            rows.append({"key": key, "check": what, "expected": expected, "actual": np.nan, "tolerance": tol, "status": "pending"})
            continue
        actual = float(numbers[key])
        ok = abs(actual - expected) <= tol + 1e-12
        rows.append({"key": key, "check": what, "expected": expected, "actual": actual, "tolerance": tol,
                     "status": "pass" if ok else "FAIL"})
    return pd.DataFrame(rows)
