"""Hypothesis tests X3, X4, X8-X14, X17 (PROJECT_PLAN §4, HANDOFF_MAYANK §3). Owner: Mayank.

Each x* function returns a plain dict of named numbers including `x<N>_verdict`, decided by the
thresholds in config.VERDICT (selection_log §3, §4, §7). The *_table helpers feed the slide 6-7 charts.
Only aggregates, never customer rows.

    python -m analysis.experiments_h
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis import config as C, prep
from analysis.experiments_f import CASH, FY_A, FY_B, WALLET, f3_mix_shift, mix_by_fy, plain, slug, sow_by

V = C.VERDICT


def monthly_hsic_row_share():
    """The portfolio's HSIC row share per calendar month (active rows): the calendar-matched baseline."""
    return prep.active(prep.load().txn).groupby("month").is_hsic.mean()


def _ci(diff):
    """Mean and 95% normal-approximation CI over customers."""
    m, h = diff.mean(), 1.96 * diff.std() / np.sqrt(len(diff))
    return m, m - h, m + h


# ---------------------------------------------------------------- X3: silent attrition vs two nulls (selection_log §3)
def silent_attrition_table():
    """Universe: card open from lookback start to horizon end, ≥ 1 HSIC row in the lookback, ≥ 1 active row in the horizon.

    Observed zero-HSIC rate in the 6-month horizon vs (a) the fixed-share null (1 - own lookback HSIC row share)^n
    and (b) the time-aware null (1 - portfolio HSIC row share in the horizon)^n, n = the customer's horizon rows.
    The 2025-01-31 lookback starts before the data, so it only sees Aug 2024-Jan 2025.
    """
    d = prep.load()
    act, c = prep.active(d.txn), d.cust
    rows = []
    for cut in C.SILENT_ATTRITION_CUTOFFS:
        lb0, _ = prep.lookback(cut)
        h0, h1 = prep.horizon(cut)
        ids = c.customer_id[c.has_card & (c.open_date <= lb0) & (c.close_date.isna() | (c.close_date >= h1))]
        s = act[act.customer_id.isin(ids)]
        lb = s[prep.in_window(s.date, lb0, cut)].groupby("customer_id").is_hsic.agg(["sum", "size"])
        lb = lb[lb["sum"] >= 1]
        hz = s[prep.in_window(s.date, h0, h1)].groupby("customer_id").is_hsic.agg(n="size", hs="sum")
        e = hz.join(lb, how="inner")
        p = act[prep.in_window(act.date, h0, h1)].is_hsic.mean()
        obs = (e.hs == 0).astype(float)
        q_fixed, q_time = (1 - e["sum"] / e["size"]) ** e.n, (1 - p) ** e.n
        fx, tm = _ci(obs - q_fixed), _ci(obs - q_time)
        rows.append({"cutoff": cut, "customers": len(e), "observed": obs.mean(), "portfolio_share": p,
                     "expected_fixed": q_fixed.mean(), "expected_time": q_time.mean(),
                     "excess_fixed": fx[0], "excess_fixed_lo": fx[1], "excess_fixed_hi": fx[2],
                     "excess_time": tm[0], "excess_time_lo": tm[1], "excess_time_hi": tm[2]})
    return pd.DataFrame(rows)


def x3_silent_attrition():
    t = silent_attrition_table()
    out = {}
    for r in t.itertuples():
        k = slug(r.cutoff.date())
        out |= {f"x3_customers_{k}": r.customers, f"x3_observed_zero_{k}": r.observed,
                f"x3_expected_fixed_{k}": r.expected_fixed, f"x3_expected_time_{k}": r.expected_time,
                f"x3_excess_fixed_{k}": r.excess_fixed, f"x3_excess_time_{k}": r.excess_time,
                f"x3_excess_time_lo_{k}": r.excess_time_lo, f"x3_excess_time_hi_{k}": r.excess_time_hi}
    concentrated = ((t.excess_time >= V["x3_excess_min"]) & (t.excess_time_lo > 0)).sum()
    out["x3_verdict"] = "concentrated" if concentrated >= V["x3_cutoffs_needed"] else "universal"
    return out


# ---------------------------------------------------------------- X4: pre-closure decay, raw vs calendar-adjusted (§4)
def pre_closure_rows():
    """Active rows of every closed card in its last 12 months, with the same-month portfolio share.

    Includes the 145 cards whose known close date (1-5 Aug 2026) falls just after the last transaction date.
    """
    act = prep.active(prep.load().txn)
    cl = act[act.close_date.notna()].copy()
    cl["months_before"] = (cl.close_date - cl.date).dt.days // 30      # 30-day months, as in experiments_ml.x7
    cl = cl[cl.months_before <= 12]
    cl["expected"] = cl.month.map(monthly_hsic_row_share())
    cl["excess"] = cl.is_hsic - cl.expected
    return cl


def pre_closure_table():
    g = pre_closure_rows().groupby("months_before").agg(raw=("is_hsic", "mean"), expected=("expected", "mean"),
                                                        excess=("excess", "mean"), rows=("is_hsic", "size"))
    g["chance_band"] = 1.96 * np.sqrt(g.expected * (1 - g.expected) / g.rows)
    return g


def x4_pre_closure():
    cl = pre_closure_rows()
    g = pre_closure_table()
    fit = sm.OLS(cl.excess.to_numpy(), sm.add_constant(cl.months_before.to_numpy(dtype=float))).fit()
    lo, hi = fit.conf_int()[1]
    near = cl[cl.months_before <= 2].excess.mean()
    decay = (lo > 0 or hi < 0) and near <= V["x4_excess_max"]
    return {"x4_rows": len(cl), "x4_raw_m12": g.raw[12], "x4_raw_m0": g.raw[0],
            "x4_excess_min_pp": g.excess.min() * 100, "x4_excess_max_pp": g.excess.max() * 100,
            "x4_excess_m0_2_pp": near * 100, "x4_slope_pp_per_month": fit.params[1] * 100,
            "x4_slope_ci_lo_pp": lo * 100, "x4_slope_ci_hi_pp": hi * 100,
            "x4_verdict": "decay before closure" if decay else "no decay beyond the calendar trend"}


# ---------------------------------------------------------------- slide 6 slice table, X8, X9
def slice_table():
    """FY25 vs FY26 SoW in every slice: is the decline concentrated anywhere? Gender is left out (fairness check only)."""
    d = prep.load()
    a = prep.active(d.txn).merge(d.cust[["customer_id", "membership", "age", "credit_limit", "apr"]], on="customer_id")
    a["age_band"] = pd.cut(a.age, [17, 25, 35, 45, 60], labels=["18-25", "26-35", "36-45", "46-60"])
    a["limit_band"] = pd.qcut(a.credit_limit, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    a["apr_band"] = pd.qcut(a.apr, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    a["vintage"] = a.open_date.dt.year.astype(str)
    a["closer"] = np.where(a.close_date.notna(), "closes in data", "stays open")
    dims = {"Membership": "membership", "Age": "age_band", "Credit limit": "limit_band", "APR": "apr_band",
            "Card vintage": "vintage", "Category": "category", "Closer": "closer"}
    rows = []
    for name, col in dims.items():
        s = sow_by(a, [col, "fy"]).unstack()
        rows += [{"dimension": name, "level": str(k), "sow_fy25": r[FY_A], "sow_fy26": r[FY_B]} for k, r in s.iterrows()]
    t = pd.DataFrame(rows).dropna()
    t["change_pp"] = (t.sow_fy26 - t.sow_fy25) * 100
    return t


def x8_prime():
    act = prep.active(prep.load().txn)
    act = act.assign(membership=np.where(act.is_prime, "Prime", "Non-Prime"))
    fy = sow_by(act, ["membership", "fy"]).unstack()
    q = sow_by(act, ["membership", "fq_label"]).unstack()
    X = pd.get_dummies(act.month.astype(str), drop_first=True).assign(prime=act.is_prime).astype(float)
    fit = sm.Logit(act.is_hsic.astype(float).to_numpy(), sm.add_constant(X)).fit(disp=0)
    lo, hi = fit.conf_int().loc["prime"]
    gaps = (fy.loc["Prime"] - fy.loc["Non-Prime"]).abs()
    out = {f"x8_sow_fy{y % 100}_{slug(m)}": fy.loc[m, y] for m in fy.index for y in C.FISCAL_YEARS}
    out |= {f"x8_sow_{slug(q.columns[i])}_{slug(m)}": q.loc[m].iloc[i] for m in q.index for i in (0, -1)}
    out |= {"x8_gap_fy25_pp": gaps[FY_A] * 100, "x8_gap_fy26_pp": gaps[FY_B] * 100,
            "x8_prime_logit_coef": fit.params["prime"], "x8_prime_logit_ci_lo": lo, "x8_prime_logit_ci_hi": hi,
            "x8_verdict": "rejected" if (gaps <= V["x8_gap_max"]).all() else "supported"}
    return out


def x9_category():
    act = prep.active(prep.load().txn)
    pooled = sow_by(act, "category")
    fy = sow_by(act, ["category", "fy"]).unstack()
    spread = fy.max() - fy.min()
    return {"x9_sow_pooled_min": pooled.min(), "x9_sow_pooled_max": pooled.max(),
            "x9_sow_fy25_min": fy[FY_A].min(), "x9_sow_fy25_max": fy[FY_A].max(),
            "x9_sow_fy26_min": fy[FY_B].min(), "x9_sow_fy26_max": fy[FY_B].max(),
            "x9_spread_fy25_pp": spread[FY_A] * 100, "x9_spread_fy26_pp": spread[FY_B] * 100,
            "x9_verdict": "rejected" if (spread <= V["x9_spread_max"]).all() else "supported"}


# ---------------------------------------------------------------- X10-X14, X17 (appendix)
def x10_credit_limit():
    """Monthly MetroMart net spend (all methods, active window) ÷ the card's credit limit, per customer-month."""
    d = prep.load()
    g = prep.active(d.txn).groupby(["customer_id", "month"]).net.sum().reset_index()
    u = g.net / g.customer_id.map(d.cust.set_index("customer_id").credit_limit)
    share = (u >= V["x10_utilisation"]).mean()
    return {"x10_util_median": u.median(), "x10_util_max": u.max(), "x10_months_ge_50pct": int((u >= V["x10_utilisation"]).sum()),
            "x10_share_months_ge_50pct": share, "x10_customer_months": len(u),
            "x10_verdict": "rejected" if share < V["x10_month_share_max"] else "supported"}


def monthly_sales_index():
    """Monthly MetroMart net sales (all customers, all methods), indexed to the 24-month mean = 100."""
    m = prep.load().txn.groupby("month").net.sum()
    return m / m.mean() * 100


def x11_festive():
    idx = monthly_sales_index()
    return {"x11_index_min": idx.min(), "x11_index_max": idx.max(), "x11_peak_month": str(idx.idxmax()),
            "x11_oct_nov_index_mean": idx[idx.index.month.isin([10, 11])].mean(),
            "x11_verdict": "rejected" if idx.max() <= V["x11_index_max"] else "supported"}


def x12_wallet():
    t = prep.load().txn
    nc = mix_by_fy(t[~t.has_card])
    share = f3_mix_shift()[f"f3_{slug(WALLET)}_share_of_loss"]
    return {"x12_wallet_share_of_hsic_loss": share,
            "x12_wallet_share_noncard_fy25": nc.loc[FY_A, WALLET], "x12_wallet_share_noncard_fy26": nc.loc[FY_B, WALLET],
            "x12_cash_upi_share_noncard_fy25": nc.loc[FY_A, CASH], "x12_cash_upi_share_noncard_fy26": nc.loc[FY_B, CASH],
            "x12_verdict": "rejected" if share < V["x12_wallet_share_max"] else "supported"}


def x13_never_activated():
    """Cardholders with active rows but no HSIC row, vs chance if every row used HSIC at the portfolio's monthly rate."""
    act = prep.active(prep.load().txn)
    lq = np.log1p(-act.month.map(monthly_hsic_row_share()).to_numpy())
    g = act.assign(lq=lq).groupby("customer_id").agg(hs=("is_hsic", "sum"), lq=("lq", "sum"))
    obs, exp = (g.hs == 0).mean(), np.exp(g.lq).mean()
    return {"x13_n": len(g), "x13_zero_hsic_observed": obs, "x13_zero_hsic_expected": exp, "x13_excess_pp": (obs - exp) * 100,
            "x13_verdict": "rejected" if obs - exp <= V["x13_excess_max"] else "supported"}


def x14_mix_persistence():
    """FY25 -> FY26 persistence of big-ticket (≥ ₹3k) and Grocery + Electronics shares of purchases (≥ 3 in each FY)."""
    p = prep.purchases(prep.load().txn)
    p = p.assign(big=p.ticket_band.isin(["3k-10k", "capped"]), ge=p.category_code.isin([C.GROCERY, C.ELECTRONICS]))
    g = p.groupby(["customer_id", "fy"]).agg(n=("big", "size"), big=("big", "mean"), ge=("ge", "mean")).unstack()
    g = g[(g[("n", FY_A)] >= C.MIN_PURCHASES_PER_PERIOD) & (g[("n", FY_B)] >= C.MIN_PURCHASES_PER_PERIOD)]
    r_big = np.corrcoef(g[("big", FY_A)], g[("big", FY_B)])[0, 1]
    r_ge = np.corrcoef(g[("ge", FY_A)], g[("ge", FY_B)])[0, 1]
    return {"x14_r_big_ticket_share": r_big, "x14_r_grocery_electronics_share": r_ge, "x14_n": len(g),
            "x14_verdict": "rejected" if max(r_big, r_ge) < V["x14_persistence_min"] else "supported"}


def x17_returns():
    r = prep.load().txn.groupby("payment_short").is_return.mean()
    return {"x17_return_share_min": r.min(), "x17_return_share_max": r.max(),
            "x17_spread_pp": (r.max() - r.min()) * 100} | {f"x17_return_share_{slug(k)}": v for k, v in r.items()} | {
            "x17_verdict": "no signal" if r.max() - r.min() <= V["x17_spread_max"] else "returns differ by method"}


X_FUNCS = [x3_silent_attrition, x4_pre_closure, x8_prime, x9_category, x10_credit_limit, x11_festive,
           x12_wallet, x13_never_activated, x14_mix_persistence, x17_returns]


def run():
    out = {}
    for f in X_FUNCS:
        out |= {k: plain(v) for k, v in f().items()}
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:42s} {v:.4f}" if isinstance(v, float) else f"{k:42s} {v}")
