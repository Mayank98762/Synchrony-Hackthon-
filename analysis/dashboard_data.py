"""Data for the 4-page dashboard (plan §11): one JSON file per page in dashboard/public/data/.

Built after run_all's export, from key_numbers.json, the aggregate tables and the experiment modules'
*_table helpers, so the dashboard shows exactly the pipeline's numbers. Aggregates only: the repo is public.
Every figure carries its key_numbers label (Measured / Simulated / Assumed); totals are asserted here.

    python -m analysis.dashboard_data        (after run_all)
"""
import json
from datetime import datetime

import numpy as np
import pandas as pd

from analysis import config as C, experiments_f as F, experiments_h as H

OUT = C.ROOT / "dashboard" / "public" / "data"
TABLES = C.OUTPUTS / "tables"
METHODS = ["HSIC", "Cash/UPI", "Wallet", "Debit", "Other CC"]
METHOD_KEY = {"HSIC": "hsic", "Cash/UPI": "cash_upi", "Wallet": "wallet", "Debit": "debit", "Other CC": "other_cc"}
BOX_NAMES = {"A": "Closed, still shopping", "B": "Protect first", "C": "Activate", "D": "Grow", "E": "Nudge",
             "F": "Non-cardholder"}

# Plan §8, ordered by priority (O3 first). `economics` keys fill in when Shreyash's economics.py lands.
OFFERS = [
    ("O3", "Reward visibility", "Product", "Every basket; Prime Grocery + Electronics first",
     "A till and receipt line: \"Pay with HSIC: earn ₹X on this basket\", and a monthly \"₹ you left on the table\".",
     "H-aware"),
    ("O1", "Instant cashback at the till", "Product", "All HSIC purchases",
     "The same reward, applied at checkout instead of on next month's statement.", "H-imm"),
    ("O2", "HSIC card on UPI", "Product", "All cardholders",
     "Link the credit card to UPI, where Cash/UPI took 47% of the lost share.", None),
    ("O4", "No-cost EMI on baskets of ₹3,000+", "Moment", "Basket ≥ ₹3,000",
     "Subvention co-funded by MetroMart; the Wallet carries about half of capped tickets.", None),
    ("O5", "Small-basket streak", "Moment", "Baskets under ₹1,000",
     "5 HSIC purchases under ₹1,000 in a month earn a ₹50 bonus.", None),
    ("O6", "Win-back", "Segment A", "Closed, still shopping",
     "Instant re-approval and 3% on everything for 90 days, capped, co-funded by MetroMart.", None),
    ("O7", "Young-card protection", "Segments B, C", "Cards under 12 months",
     "An activation milestone (3 swipes in 60 days) plus a 3-month Prime trial for Non-Prime.", None),
    ("O8", "Threshold bonus", "Segment D", "High-frequency mature cards",
     "An extra 1% only on HSIC spend above the customer's own trailing 3-month average.", None),
]


def plain(v):
    if isinstance(v, (np.generic,)):
        return v.item()
    if isinstance(v, (pd.Period, pd.Timestamp)):
        return str(v.date()) if isinstance(v, pd.Timestamp) else str(v)
    if isinstance(v, float) and np.isnan(v):
        return None
    return v


def records(df):
    return [{k: plain(v) for k, v in r.items()} for r in df.to_dict("records")]


def key_numbers():
    raw = json.loads((C.OUTPUTS / "key_numbers.json").read_text(encoding="utf-8"))
    return raw


class KN:
    """Reads key_numbers: .v(key) the value (None if the owner's module hasn't produced it), .fig(key) value + label."""

    def __init__(self):
        self.raw = key_numbers()

    def v(self, key):
        return self.raw[key]["value"] if key in self.raw else None

    def fig(self, key):
        if key not in self.raw:
            return {"key": key, "value": None, "label": "Pending"}
        return {"key": key, "value": self.raw[key]["value"], "label": self.raw[key]["label"]}


def overview(kn):
    q = F.quarterly_sow_table()
    pc = F.per_card_monthly_table()
    mix = {fy: {m: kn.v(f"base_mix_fy{fy % 100}_{METHOD_KEY[m]}") for m in METHODS} for fy in C.FISCAL_YEARS}
    for fy, parts in mix.items():
        assert abs(sum(parts.values()) - 1) < 1e-9, f"FY{fy} payment mix does not sum to 1"
    bridge = {k: kn.v(f"f2_{k}_pp") for k in ("leaver", "stayer", "joiner", "total")}
    assert abs(bridge["leaver"] + bridge["stayer"] + bridge["joiner"] - bridge["total"]) < 1e-9, "Bridge does not reconcile"
    loss = {m: kn.v(f"f3_{METHOD_KEY[m]}_share_of_loss") for m in METHODS[1:]}
    assert abs(sum(loss.values()) - 1) < 1e-9, "loss shares do not sum to 1"
    return {
        "sow_quarterly": [{"quarter": k, "sow": float(v)} for k, v in q.items()],
        "per_card_monthly": [{"month": str(m), "net_per_card": float(r.net_per_card), "hsic_per_card": float(r.hsic_per_card),
                              "cards": int(r.cards)} for m, r in pc.iterrows()],
        "kpis": {k: kn.fig(k) for k in [
            "f1_sow_fy25", "f1_sow_fy26", "f1_sow_fy25_q1", "f1_sow_fy26_q4", "f1_slope_pp_per_quarter",
            "f14_aug24_net_per_card", "f14_may26_net_per_card", "f14_aug24_hsic_per_card", "f14_may26_hsic_per_card",
            "f9_rate_first", "f9_rate_last", "f11_still_shopping", "f11_post_close_net", "f12_gap",
            "f8_prime_ge_left_on_table", "f8_rewards_earned_fy26"]},
        "mix": [{"method": m, "fy25": mix[2025][m], "fy26": mix[2026][m]} for m in METHODS],
        "bridge": bridge,
        "loss_share": [{"method": m, "share": s} for m, s in loss.items()],
    }


def segments(kn):
    t = H.slice_table()
    band = pd.read_csv(TABLES / "x1_sow_band_movement.csv")
    return {
        "slices": records(t),
        "gate": {k: kn.fig(k) for k in [
            "x1_variance_ratio_fy25", "x1_variance_ratio_fy26", "x1_split_half_r", "x1_split_half_ci_lo", "x1_split_half_ci_hi",
            "x1_split_half_n", "x1_persistence_r", "x1_persistence_ci_lo", "x1_persistence_ci_hi", "x1_persistence_n",
            "f13_r_purchases", "f13_r_net", "x8_prime_logit_coef", "x8_prime_logit_ci_lo", "x8_prime_logit_ci_hi"]},
        "band_movement": records(band),
        "kmeans": {k: kn.fig(k) for k in ["seg_kmeans_k", "seg_kmeans_customers", "seg_kmeans_ari", "seg_kmeans_eta2",
                                          "seg_kmeans_fy25_sow_spread_pp", "seg_kmeans_fy26_sow_spread_pp"]},
        "kmeans_clusters": records(pd.read_csv(TABLES / "segments_kmeans_clusters.csv")),
    }


def attrition(kn):
    silent = H.silent_attrition_table()
    decay = H.pre_closure_table().reset_index()
    quarters = F.closure_quarter_table()
    age = [{"cutoff": str(cut.date()), "bin": b,
            "rate": kn.v(f"f10_{F.slug(cut.date())}_closure_{F.slug(b)}")}
           for cut in (C.CUTOFF_TRAIN, C.CUTOFF_TEST) for b in C.CARD_AGE_LABELS]
    model = pd.read_csv(C.MODEL_EVAL / "closure_comparison.csv")[["model", "roc_auc", "pr_auc", "top_decile_capture"]]
    return {
        "silent": records(silent.assign(cutoff=silent.cutoff.astype(str).str[:10])),
        "decay": records(decay),
        "closures_quarterly": records(quarters),
        "closure_by_age": age,
        "closure_model": records(model),
        "figures": {k: kn.fig(k) for k in [
            "x3_verdict", "x4_verdict", "x4_raw_m12", "x4_raw_m0", "x4_slope_pp_per_month", "x4_slope_ci_lo_pp",
            "x4_slope_ci_hi_pp", "f9_rate_first", "f9_rate_last", "f10_2026_01_31_young_over_old", "cm_b2_roc_auc",
            "cm_lr_all_roc_auc", "cm_test_cards", "cm_test_closers", "cm_test_base_rate", "x5_usage_increment_roc",
            "f11_still_shopping", "f11_post_close_net", "f11_mix_cash_upi", "f11_mix_wallet", "f11_mix_debit",
            "f11_mix_other_cc"]},
    }


def priority(kn):
    box = pd.read_csv(TABLES / "segments_box_table.csv")
    sizes = pd.read_csv(TABLES / "segments_sizes.csv")
    split = pd.read_csv(TABLES / "segments_young_split.csv")
    assert sizes.customers_at_score.sum() == 45_000, "segment sizes at 2026-07-31 do not sum to the 45,000 customers"
    econ = {k: v for k, v in kn.raw.items() if k.startswith(("o1_", "o2_", "o3_", "o4_", "o5_", "o6_", "o7_", "o8_", "mde_"))}
    return {
        "boxes": records(box),
        "sizes": records(sizes),
        "young_split": records(split),
        "segment_a": {k: kn.fig(k) for k in ["seg_A_n_score", "seg_A_post_close_net", "f11_still_shopping", "f11_post_close_net"]},
        "axes": {k: kn.fig(k) for k in ["seg_young_top_share", "seg_mature_top_share", "seg_sow_max_gap_pp",
                                        "seg_age_closure_diff", "seg_freq_nonhsic_diff", "seg_freq_cut", "seg_freq_cut_score"]},
        "offers": [{"id": i, "name": n, "layer": layer, "who": who, "what": what, "tests": tests} for i, n, layer, who, what, tests in OFFERS],
        "economics": econ,                       # empty until economics.py lands
        "scenarios": {k: kn.fig(k) for k in kn.raw if k.startswith("assumed_")},
    }


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    kn = KN()
    meta = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "data_window": f"{C.DATA_START.date()} to {C.DATA_END.date()}",
            "customers": 45_000, "source": "outputs/key_numbers.json and outputs/tables (run_all.py)"}
    paths = []
    for name, build in (("overview", overview), ("segments", segments), ("attrition", attrition), ("priority", priority)):
        path = OUT / f"{name}.json"
        path.write_text(json.dumps({"meta": meta, **build(kn)}, ensure_ascii=False, indent=1, default=plain), encoding="utf-8")
        paths.append(path)
    size = sum(p.stat().st_size for p in paths)
    assert size < 2_000_000, f"dashboard data is {size / 1e6:.1f} MB, over the plan's 2 MB budget"
    return paths, {"bytes": size}


if __name__ == "__main__":
    paths, info = run()
    for p in paths:
        print(p.relative_to(C.ROOT), f"{p.stat().st_size / 1000:.1f} kB")
    print(f"total {info['bytes'] / 1000:.1f} kB")
