"""Second, independent verification of Mayank's work. Owner: Mayank.

verify.py checks the numbers against the plan and the handoff. This checks the code itself:
A. independent re-implementation from the raw CSVs (no prep, no experiment code) -> must match key_numbers.json
B. internal invariants   C. determinism   D. artifacts (charts, key_numbers, notebook, public-repo guard)
E. deck text (deck/slides_04-07.md)   F. overlap with the first EDA (outputs/eda/eda_numbers.json)
Writes outputs/verification/second_check_report.md and exits non-zero if any check failed.

    python -m analysis.verify_second        (after run_all.py, charts_story and the notebook)
"""
import fnmatch
import json
import re
import sys

import numpy as np
import pandas as pd
from PIL import Image

from analysis import charts_story as CH, config as C, experiments_f as F, experiments_h as H

REPORT = C.OUTPUTS / "verification" / "second_check_report.md"
ROWS = []
CHARTS = ["04_sow_trend", "04_per_card", "04_bridge", "05_mix_shift", "05_ticket_bands", "05_capped_mix",
          "06_slices", "06_gate", "06_band_movement", "07_silent_null", "07_decay_raw_vs_adj", "07_kmeans"]


def check(section, name, ok, detail=""):
    ROWS.append({"section": section, "check": name, "ok": bool(ok), "detail": detail})


def same(section, name, independent, pipeline, tol=1e-9):
    check(section, name, abs(independent - pipeline) <= tol * max(1, abs(pipeline)),
          f"independent {independent:.6g} · pipeline {pipeline:.6g}")


# ---------------------------------------------------------------- A. independent re-implementation
def independent(n):
    tx = pd.read_csv(C.FILES["transactions"], parse_dates=["Transaction_Date"])
    cu = pd.read_csv(C.FILES["customers"], parse_dates=["Credit_Card_Open_Date", "Credit_Card_Closed_Date"]).set_index("Customer_ID")
    od, cd = tx.Customer_ID.map(cu.Credit_Card_Open_Date), tx.Customer_ID.map(cu.Credit_Card_Closed_Date)
    d, amt, code, cat = tx.Transaction_Date, tx.Transaction_Amount.to_numpy(), tx.Payment_Code.to_numpy(), tx.Category_Code.to_numpy()
    ids = tx.Customer_ID.to_numpy()
    sale = (tx.Transaction_Type == "Sale").to_numpy()
    net = np.where(sale, amt, -amt)
    act = (od.notna() & (d >= od) & (cd.isna() | (d <= cd))).to_numpy()
    hs = code == 3
    fy = (d.dt.year + (d.dt.month >= 8)).to_numpy()
    prime = tx.Customer_ID.map(cu.Membership_Type).to_numpy() == "Prime"
    rate = np.where(prime & (cat == 1), .05, np.where(prime & (cat == 2), .03, .01))
    A = "A. Independent re-implementation"

    def sow(m):
        return net[m & hs].sum() / net[m].sum()
    same(A, "F1 SoW FY25", sow(act & (fy == 2025)), n["f1_sow_fy25"])
    same(A, "F1 SoW FY26", sow(act & (fy == 2026)), n["f1_sow_fy26"])

    o, c = cu.Credit_Card_Open_Date, cu.Credit_Card_Closed_Date
    stay = np.isin(ids, cu.index[(o <= "2024-08-01") & (c.isna() | (c >= "2026-07-31"))])
    st = act & stay
    s25a, s26a, s25s, s26s = sow(act & (fy == 2025)), sow(act & (fy == 2026)), sow(st & (fy == 2025)), sow(st & (fy == 2026))
    same(A, "F2 Bridge leavers (pp)", (s25s - s25a) * 100, n["f2_leaver_pp"])
    same(A, "F2 Bridge stayers (pp)", (s26s - s25s) * 100, n["f2_stayer_pp"])
    same(A, "F2 Bridge joiners (pp)", (s26a - s26s) * 100, n["f2_joiner_pp"])

    def share(m, k):
        return net[m & (code == k)].sum() / net[m].sum()
    loss = share(st & (fy == 2025), 3) - share(st & (fy == 2026), 3)
    same(A, "F3 Cash/UPI share of HSIC loss", (share(st & (fy == 2026), 4) - share(st & (fy == 2025), 4)) / loss,
         n["f3_cash_upi_share_of_loss"])

    m26 = act & (fy == 2026)
    ge = m26 & ~hs & prime & np.isin(cat, [1, 2])
    same(A, "F8 Prime G+E left on the table FY26", (net[ge] * rate[ge]).sum(), n["f8_prime_ge_left_on_table"])
    same(A, "F8 rewards earned FY26", (net[m26 & hs] * rate[m26 & hs]).sum(), n["f8_rewards_earned_fy26"])

    for cut, end in [("2025-07-31", "2026-01-31"), ("2026-01-31", "2026-07-31")]:
        cut_, end_, k = pd.Timestamp(cut), pd.Timestamp(end), cut.replace("-", "_")
        op = o.notna() & (o <= cut_) & (c.isna() | (c > cut_))
        age = ((cut_ - o[op]).dt.days / 365.25).to_numpy()
        lab = (c[op] <= end_).to_numpy()          # NaT compares False: still open
        b = np.digitize(age, [.5, 1, 2, 3], right=True)   # bins are right-closed
        check(A, f"F10 open cards {cut}", op.sum() == n[f"f10_{k}_cards"], f"{op.sum()} vs {n[f'f10_{k}_cards']}")
        check(A, f"F10 closers {cut}", lab.sum() == n[f"f10_{k}_closers"], f"{lab.sum()} vs {n[f'f10_{k}_closers']}")
        for i, name in enumerate(["lt6m", "6_12m", "1_2y", "2_3y", "3yplus"]):
            same(A, f"F10 6m closure {cut} {name}", lab[b == i].mean(), n[f"f10_{k}_closure_{name}"])

    post = (cd.notna() & (d > cd)).to_numpy()
    same(A, "F11 post-closure net ₹", net[post].sum(), n["f11_post_close_net"])
    check(A, "F11 closed-and-shopping customers", len(np.unique(ids[post])) == n["f11_still_shopping"])

    aug = ((d >= "2024-08-01") & (d <= "2024-08-31")).to_numpy()
    cards_aug = ((o <= "2024-08-31") & (c.isna() | (c >= "2024-08-01"))).sum()
    check(A, "F14 cards active Aug 2024", cards_aug == n["f14_aug24_cards"], f"{cards_aug}")
    same(A, "F14 net per card Aug 2024", net[act & aug].sum() / cards_aug, n["f14_aug24_net_per_card"])
    same(A, "F14 HSIC per card Aug 2024", net[act & aug & hs].sum() / cards_aug, n["f14_aug24_hsic_per_card"])

    small = act & sale & (amt <= 1000)
    for y in (2025, 2026):
        same(A, f"F5 HSIC row share <1k FY{y % 100}", hs[small & (fy == y)].mean(), n[f"f5_hsic_share_fy{y % 100}_lt1k"])

    # X3 at 2026-01-31 (selection_log §3): written row-wise with numpy
    lb0, cut, h1 = pd.Timestamp("2025-01-31"), pd.Timestamp("2026-01-31"), pd.Timestamp("2026-07-31")
    inu = np.isin(ids, cu.index[o.notna() & (o <= lb0) & (c.isna() | (c >= h1))]) & act
    lb = inu & (d > lb0).to_numpy() & (d <= cut).to_numpy()
    hz_all = act & (d > cut).to_numpy() & (d <= h1).to_numpy()
    hz = inu & hz_all
    assert d[lb].max() <= cut < d[hz].min(), "X3 lookback/horizon overlap"
    g = pd.DataFrame({"id": ids[lb], "h": hs[lb]}).groupby("id").h.agg(["sum", "size"])
    g = g[g["sum"] >= 1]
    e = pd.DataFrame({"id": ids[hz], "h": hs[hz]}).groupby("id").h.agg(n="size", hs="sum").join(g, how="inner")
    p = hs[hz_all].mean()
    obs = (e.hs == 0).astype(float)
    same(A, "X3 fixed-share excess 2026-01-31", (obs - (1 - e["sum"] / e["size"]) ** e.n).mean(), n["x3_excess_fixed_2026_01_31"])
    same(A, "X3 time-aware excess 2026-01-31", (obs - (1 - p) ** e.n).mean(), n["x3_excess_time_2026_01_31"])
    check(A, "X3 customers 2026-01-31", len(e) == n["x3_customers_2026_01_31"], f"{len(e)}")

    ym = d.dt.year.to_numpy() * 12 + d.dt.month.to_numpy()
    months, inv = np.unique(ym[act], return_inverse=True)
    p_month = np.bincount(inv, weights=hs[act]) / np.bincount(inv)
    z = pd.DataFrame({"id": ids[act], "h": hs[act], "lq": np.log(1 - p_month[inv])}).groupby("id").agg(h=("h", "sum"), lq=("lq", "sum"))
    same(A, "X13 zero-HSIC observed", (z.h == 0).mean(), n["x13_zero_hsic_observed"])
    same(A, "X13 zero-HSIC expected", np.exp(z.lq).mean(), n["x13_zero_hsic_expected"])

    # Devansh's X1 SoW-band table, rebuilt from the raw rows: an outside check on the numbers slide 6 shows
    f = pd.DataFrame({"id": ids[act], "fy": fy[act], "h": (net * hs)[act], "net": net[act], "p": sale[act]})
    f = f.groupby(["id", "fy"]).sum().unstack(fill_value=0)          # a missing FY is 0 purchases, not skipped
    f = f[(f.p.min(axis=1) >= 3) & (f.net.min(axis=1) > 0)]
    r25, r26 = f.h[2025] / f.net[2025], f.h[2026] / f.net[2026]
    q1, q2 = np.quantile(r25[r25 > 0], [1 / 3, 2 / 3])

    def band(r):
        return np.where(r <= 0, 0, 1 + (r > q1) + (r > q2))          # Zero = no net HSIC spend
    zero = pd.Series(band(r26) == 0).groupby(band(r25)).mean()
    check(A, "X1 band table universe (Devansh)", len(f) == n["x1_sow_filter_n"], f"{len(f)}")
    same(A, "X1 band cut low/mid (Devansh)", q1, n["x1_band_edges_low_mid"])
    same(A, "X1 band min to Zero (Devansh)", zero.min(), n["x1_band_to_zero_min"])
    same(A, "X1 band max to Zero (Devansh)", zero.max(), n["x1_band_to_zero_max"])


# ---------------------------------------------------------------- B. invariants
def invariants(n):
    B = "B. Internal invariants"
    from analysis import prep
    d = prep.load()
    act = prep.active(d.txn)
    check(B, "Payment-mix shares sum to 1 per FY", np.allclose(F.mix_by_fy(act).sum(axis=1), 1))
    loss = sum(v for k, v in n.items() if re.fullmatch(r"f3_.+_share_of_loss", k))
    check(B, "F3 shares of HSIC's loss sum to 100%", np.isclose(loss, 1), f"{loss:.6f}")
    check(B, "F11 post-closure mix sums to 1", np.isclose(sum(v for k, v in n.items() if k.startswith("f11_mix_")), 1))
    b = F.bridge_table()
    check(B, "F2 Bridge reconciles to FY26 SoW", np.isclose(b.iloc[0] + b.iloc[1:4].sum(), b.iloc[4]) and np.isclose(b.iloc[4], n["f1_sow_fy26"]))
    check(B, "F1 eight fiscal quarters", len(F.quarterly_sow_table()) == 8)
    check(B, "F14 24 monthly rows", len(F.per_card_monthly_table()) == 24)
    check(B, "F5 ticket shares sum to 1 per band and FY", np.allclose(F.ticket_band_table().sum(axis=1), 1))
    check(B, "F7 capped mix sums to 1 per FY", np.allclose(F.capped_mix_table().sum(axis=1), 1))
    for cut in (C.CUTOFF_TRAIN, C.CUTOFF_TEST):
        u = prep.snapshot_universe(cut)
        check(B, f"F10 every open card in an age bin ({cut.date()})", u.card_age_bin.notna().all() and (u.card_age_years >= 0).all())
        check(B, f"F10 labels only after the cutoff ({cut.date()})", (u.close_date[u.closed_6m.astype(bool)] > cut).all())
    st = H.slice_table()
    check(B, "Every slice's SoW fell 7-11pp (slide 6 headline)", st.change_pp.between(-11.5, -6.5).all(),
          f"range {st.change_pp.min():.1f} to {st.change_pp.max():.1f}pp")
    sa = H.silent_attrition_table()
    check(B, "X3 shares are probabilities", sa[["observed", "expected_fixed", "expected_time"]].stack().between(0, 1).all())
    check(B, "X3 fixed-share null below observed at every cutoff (the trend)", (sa.excess_fixed > 0).all())
    pc = H.pre_closure_table()
    check(B, "X4 covers months 0..12", list(pc.index) == list(range(13)))
    verdicts = [k for k in n if re.fullmatch(r"x(3|4|8|9|1[0-4]|17)_verdict", k)]
    check(B, "Every X test of mine returns a verdict", len(verdicts) == 10, ", ".join(sorted(verdicts)))


# ---------------------------------------------------------------- C-F
def determinism(n):
    m = F.run() | H.run()
    diff = [k for k in m if n.get(k) != m[k]]   # json round-trips floats exactly
    check("C. Determinism", "A fresh in-process run equals key_numbers.json", not diff, ", ".join(diff[:5]))
    m2 = F.run() | H.run()
    check("C. Determinism", "Two runs in a row give identical numbers", m == m2)


def artifacts(n):
    D = "D. Artifacts"
    for name in CHARTS:
        p = C.CHARTS / f"{name}.png"
        size = Image.open(p).size if p.exists() else None
        check(D, f"Chart {name}.png exists, 16:9", size and abs(size[0] / size[1] - 16 / 9) < .01, f"{size}" if size else "missing")
    check(D, "One chart function per expected chart", len(CH.CHARTS) == len(CHARTS))
    stray = sorted(p.name for p in C.CHARTS.glob("0[4-7]_*.png") if p.stem not in CHARTS)
    check(D, "No stray slide 4-7 charts", not stray, ", ".join(stray))
    nb = json.loads((C.ROOT / "notebooks" / "story.ipynb").read_text(encoding="utf-8"))
    errs = [o for cell in nb["cells"] for o in cell.get("outputs", []) if o.get("output_type") == "error"]
    ran = all(cell.get("execution_count") for cell in nb["cells"] if cell["cell_type"] == "code")
    check(D, "Notebook executed, no error cells", ran and not errs)
    mine = [k for k in n if re.match(r"(f(1[0-4]?|[2-9])|x(3|4|8|9|1[0-4]|17))_", k)]
    labels = {k: v["label"] for k, v in json.loads((C.OUTPUTS / "key_numbers.json").read_text(encoding="utf-8")).items()}
    check(D, "All my keys are labelled Measured", all(labels[k] == "Measured" for k in mine), f"{len(mine)} keys")
    bad = [p for p in (C.OUTPUTS / "verification").glob("*.csv")]
    check(D, "No customer-level CSV written by my scripts", not bad, ", ".join(map(str, bad)))


def deck_text(n):
    E = "E. Deck text (deck/slides_04-07.md)"
    md = (C.ROOT / "deck" / "slides_04-07.md").read_text(encoding="utf-8")
    slides = md.split("## Numbers that differ")[0].split("## Slide 4")[1]
    bad = re.findall(r"\bv4\b|blueprint|pre-?regist", slides, flags=re.I)
    check(E, "No v4 / blueprint / pre-registration on slides", not bad, ", ".join(bad))
    why = [line for line in slides.splitlines() if "**Why" in line]
    check(E, "Every 'Why' line labelled Hypothesis", why and all("**H**" in line for line in why), f"{len(why)} lines")
    check(E, "Silent attrition never called 'rejected'", not re.search(r"silent attrition[^.\n]*rejected", slides, flags=re.I))
    missing = []
    for tok in re.findall(r"`([^`]+)`", md):
        if tok.endswith(".png"):
            missing += [] if (C.CHARTS / tok).exists() else [tok]
        elif tok.endswith(".csv"):
            missing += [] if (C.ROOT / tok).exists() else [tok]
        elif re.fullmatch(r"[a-z0-9_*]+", tok) and not fnmatch.filter(n, tok):
            missing.append(tok)
    check(E, "Every cited key, chart and table exists", not missing, ", ".join(missing))

    def pct(k, dp=1):
        return f"{n[k] * 100:.{dp}f}%"
    shown = {"f1_sow_fy25": pct("f1_sow_fy25"), "f1_sow_fy26": pct("f1_sow_fy26"), "f1_sow_fy25_q1": pct("f1_sow_fy25_q1"),
             "f1_sow_fy26_q4": pct("f1_sow_fy26_q4"), "f1_slope": f"−{-n['f1_slope_pp_per_quarter']:.1f}pp a quarter",
             "f14_aug24_net_per_card": f"₹{n['f14_aug24_net_per_card']:,.0f}", "f14_may26_net_per_card": f"₹{n['f14_may26_net_per_card']:,.0f}",
             "f14_aug24_hsic_per_card": f"₹{n['f14_aug24_hsic_per_card']:,.0f}", "f14_may26_hsic_per_card": f"₹{n['f14_may26_hsic_per_card']:,.0f}",
             "f2_leaver_pp": f"+{n['f2_leaver_pp']:.2f}pp", "f2_stayer_pp": f"−{-n['f2_stayer_pp']:.2f}pp",
             "f2_joiner_pp": f"−{-n['f2_joiner_pp']:.2f}pp", "f2_stayers_n": f"{n['f2_stayers_n']:,}",
             "f3_cash_upi_share_of_loss": pct("f3_cash_upi_share_of_loss", 0), "f3_wallet_share_of_loss": pct("f3_wallet_share_of_loss", 0),
             "f4_stayers": f"+{n['f4_cash_upi_change_pp_stayers']:.1f}pp", "f4_noncard": f"+{n['f4_cash_upi_change_pp_noncardholders']:.1f}pp",
             "f6_t1": pct("f6_hsic_row_share_t1"), "f6_t3": pct("f6_hsic_row_share_t3"),
             "f7_fy25": pct("f7_wallet_share_capped_fy25"), "f7_fy26": pct("f7_wallet_share_capped_fy26"),
             "x8_prime_q1": pct("x8_sow_fy25_q1_prime"), "x8_nonprime_q4": pct("x8_sow_fy26_q4_non_prime"),
             "x8_coef": f"−{-n['x8_prime_logit_coef']:.3f}", "x1_split_half_r": f"−{-n['x1_split_half_r']:.3f}",
             "x1_persistence_r": f"+{n['x1_persistence_r']:.3f}", "x1_sow_filter_n": f"{n['x1_sow_filter_n']:,}",
             "x1_band": f"{n['x1_band_to_zero_min'] * 100:.0f}–{n['x1_band_to_zero_max'] * 100:.0f}%",
             "x13_obs": pct("x13_zero_hsic_observed"), "x13_exp": pct("x13_zero_hsic_expected"),
             "x3_fixed": " / ".join(f"{n[f'x3_excess_fixed_{c}'] * 100:+.1f}" for c in ("2025_01_31", "2025_07_31", "2026_01_31")),
             "x3_time": " / ".join(CH.signed(n[f"x3_excess_time_{c}"] * 100) for c in ("2025_01_31", "2025_07_31", "2026_01_31")),
             "x4_raw_m12": pct("x4_raw_m12"), "x4_raw_m0": pct("x4_raw_m0"),
             "x4_range": f"{CH.signed(n['x4_excess_min_pp'])} to {CH.signed(n['x4_excess_max_pp'])}pp",
             "x4_slope": f"{CH.signed(n['x4_slope_pp_per_month'], 2)}pp a month", "kmeans_ari": f"{n['seg_kmeans_ari']:.2f}",
             "kmeans_fy25": f"{n['seg_kmeans_fy25_sow_spread_pp']:.0f}pp", "kmeans_fy26": f"{n['seg_kmeans_fy26_sow_spread_pp']:.1f}pp",
             "kmeans_eta2": f"{n['seg_kmeans_eta2']:.2%}", "x10_median": pct("x10_util_median"),
             "x11": f"{n['x11_index_min']:.0f}–{n['x11_index_max']:.0f}", "x17": pct("x17_return_share_min"),
             "f9": f"{n['f9_rate_first'] * 100:.1f}% (Jul–Sep 2024) → {n['f9_rate_last'] * 100:.1f}%"}
    for b, lab in [("lt1k", "under ₹1k"), ("capped", "capped")]:
        shown[f"f5_{b}"] = f"{lab} {n[f'f5_hsic_share_fy25_{b}'] * 100:.1f} → {n[f'f5_hsic_share_fy26_{b}'] * 100:.1f}%"
    off = [f"{k}={v}" for k, v in shown.items() if v not in md]
    check(E, f"{len(shown)} displayed numbers match key_numbers.json", not off, ", ".join(off))


def eda_overlap(n):
    G = "F. Overlap with the first EDA (same definition)"
    e = json.loads((C.OUTPUTS / "eda" / "eda_numbers.json").read_text(encoding="utf-8"))
    pairs = [("sow_fy25", "f1_sow_fy25", 1e-9), ("sow_fy26", "f1_sow_fy26", 1e-9), ("sow_first_month", "f14_aug24_sow", 1e-9),
             ("forgone_fy26_prime_grocery_electronics", "f8_prime_ge_left_on_table", 1e-6), ("forgone_fy26", "f8_all_left_on_table", 1e-6),
             ("rewards_fy26", "f8_rewards_earned_fy26", 1e-6), ("closed_cards", "f11_closed_cards", 0),
             ("closed_still_shopping", "f11_still_shopping", 0)]
    for ek, mk, tol in pairs:
        same(G, f"{mk} vs EDA {ek}", e[ek], n[mk], tol)
    # the EDA's closure_hazard also counts cards opened inside the quarter, so compare it with closed_any, not F9
    q = F.closure_quarter_table()
    any_rate = q.closed_any / q.open_at_start
    same(G, "closures incl. same-quarter cards, first quarter vs EDA closure_hazard_first_q", e["closure_hazard_first_q"], any_rate.iloc[0])
    same(G, "closures incl. same-quarter cards, last quarter vs EDA closure_hazard_last_q", e["closure_hazard_last_q"], any_rate.iloc[-1])
    same(G, "Cash/UPI change, non-cardholders (pp) vs EDA (2dp)", e["bench_change_pp"]["Cash/UPI"], round(n["f4_cash_upi_change_pp_noncardholders"], 2))
    same(G, "Post-close Wallet share vs EDA (3dp)", e["post_close_mix"]["MetroMart Wallet"], round(n["f11_mix_wallet"], 3))


def write_report():
    df = pd.DataFrame(ROWS)
    lines = ["# Second verification report", "", "Generated by `python -m analysis.verify_second`: an independent re-implementation "
             "from the raw CSVs, invariants, determinism, artifacts, deck text and the EDA overlap.", "",
             f"**{df.ok.sum()} / {len(df)} checks pass.**", ""]
    for sec, part in df.groupby("section", sort=False):
        lines += [f"## {sec} ({part.ok.sum()} / {len(part)})", "", "| | Check | Detail |", "|---|---|---|"]
        lines += [f"| {'✅' if r.ok else '❌'} | {r.check} | {r.detail} |" for r in part.itertuples()]
        lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    return df


if __name__ == "__main__":
    n = {k: v["value"] for k, v in json.loads((C.OUTPUTS / "key_numbers.json").read_text(encoding="utf-8")).items()}
    independent(n); invariants(n); determinism(n); artifacts(n); deck_text(n); eda_overlap(n)
    df = write_report()
    print(f"{REPORT}\n{df.ok.sum()}/{len(df)} pass")
    if not df.ok.all():
        print(df[~df.ok].to_string(index=False))
        sys.exit(1)
