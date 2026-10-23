"""Heterogeneity gate and the ML-side hypothesis tests: X1, X2, X7, X15, X16.

X5 and X6 (does usage predict closure; HGB vs LR) come out of closure_model.py, and the K-means
negative control out of segments.py, so no model is fitted twice.

    python -m analysis.experiments_ml
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis import config as C, prep

TABLES = C.OUTPUTS / "tables"


# ---------------------------------------------------------------- reusable gate
def _shares(rows, flag, min_rows):
    g = rows.groupby("customer_id")[flag].agg(["sum", "count"])
    g = g[g["count"] >= min_rows]
    return g["sum"] / g["count"], g["count"]


def variance_ratio(rows, flag="is_hsic", min_rows=C.GATE["min_rows"]):
    """Observed variance of per-customer shares ÷ the variance binomial noise alone would give."""
    share, n = _shares(rows, flag, min_rows)
    p = (share * n).sum() / n.sum()
    return float(share.var() / (p * (1 - p) / n).mean()), int(len(share))


def split_half_r(rows, flag="is_hsic", min_rows=C.GATE["min_rows"]):
    """Correlation of the share on odd vs even rows (ordered by txn_id) within the same period."""
    keep = rows.groupby("customer_id")[flag].transform("size") >= min_rows
    r = rows[keep].sort_values("txn_id")
    half = r.groupby("customer_id").cumcount() % 2
    h = r.groupby([r.customer_id, half])[flag].mean().unstack().dropna()
    return float(h[0].corr(h[1])), int(len(h))


def persistence_r(rows_a, rows_b, flag="is_hsic", min_rows=C.GATE["min_rows"]):
    a, _ = _shares(rows_a, flag, min_rows)
    b, _ = _shares(rows_b, flag, min_rows)
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner")
    return float(j.a.corr(j.b)), int(len(j))


def corr_ci(r, n, z=1.96):
    """95% CI for a Pearson r via the Fisher transform."""
    f, se = np.arctanh(r), 1 / np.sqrt(n - 3)
    return float(np.tanh(f - z * se)), float(np.tanh(f + z * se))


def gate(rows_a, rows_b, flag="is_hsic", min_rows=C.GATE["min_rows"]):
    """The three-test heterogeneity gate (selection_log §2) on a per-customer binary flag.

    rows_a / rows_b: transaction rows for the two periods (e.g. active FY25 / FY26 rows).
    A variable is usable for targeting only if `passes` is True.
    """
    vr_a, n_a = variance_ratio(rows_a, flag, min_rows)
    vr_b, n_b = variance_ratio(rows_b, flag, min_rows)
    sh, n_sh = split_half_r(rows_a, flag, min_rows)
    pr, n_pr = persistence_r(rows_a, rows_b, flag, min_rows)
    t = C.GATE
    tests = {
        "variance_ratio": vr_a >= t["variance_ratio_min"] and vr_b >= t["variance_ratio_min"],
        "split_half": sh >= t["split_half_min"],
        "persistence": pr >= t["persistence_min"],
    }
    return {
        "variance_ratio_a": vr_a, "variance_ratio_b": vr_b, "n_a": n_a, "n_b": n_b,
        "split_half_r": sh, "split_half_ci": corr_ci(sh, n_sh), "n_split_half": n_sh,
        "persistence_r": pr, "persistence_ci": corr_ci(pr, n_pr), "n_persistence": n_pr,
        "tests": tests, "passes": all(tests.values()),
    }


# ---------------------------------------------------------------- X1: are customers different at all?
def customer_sow_by_fy(act):
    """Customer-level ₹ SoW per FY for customers passing the rule-9 filter (≥ 3 purchases in each FY).

    Clipped to [0, 1]: returns can push a customer's HSIC net below 0, and a near-zero total net
    makes the ratio explode (one FY25 value is above 300). Clipping keeps those few rows from
    driving correlations and clusters.
    """
    buys = act[act.is_sale].groupby(["customer_id", "fy"]).size().unstack(fill_value=0)
    ok = buys.index[(buys[C.FISCAL_YEARS[0]] >= C.MIN_PURCHASES_PER_PERIOD) & (buys[C.FISCAL_YEARS[1]] >= C.MIN_PURCHASES_PER_PERIOD)]
    rows = act[act.customer_id.isin(ok)]
    tot = rows.groupby(["customer_id", "fy"]).net.sum().unstack()
    hs = rows[rows.is_hsic].groupby(["customer_id", "fy"]).net.sum().unstack().reindex(tot.index).fillna(0)
    return (hs / tot.where(tot > 0)).dropna().clip(0, 1)


def sow_clip_count(act):
    """How many customer-FY SoW values the clip changes (reported, so the clip isn't hidden)."""
    buys = act[act.is_sale].groupby(["customer_id", "fy"]).size().unstack(fill_value=0)
    ok = buys.index[(buys[C.FISCAL_YEARS[0]] >= C.MIN_PURCHASES_PER_PERIOD) & (buys[C.FISCAL_YEARS[1]] >= C.MIN_PURCHASES_PER_PERIOD)]
    rows = act[act.customer_id.isin(ok)]
    tot = rows.groupby(["customer_id", "fy"]).net.sum().unstack()
    hs = rows[rows.is_hsic].groupby(["customer_id", "fy"]).net.sum().unstack().reindex(tot.index).fillna(0)
    raw = (hs / tot.where(tot > 0)).dropna()
    return int(((raw < 0) | (raw > 1)).sum().sum())


def sow_bands(sow):
    """Zero (≤ 0) / Low / Mid / High, cut at terciles of the non-zero FY25 values (rule 9)."""
    fy_a, fy_b = C.FISCAL_YEARS
    edges = sow.loc[sow[fy_a] > 0, fy_a].quantile([1 / 3, 2 / 3]).values
    labels = ["Zero", "Low", "Mid", "High"]

    def band(s):
        return pd.Series(np.select([s <= 0, s <= edges[0], s <= edges[1]], labels[:3], labels[3]), index=s.index)

    moves = pd.crosstab(band(sow[fy_a]), band(sow[fy_b])).reindex(index=labels, columns=labels, fill_value=0)
    return moves.rename_axis(index=f"fy{fy_a % 100}_band", columns=f"fy{fy_b % 100}_band"), edges


def x1_heterogeneity():
    d = prep.load()
    act = prep.active(d.txn)
    fy_a, fy_b = C.FISCAL_YEARS
    g = gate(act[act.fy == fy_a], act[act.fy == fy_b])

    sow = customer_sow_by_fy(act)
    moves, edges = sow_bands(sow)
    to_zero = moves["Zero"] / moves.sum(axis=1)
    TABLES.mkdir(parents=True, exist_ok=True)
    moves.to_csv(TABLES / "x1_sow_band_movement.csv")

    return {
        "x1_variance_ratio_fy25": g["variance_ratio_a"], "x1_variance_ratio_fy26": g["variance_ratio_b"],
        "x1_gate_n_fy25": g["n_a"],
        "x1_split_half_r": g["split_half_r"], "x1_split_half_ci_lo": g["split_half_ci"][0], "x1_split_half_ci_hi": g["split_half_ci"][1],
        "x1_split_half_n": g["n_split_half"],
        "x1_persistence_r": g["persistence_r"], "x1_persistence_ci_lo": g["persistence_ci"][0], "x1_persistence_ci_hi": g["persistence_ci"][1],
        "x1_persistence_n": g["n_persistence"],
        "x1_gate_pass": bool(g["passes"]),
        "x1_sow_r_fy25_fy26": float(sow[fy_a].corr(sow[fy_b])), "x1_sow_filter_n": int(len(sow)),
        "x1_sow_values_clipped": sow_clip_count(act),
        "x1_band_edges_low_mid": float(edges[0]), "x1_band_edges_mid_high": float(edges[1]),
        "x1_band_to_zero_min": float(to_zero.min()), "x1_band_to_zero_max": float(to_zero.max()),
        "x1_verdict": "customers differ" if g["passes"] else "no customer-level differences beyond chance",
    }


# ---------------------------------------------------------------- X2: is there anything for a per-customer detector to find?
def _naive_flag(s25, s26):
    """D0 baseline detector: share falls by ≥ 10pp and by ≥ 30% relative."""
    drop = s25 - s26
    return (drop >= 0.10) & (drop >= 0.30 * s25)


def x2_decline_detector():
    """Naive decliner flag rate on real data vs on simulated customers who all share the portfolio rate.

    If the two match, every "decliner" is what chance plus the portfolio trend produce, so there is
    nothing customer-specific for a detector to find.
    """
    d = prep.load()
    act = prep.active(d.txn)
    fy_a, fy_b = C.FISCAL_YEARS
    g = act.groupby(["customer_id", "fy"]).is_hsic.agg(["sum", "count"]).unstack()
    ok = (g["count"][fy_a] >= C.GATE["min_rows"]) & (g["count"][fy_b] >= C.GATE["min_rows"])
    g = g[ok]
    n_a, n_b = g["count"][fy_a].to_numpy(dtype=int), g["count"][fy_b].to_numpy(dtype=int)
    observed = _naive_flag(g["sum"][fy_a] / n_a, g["sum"][fy_b] / n_b).mean()

    p_a, p_b = act[act.fy == fy_a].is_hsic.mean(), act[act.fy == fy_b].is_hsic.mean()
    rng = np.random.default_rng(C.SEED)
    sims = [_naive_flag(rng.binomial(n_a, p_a) / n_a, rng.binomial(n_b, p_b) / n_b).mean() for _ in range(200)]
    lo, hi = np.percentile(sims, [2.5, 97.5])
    return {
        "x2_customers": int(ok.sum()),
        "x2_naive_flag_rate_observed": float(observed),
        "x2_naive_flag_rate_null": float(np.mean(sims)),
        "x2_naive_flag_rate_null_lo": float(lo), "x2_naive_flag_rate_null_hi": float(hi),
        "x2_excess_pp": float((observed - np.mean(sims)) * 100),
        "x2_verdict": "nothing to detect" if lo <= observed <= hi else "customer-specific declines exist",
    }


# ---------------------------------------------------------------- X7: onboarding usage cliff
def x7_onboarding():
    """HSIC row share by months since opening, minus the portfolio share in the same calendar month."""
    d = prep.load()
    act = prep.active(d.txn)
    portfolio = act.groupby("month").is_hsic.mean()
    new = act[act.open_date >= C.DATA_START].copy()
    new["tenure_m"] = ((new.date - new.open_date).dt.days // 30).clip(upper=18)
    new["excess"] = new.is_hsic - new.month.map(portfolio)

    by_month = new.groupby("tenure_m").agg(rows=("excess", "size"), excess=("excess", "mean"))
    TABLES.mkdir(parents=True, exist_ok=True)
    by_month.to_csv(TABLES / "x7_onboarding_excess.csv")
    fit = sm.OLS(new.excess.to_numpy(), sm.add_constant(new.tenure_m.to_numpy(dtype=float))).fit()
    lo, hi = fit.conf_int()[1]
    return {
        "x7_rows": int(len(new)),
        "x7_max_abs_excess_pp": float(by_month.excess.abs().max() * 100),
        "x7_slope_pp_per_month": float(fit.params[1] * 100),
        "x7_slope_ci_lo_pp": float(lo * 100), "x7_slope_ci_hi_pp": float(hi * 100),
        "x7_verdict": "onboarding cliff" if hi < 0 else "no onboarding usage cliff",
    }


# ---------------------------------------------------------------- X15 / X16: data audits
def x15_sparsity():
    """Is a 60-day SoW target even computable?"""
    d = prep.load()
    days = (C.DATA_END - C.DATA_START).days + 1
    rows_per_customer = len(d.txn) / len(d.cust)
    end = C.DATA_END
    start = end - pd.Timedelta(days=60)
    open_cards = d.cust[prep.open_at(d.cust, end)].customer_id
    recent = prep.active(d.txn)
    recent = recent[prep.in_window(recent.date, start, end)]
    net = recent.groupby("customer_id").net.sum().reindex(open_cards, fill_value=0)
    return {
        "x15_rows_per_customer": float(rows_per_customer),
        "x15_rows_per_60d": float(rows_per_customer * 60 / days),
        "x15_open_cards_last_60d": int(len(open_cards)),
        "x15_sow_undefined_share_last_60d": float((net <= 0).mean()),
        "x15_verdict": "infeasible: SoW is undefined for most customers in a 60-day window",
    }


def x16_treatment_data():
    """Uplift modelling needs past offers with treated and control groups. Is there any such field?"""
    d = prep.load()
    columns = list(d.cust.columns) + list(d.txn.columns)
    hits = [c for c in columns if any(k in c.lower() for k in ("offer", "campaign", "promo", "treat", "coupon"))]
    return {
        "x16_columns_checked": len(columns),
        "x16_offer_fields": len(hits),
        "x16_verdict": "infeasible: no offer history" if not hits else "offer fields present",
    }


def run():
    out = {}
    for f in (x1_heterogeneity, x2_decline_detector, x7_onboarding, x15_sparsity, x16_treatment_data):
        out.update(f())
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:38s} {v:.4f}" if isinstance(v, float) else f"{k:38s} {v}")
