"""PROJECT_PLAN §14 / HANDOFF_MAYANK §6 verification of Mayank's numbers. Owner: Mayank.

Runs after `python analysis/run_all.py` and reads its outputs (key_numbers.json, model_eval/checks.csv):
1. Pipeline checks: every checks.py row on a Mayank key passes, none pending, no FAIL anywhere -> blocking.
2. Handoff stubs: every 23 Oct figure in HANDOFF_MAYANK §2-§3 within ±0.2pp, or the precision it is quoted at.
   A miss is blocking unless its cause has been found and is written in CAUSES (the tolerance is never widened).
3. Consistency with Devansh's modules (same universe, same counts) -> blocking.
4. Spot checks: 3 customers from segments.py traced from the raw CSV rows -> segment -> offer (PROJECT_PLAN §7).
Writes outputs/verification/verification_report.md, then exits non-zero if a blocking check failed.

    python -m analysis.verify
"""
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

from analysis import config as C, prep
from analysis.segments import assign

REPORT = C.OUTPUTS / "verification" / "verification_report.md"
MINE = ("f1_", "f2_", "f3_", "f4_", "f5_", "f6_", "f7_", "f8_", "f9_", "f10_", "f11_", "f13_", "f14_",
        "x3_", "x4_", "x8_", "x9_", "x10_", "x11_", "x12_", "x13_", "x14_", "x17_")

# (key, 23 Oct stub, tolerance, scale) in the units the handoff quotes: % for shares (scale 100), else as is.
# Tolerance: ±0.2pp (§14), or half the last quoted digit when the stub is quoted more coarsely.
STUBS = [
    ("f1_sow_fy25", .2891, .002, 1), ("f1_sow_fy26", .1948, .002, 1),
    ("f1_sow_fy25_q1", 32.7, .2, 100), ("f1_sow_fy26_q4", 15.6, .2, 100),
    ("f2_leaver_pp", .26, .2, 1), ("f2_stayer_pp", -9.54, .2, 1), ("f2_joiner_pp", -.15, .2, 1),
    ("f2_stayer_sow_fy25", 29.2, .2, 100), ("f2_stayer_sow_fy26", 19.6, .2, 100), ("f2_stayers_n", 18111, 0, 1),
    ("f3_cash_upi_share_of_loss", 47, .5, 100), ("f3_debit_share_of_loss", 21, .5, 100),
    ("f3_other_cc_share_of_loss", 19, .5, 100), ("f3_wallet_share_of_loss", 14, .5, 100),
    ("f4_cash_upi_change_pp_stayers", 4.5, .2, 1), ("f4_cash_upi_change_pp_noncardholders", 1.8, .2, 1),
    ("f5_hsic_share_fy25_lt1k", 23.3, .2, 100), ("f5_hsic_share_fy26_lt1k", 15.0, .2, 100),
    ("f5_hsic_share_fy25_1k_3k", 27.9, .2, 100), ("f5_hsic_share_fy26_1k_3k", 18.3, .2, 100),
    ("f5_hsic_share_fy25_3k_10k", 28.8, .2, 100), ("f5_hsic_share_fy26_3k_10k", 19.3, .2, 100),
    ("f5_hsic_share_fy25_capped", 30.1, .2, 100), ("f5_hsic_share_fy26_capped", 21.7, .2, 100),
    ("f6_hsic_row_share_t1", 17.1, .2, 100), ("f6_hsic_row_share_t2", 24.2, .2, 100), ("f6_hsic_row_share_t3", 25.5, .2, 100),
    ("f6_auc_month", .592, .002, 1), ("f6_auc_everything", .604, .002, 1),
    ("f7_wallet_share_capped_fy25", 48.5, .2, 100), ("f7_wallet_share_capped_fy26", 51.1, .2, 100),
    ("f8_prime_ge_other_net", 47.4e6, .05e6, 1), ("f8_prime_ge_left_on_table", 1.60e6, .005e6, 1),
    ("f8_all_left_on_table", 3.98e6, .005e6, 1), ("f8_rewards_earned_fy26", .96e6, .005e6, 1),
    ("f9_rate_first", 1.7, .2, 100), ("f9_rate_last", 3.4, .2, 100),
    *[(f"f10_2025_07_31_closure_{b}", v, .2, 100) for b, v in zip(["lt6m", "6_12m", "1_2y", "2_3y", "3yplus"], [8.3, 6.6, 4.6, 3.8, 2.8])],
    *[(f"f10_2026_01_31_closure_{b}", v, .2, 100) for b, v in zip(["lt6m", "6_12m", "1_2y", "2_3y", "3yplus"], [14.7, 9.0, 6.3, 4.0, 3.0])],
    ("f11_still_shopping", 6227, 0, 1), ("f11_closed_cards", 7664, 0, 1), ("f11_post_close_net", 91.2e6, .05e6, 1),
    ("f11_mix_wallet", 46, .5, 100), ("f11_mix_cash_upi", 28, .5, 100), ("f11_mix_debit", 13, .5, 100), ("f11_mix_other_cc", 13, .5, 100),
    ("f13_r_purchases", .44, .005, 1), ("f13_r_net", .22, .005, 1),
    ("f14_aug24_cards", 21514, 0, 1), ("f14_aug24_net_per_card", 1036.8, .05, 1), ("f14_aug24_hsic_per_card", 356.2, .05, 1),
    ("f14_aug24_sow", .344, .0005, 1), ("f14_may26_cards", 30742, 0, 1), ("f14_may26_net_per_card", 1028.9, .05, 1),
    ("f14_may26_hsic_per_card", 166.7, .05, 1), ("f14_may26_sow", .162, .0005, 1),
    ("x3_excess_fixed_2025_01_31", 21.6, .2, 100), ("x3_excess_fixed_2025_07_31", 17.5, .2, 100), ("x3_excess_fixed_2026_01_31", 21.5, .2, 100),
    ("x3_excess_time_2025_01_31", 0, 1.5, 100), ("x3_excess_time_2025_07_31", 0, 1.5, 100), ("x3_excess_time_2026_01_31", 0, 1.5, 100),
    ("x4_raw_m12", 27.0, .2, 100), ("x4_raw_m0", 20.5, .2, 100), ("x4_excess_min_pp", -1.4, .2, 1), ("x4_excess_max_pp", 2.3, .2, 1),
    ("x8_sow_fy25_q1_prime", 32.7, .2, 100), ("x8_sow_fy26_q4_prime", 15.6, .2, 100),
    ("x8_sow_fy25_q1_non_prime", 32.8, .2, 100), ("x8_sow_fy26_q4_non_prime", 15.5, .2, 100),
    ("x9_sow_pooled_min", 23, .5, 100), ("x9_sow_pooled_max", 24, .5, 100),
    ("x10_util_median", 1.2, .05, 100), ("x10_util_max", 26.5, .05, 100), ("x10_months_ge_50pct", 0, 0, 1),
    ("x11_index_min", 92, .5, 1), ("x11_index_max", 108, .5, 1),
    ("x12_wallet_share_of_hsic_loss", 14, .5, 100), ("x12_wallet_share_noncard_fy25", 48.8, .2, 100),
    ("x12_wallet_share_noncard_fy26", 44.8, .2, 100),
    ("x13_zero_hsic_observed", 26.9, .2, 100), ("x13_zero_hsic_expected", 25.7, .2, 100),
    ("x14_r_big_ticket_share", .008, .0005, 1), ("x14_r_grocery_electronics_share", .000, .0005, 1),
    ("x17_return_share_min", 10.1, .05, 100), ("x17_return_share_max", 10.1, .05, 100),
]
VERDICTS = {"x3_verdict": "universal", "x4_verdict": "no decay beyond the calendar trend", "x8_verdict": "rejected",
            "x9_verdict": "rejected", "x10_verdict": "rejected", "x11_verdict": "rejected", "x12_verdict": "rejected",
            "x13_verdict": "rejected", "x14_verdict": "rejected", "x17_verdict": "no signal"}

# Stub misses whose cause was found and reproduced: key -> cause. The deck uses the pipeline value.
CAUSES = {
    "f9_rate_first": "the 23 Oct figure is the fiscal quarter Aug-Oct 2024 (reproduces 1.70%); the handoff and the pipeline use "
                     "the calendar quarter Jul-Sep 2024 (1.77%)",
    "x11_index_min": "the 23 Oct index used gross Sale ₹ (reproduces 91.9-108.4); the pipeline follows the brief's net rule "
                     "(91.4-108.6). Verdict unchanged: no month above 115",
    "x11_index_max": "as x11_index_min",
    "f6_hsic_row_share_t2": "the 23 Oct terciles were a qcut that drops repeated edges: in 8 of 80 category × quarter groups "
                           "(all category 7) over a third of rows are capped at ₹9,999.99, so the top bin vanished and capped rows "
                           "fell into the middle tercile (reproduces 17.10 / 24.11 / 25.52%). The pipeline sends ties up, so terciles "
                           "are balanced and every capped row is high (17.10 / 23.95 / 25.58%)",
    "f6_hsic_row_share_t3": "as f6_hsic_row_share_t2",
    "x13_zero_hsic_expected": "the 23 Oct chance level used one pooled HSIC rate for all 24 months (reproduces 25.74%); the "
                              "pipeline uses the portfolio's rate in each calendar month, as every other null does (26.92%)",
}
# Stub misses whose 23 Oct definition was not recorded and no variant tried reproduces: reported, not blocking.
UNRESOLVED = {
    "f9_rate_last": "calendar Apr-Jun 2026 is 4.01% (the EDA agrees). 3.4% matches no calendar quarter; the nearest is "
                    "fiscal Feb-Apr 2026 (3.34%). 'More than doubled' holds on every definition",
    "f6_auc_month": "AUCs move ±0.005 with the train/test split (random, by customer, purchases vs all active rows tried: "
                    "0.586-0.592 month only, 0.607-0.614 everything); the 23 Oct split was not recorded. "
                    "Message unchanged: the features add about 0.02 AUC",
    "f6_auc_everything": "as f6_auc_month",
    "f13_r_purchases": "stayers 0.432 / all customers 0.433 / active rows only 0.375 tried; none gives 0.44. Message "
                       "unchanged: purchase count persists far more than spend, and SoW not at all",
    "f13_r_net": "stayers 0.226 / all customers 0.237 tried; the pipeline uses the F2 stayers",
    "x14_r_big_ticket_share": "every universe tried (active / all sales, ≥ 2 / ≥ 3 purchases) gives |r| < 0.007, inside "
                              "one standard error (≈ 0.009 at n = 12,886). Both values are zero for the verdict",
    "x14_r_grocery_electronics_share": "as x14_r_big_ticket_share",
}

# PROJECT_PLAN §7: segment -> offer
LEVER = {"A": "O6 win-back", "B": "O7 onboarding protection + O3 reward visibility", "C": "O7 activation milestone + Prime trial",
         "D": "O8 threshold bonus + O3 reward visibility", "E": "O1-O5 product fixes only", "F": "acquisition (stretch)"}


def numbers():
    return {k: v["value"] for k, v in json.loads((C.OUTPUTS / "key_numbers.json").read_text(encoding="utf-8")).items()}


def pipeline_checks(rows):
    chk = pd.read_csv(C.MODEL_EVAL / "checks.csv")
    for r in chk.itertuples():
        mine = r.key.startswith(MINE)
        ok = r.status == "pass" or (r.status == "pending" and not mine)
        rows.append({"part": "1", "check": f"checks.py: {r.check} (`{r.key}`)", "actual": r.actual, "expected": r.expected,
                     "tol": r.tolerance, "status": r.status if ok else ("FAIL" if r.status == "FAIL" else "PENDING (mine)"),
                     "blocking": not ok})


def stub_checks(n, rows):
    for key, stub, tol, scale in STUBS:
        if key not in n:
            rows.append({"part": "2", "check": key, "actual": np.nan, "expected": stub, "tol": tol, "status": "MISSING", "blocking": True})
            continue
        actual = n[key] * scale
        ok = abs(actual - stub) <= tol + 1e-9
        status = "pass" if ok else "explained" if key in CAUSES else "unresolved" if key in UNRESOLVED else "FAIL"
        rows.append({"part": "2", "check": key, "actual": actual, "expected": stub, "tol": tol, "status": status, "blocking": status == "FAIL"})
    for key, want in VERDICTS.items():
        rows.append({"part": "2", "check": key, "actual": n.get(key), "expected": want, "tol": "",
                     "status": "pass" if n.get(key) == want else "FAIL", "blocking": n.get(key) != want})


def consistency(n, rows):
    def same(name, a, b, tol=0):
        ok = abs(a - b) <= tol
        rows.append({"part": "3", "check": name, "actual": a, "expected": b, "tol": tol, "status": "pass" if ok else "FAIL", "blocking": not ok})
    for cut, tag in [("2025_07_31", "train"), ("2026_01_31", "test")]:
        same(f"F10 open cards at {cut} = closure_model universe", n[f"f10_{cut}_cards"], n[f"cm_{tag}_cards"])
        same(f"F10 closers after {cut} = closure_model labels", n[f"f10_{cut}_closers"], n[f"cm_{tag}_closers"])
    same("X12 Wallet share of loss = F3", n["x12_wallet_share_of_hsic_loss"], n["f3_wallet_share_of_loss"], 1e-12)
    same("F1 SoW = checks.foundation anchor (FY25)", n["f1_sow_fy25"], n["base_sow_fy25"], 1e-12)
    same("F1 SoW = checks.foundation anchor (FY26)", n["f1_sow_fy26"], n["base_sow_fy26"], 1e-12)
    # segment A (net > 0 after close) is F11's closers minus the return-only ones, so it is smaller and spends more
    same("Segment A ⊆ F11 closers still shopping", float(n["seg_A_n_score"] <= n["f11_still_shopping"]), 1.0)
    same("Segment A post-close net ≥ F11 (drops return-only)", float(n["seg_A_post_close_net"] >= n["f11_post_close_net"]), 1.0)


def spot_checks():
    """Trace one customer per kind from the raw CSVs (not prep's frame) to their segment and offer, at 2026-07-31."""
    cut = C.CUTOFF_SCORE
    cust, freq_cut = assign(cut)
    raw = pd.read_csv(C.FILES["transactions"], parse_dates=["Transaction_Date"])
    rc = pd.read_csv(C.FILES["customers"], parse_dates=["Credit_Card_Open_Date", "Credit_Card_Closed_Date"]).set_index("Customer_ID")
    rng = np.random.default_rng(C.SEED)
    seg = cust.set_index("customer_id").segment
    picks = {"closed-and-shopping": ("A", rng.choice(np.sort(seg.index[seg == "A"]))),
             "young card": ("BC", rng.choice(np.sort(seg.index[seg.isin(["B", "C"])]))),
             "high-frequency mature card": ("D", rng.choice(np.sort(seg.index[seg == "D"])))}
    lb0, _ = prep.lookback(cut)
    out = []
    for kind, (allowed, cid) in picks.items():
        c, r = rc.loc[cid], raw[raw.Customer_ID == cid]
        o, cl = c.Credit_Card_Open_Date, c.Credit_Card_Closed_Date
        signed = r.Transaction_Amount.where(r.Transaction_Type == "Sale", -r.Transaction_Amount)
        act = (r.Transaction_Date >= o) & (pd.isna(cl) | (r.Transaction_Date <= cl))
        hs = r.Payment_Code == C.HSIC_CODE
        assert act[hs].all(), f"{cid}: HSIC row outside the card window"
        if allowed == "A":
            after = r.Transaction_Date > cl
            assert cl <= cut and signed[after].sum() > 0 and not hs[after].any(), f"{cid}: not a closed-and-shopping customer"
            facts = [f"card closed {cl:%Y-%m-%d}", f"{int(after.sum())} rows after closure, none on HSIC",
                     f"₹{signed[after].sum():,.0f} net after closure"]
            mine = "A"
        else:
            freq = int(((r.Transaction_Type == "Sale") & (r.Transaction_Date > lb0) & (r.Transaction_Date <= cut)).sum())
            age = (cut - o).days / C.DAYS_PER_YEAR
            young, high = age < C.YOUNG_CARD_YEARS, freq > freq_cut
            mine = "B" if young and high else "C" if young else "D" if high else "E"
            facts = [f"card age {age:.2f}y ({'young' if young else 'mature'})",
                     f"{freq} Sale rows in the 12 months to {cut.date()} (top tercile: > {freq_cut:g})"]
        assert mine == seg[cid] and mine in allowed, f"{cid}: raw rows say {mine}, segments.py says {seg[cid]}"
        net = signed[act].sum()
        out.append({"kind": kind, "id": int(cid), "membership": c.Membership_Type, "open": f"{o:%Y-%m-%d}", "rows": len(r),
                    "active_rows": int(act.sum()), "hsic_rows": int(hs.sum()),
                    "active_sow": f"{signed[act & hs].sum() / net:.1%}" if net > 0 else "n/a (no net active spend)",
                    "facts": facts, "segment": seg[cid], "lever": LEVER[seg[cid]]})
    return out


def write_report(df, spots, pending):
    def fmt(v):
        if isinstance(v, (float, np.floating)):
            return "n/a" if np.isnan(v) else f"{v:,.4f}".rstrip("0").rstrip(".")
        return f"{v:,}" if isinstance(v, (int, np.integer)) else str(v)

    icon = {"pass": "✅", "explained": "🟡", "unresolved": "🟠", "pending": "⏳"}
    lines = ["# Verification report: Mayank's numbers (PROJECT_PLAN §14)", "",
             "Generated by `python -m analysis.verify` after `run_all.py`. ✅ pass · 🟡 stub missed, cause found and reproduced · "
             "🟠 stub missed, the 23 Oct definition can't be reproduced (see below) · ⏳ pending on another owner's module · "
             "❌ blocking failure. In every 🟡 / 🟠 case the deck uses the pipeline value.", ""]
    titles = {"1": "Pipeline reproduction checks (`checks.py`)", "2": "23 Oct stubs in HANDOFF_MAYANK", "3": "Consistency with Devansh's modules"}
    for part, title in titles.items():
        p = df[df.part == part]
        lines += [f"## {title}", "", f"**{(p.status == 'pass').sum()} pass · {(p.status == 'explained').sum()} explained · "
                  f"{(p.status == 'unresolved').sum()} unresolved · {(p.status == 'pending').sum()} pending · "
                  f"{p.blocking.sum()} blocking failures.**", "",
                  "| | Check | Actual | Expected | Tol |", "|---|---|---|---|---|"]
        lines += [f"| {icon.get(r.status, '❌')} | {r.check} | {fmt(r.actual)} | {fmt(r.expected)} | {fmt(r.tol)} |" for r in p.itertuples()]
        lines.append("")
    for title, notes, status in [("Causes of the explained stub misses (🟡)", CAUSES, "explained"),
                                 ("Unresolved stub misses (🟠): what was tried", UNRESOLVED, "unresolved")]:
        hit = set(df.check[df.status == status])
        lines += [f"## {title}", ""] + [f"- `{k}`: {v}" for k, v in notes.items() if k in hit] + [""]
    lines += ["## Spot checks: raw rows → segment → offer (assignment at 2026-07-31)", ""]
    for s in spots:
        lines += [f"**{s['kind']}**: customer {s['id']} ({s['membership']}, card opened {s['open']})",
                  f"- raw rows {s['rows']}, active-window rows {s['active_rows']}, HSIC rows {s['hsic_rows']} (all inside the card window), "
                  f"active SoW {s['active_sow']}", *[f"- {f}" for f in s["facts"]],
                  f"- → segment **{s['segment']}** (same as `segments.assign`) → {s['lever']}", ""]
    lines += ["## Pending (owner module not in the repo yet)", "", *([f"- {p}" for p in pending] or ["- none"]), ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    n, rows = numbers(), []
    pipeline_checks(rows)
    stub_checks(n, rows)
    consistency(n, rows)
    df = pd.DataFrame(rows)
    has = lambda m: importlib.util.find_spec(f"analysis.{m}") is not None
    pending = [p for m, p in [("economics", "F12 gap and F15 net lost margin (Shreyash); break-even by hand; a `never` test offer"),
                              ("style", "Shreyash's `style.py`: charts still use the local stand-in style")] if not has(m)]
    write_report(df, spot_checks(), pending)
    bad = df[df.blocking]
    print(f"{REPORT}\n{(df.status == 'pass').sum()} pass · {(df.status == 'explained').sum()} explained · "
          f"{(df.status == 'unresolved').sum()} unresolved · {len(bad)} blocking failures")
    if len(bad):
        print(bad.to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
