"""Findings F1-F11, F13, F14 (PROJECT_PLAN §5, HANDOFF_MAYANK §2). Owner: Mayank.

Each f* function returns a plain dict of named numbers, keys prefixed with the finding ID (INTERFACE.md).
The *_table helpers return the frames the slide 4-5 charts draw from. Only aggregates, never customer rows.
F12 and F15 are Shreyash's and live in their own section at the bottom, with no shared helpers.

    python -m analysis.experiments_f
"""
import re

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from analysis import config as C, prep

FY_A, FY_B = C.FISCAL_YEARS
HSIC, CASH, WALLET = C.PAYMENT_SHORT[C.HSIC_CODE], "Cash/UPI", "Wallet"


def slug(s):
    """Key-safe label, same rule as checks.foundation: 'Cash/UPI' -> 'cash_upi', '<6m' -> 'lt6m', '2025-01-31' -> '2025_01_31'."""
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower().replace("<", "lt").replace("+", "plus")).strip("_")


def sow_by(rows, by):
    """SoW (ratio of sums) per group. Pass active rows only."""
    g = rows.assign(h=rows.net.where(rows.is_hsic, 0.0)).groupby(by, observed=True)[["h", "net"]].sum()
    return g.h / g.net


def mix_by_fy(rows):
    """Share of net ₹ by payment method, per FY."""
    m = rows.pivot_table(index="fy", columns="payment_short", values="net", aggfunc="sum")
    return m.div(m.sum(axis=1), axis=0)


def stayers():
    """F2 Bridge universe: card open on 2024-08-01 and not closed before 2026-07-31."""
    c = prep.load().cust
    return c.customer_id[c.has_card & (c.open_date <= C.DATA_START) & (c.close_date.isna() | (c.close_date >= C.DATA_END))]


# ---------------------------------------------------------------- slide 4: the decline
def quarterly_sow_table():
    return sow_by(prep.active(prep.load().txn), "fq_label").rename("sow")


def f1_sow_trend():
    act = prep.active(prep.load().txn)
    q = quarterly_sow_table()
    out = {f"f1_sow_fy{fy % 100}": prep.sow(act[act.fy == fy]) for fy in C.FISCAL_YEARS}
    out |= {f"f1_sow_{slug(k)}": v for k, v in q.items()}
    out["f1_slope_pp_per_quarter"] = np.polyfit(np.arange(len(q)), q.to_numpy(), 1)[0] * 100
    return out


def bridge_table():
    """FY25 all -> stayers FY25 -> stayers FY26 -> FY26 all, as SoW levels and steps (shares)."""
    act = prep.active(prep.load().txn)
    st = act[act.customer_id.isin(stayers())]
    s_a, s_b = prep.sow(act[act.fy == FY_A]), prep.sow(act[act.fy == FY_B])
    st_a, st_b = prep.sow(st[st.fy == FY_A]), prep.sow(st[st.fy == FY_B])
    b = pd.Series({"FY25 SoW": s_a, "Leavers": st_a - s_a, "Stayers": st_b - st_a, "Joiners": s_b - st_b, "FY26 SoW": s_b})
    assert np.isclose(b.iloc[0] + b.iloc[1:4].sum(), b.iloc[4]), "Bridge does not reconcile"
    b.attrs |= {"stayer_sow_fy25": st_a, "stayer_sow_fy26": st_b}
    return b


def f2_bridge():
    b = bridge_table()
    return {"f2_stayers_n": len(stayers()),
            "f2_stayer_sow_fy25": b.attrs["stayer_sow_fy25"], "f2_stayer_sow_fy26": b.attrs["stayer_sow_fy26"],
            "f2_leaver_pp": b["Leavers"] * 100, "f2_stayer_pp": b["Stayers"] * 100, "f2_joiner_pp": b["Joiners"] * 100,
            "f2_total_pp": (b["FY26 SoW"] - b["FY25 SoW"]) * 100}


def per_card_monthly_table():
    """F14: per month, cards whose active window covers any day of it; active net and HSIC ₹ per such card."""
    d = prep.load()
    c = d.cust[d.cust.has_card]
    act = prep.active(d.txn)
    g = act.assign(h=act.net.where(act.is_hsic, 0.0)).groupby("month")[["net", "h"]].sum()
    g["cards"] = [int(((c.open_date <= p.end_time.normalize()) & (c.close_date.isna() | (c.close_date >= p.start_time))).sum())
                  for p in g.index]
    g["net_per_card"], g["hsic_per_card"], g["sow"] = g.net / g.cards, g.h / g.cards, g.h / g.net
    return g


def f14_per_card():
    g = per_card_monthly_table()
    out = {}
    for lab, month in [("aug24", "2024-08"), ("may26", "2026-05")]:
        r = g.loc[pd.Period(month, "M")]
        out |= {f"f14_{lab}_cards": int(r.cards), f"f14_{lab}_net_per_card": r.net_per_card,
                f"f14_{lab}_hsic_per_card": r.hsic_per_card, f"f14_{lab}_sow": r.sow}
    return out


# ---------------------------------------------------------------- slide 5: where it went
def f3_mix_shift():
    """Stayers' payment-mix shift FY25 -> FY26, and each method's share of HSIC's lost share."""
    act = prep.active(prep.load().txn)
    m = mix_by_fy(act[act.customer_id.isin(stayers())])
    change = m.loc[FY_B] - m.loc[FY_A]
    loss = -change[HSIC]
    assert np.isclose(change.drop(HSIC).sum(), loss), "mix shifts don't add up to HSIC's loss"
    out = {"f3_hsic_change_pp": change[HSIC] * 100}
    for k, v in change.drop(HSIC).items():
        out[f"f3_{slug(k)}_change_pp"] = v * 100
        out[f"f3_{slug(k)}_share_of_loss"] = v / loss
    return out


def f4_did():
    """Cash/UPI share gain: stayers (active rows) vs non-cardholders (the market benchmark)."""
    d = prep.load()
    act = prep.active(d.txn)
    st, nc = mix_by_fy(act[act.customer_id.isin(stayers())]), mix_by_fy(d.txn[~d.txn.has_card])
    ds, dn = (st.loc[FY_B, CASH] - st.loc[FY_A, CASH]) * 100, (nc.loc[FY_B, CASH] - nc.loc[FY_A, CASH]) * 100
    return {"f4_cash_upi_change_pp_stayers": ds, "f4_cash_upi_change_pp_noncardholders": dn, "f4_did_pp": ds - dn}


def ticket_band_table():
    """Share of purchases (active-window Sale rows) by method within ticket band, per FY."""
    p = prep.purchases(prep.load().txn)
    return p.groupby(["ticket_band", "fy"], observed=True).payment_short.value_counts(normalize=True).unstack()


def f5_ticket_bands():
    g = ticket_band_table()
    p = prep.purchases(prep.load().txn)
    p = p[p.fy == FY_B]
    sales = p.groupby("ticket_band", observed=True).net.sum()
    hsic_sales = p[p.is_hsic].groupby("ticket_band", observed=True).net.sum()
    out = {}
    for b in C.TICKET_LABELS:
        a, z = g.loc[(b, FY_A), HSIC], g.loc[(b, FY_B), HSIC]
        out |= {f"f5_hsic_share_fy25_{slug(b)}": a, f"f5_hsic_share_fy26_{slug(b)}": z,
                f"f5_cash_upi_gain_pp_{slug(b)}": (g.loc[(b, FY_B), CASH] - g.loc[(b, FY_A), CASH]) * 100,
                f"f5_sales_fy26_{slug(b)}": sales[b], f"f5_hsic_sales_fy26_{slug(b)}": hsic_sales[b]}
    rel = [1 - out[f"f5_hsic_share_fy26_{slug(b)}"] / out[f"f5_hsic_share_fy25_{slug(b)}"] for b in C.TICKET_LABELS]
    out["f5_hsic_rel_loss_min"], out["f5_hsic_rel_loss_max"] = min(rel), max(rel)
    return out


def f6_ticket_signal():
    """HSIC row share by ticket tercile within category × quarter; AUC of HSIC-use models by feature group."""
    d = prep.load()
    s = prep.purchases(d.txn).merge(d.cust[["customer_id", "age", "credit_limit", "apr"]], on="customer_id")
    # ties at an edge go up, so equal tickets share a tercile and every capped ₹9,999.99 row counts as high
    # (in 8 of 80 groups over a third of rows are capped; a plain qcut would drop the top bin there)
    g = s.groupby(["category_code", "fq_label"]).amount
    s["tercile"] = (s.amount >= g.transform(lambda x: x.quantile(1 / 3))).astype(int) + (
        s.amount >= g.transform(lambda x: x.quantile(2 / 3)))
    share = s.groupby("tercile").is_hsic.mean()
    month = pd.get_dummies(s.month.astype(str), prefix="m")
    ticket = pd.DataFrame({"log_amt": np.log(s.amount), "capped": s.is_capped})
    cat = pd.get_dummies(s.category_code, prefix="c")
    profile = pd.DataFrame({"age": s.age, "limit": s.credit_limit / 1e5, "apr": s.apr, "prime": s.is_prime,
                            "tenure_y": (s.date - s.open_date).dt.days / C.DAYS_PER_YEAR})
    sets = {"month": [month], "month_ticket": [month, ticket], "month_ticket_category": [month, ticket, cat],
            "everything": [month, ticket, cat, profile]}
    tr, te = train_test_split(np.arange(len(s)), test_size=0.3, random_state=C.SEED)
    y = s.is_hsic.to_numpy()
    out = {f"f6_hsic_row_share_t{i + 1}": share[i] for i in range(3)}
    for name, parts in sets.items():
        X = pd.concat(parts, axis=1).astype(float).to_numpy()
        X = (X - X[tr].mean(0)) / (X[tr].std(0) + 1e-9)
        p = LogisticRegression(max_iter=500).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
        out[f"f6_auc_{name}"] = roc_auc_score(y[te], p)
    return out


def capped_mix_table():
    """Share of capped (₹9,999.99) purchases by method, per FY."""
    p = prep.purchases(prep.load().txn)
    return p[p.is_capped].groupby("fy").payment_short.value_counts(normalize=True).unstack()


def f7_wallet_capped():
    m = capped_mix_table()
    return {"f7_wallet_share_capped_fy25": m.loc[FY_A, WALLET], "f7_wallet_share_capped_fy26": m.loc[FY_B, WALLET],
            "f7_hsic_share_capped_fy25": m.loc[FY_A, HSIC], "f7_hsic_share_capped_fy26": m.loc[FY_B, HSIC]}


def f8_reward_paradox():
    """Cashback a cardholder would have earned had their FY26 active non-HSIC spend gone on HSIC."""
    act = prep.active(prep.load().txn)
    a = act[act.fy == FY_B]
    off = a[~a.is_hsic]
    ge = off[off.is_prime & off.category_code.isin([C.GROCERY, C.ELECTRONICS])]
    return {"f8_prime_ge_other_net": ge.net.sum(), "f8_prime_ge_left_on_table": (ge.net * ge.reward_rate).sum(),
            "f8_all_left_on_table": (off.net * off.reward_rate).sum(), "f8_rewards_earned_fy26": a.reward.sum()}


# ---------------------------------------------------------------- closures (F9-F11, slide 8)
def closure_quarter_table():
    """Calendar quarters: closures in the quarter ÷ cards open at its start."""
    c = prep.load().cust
    c = c[c.has_card]
    rows = []
    for q in pd.period_range("2024Q3", "2026Q2", freq="Q"):
        start, end = q.start_time, q.end_time.normalize()
        rows.append({"quarter": str(q), "closed": int(c.close_date.between(start, end).sum()),
                     "open_at_start": int(((c.open_date < start) & (c.close_date.isna() | (c.close_date >= start))).sum())})
    return pd.DataFrame(rows).assign(rate=lambda t: t.closed / t.open_at_start)


def f9_closure_trend():
    q = closure_quarter_table()
    out = {f"f9_rate_{slug(r.quarter)}": r.rate for r in q.itertuples()}
    out |= {"f9_rate_first": q.rate.iloc[0], "f9_rate_last": q.rate.iloc[-1], "f9_ratio": q.rate.iloc[-1] / q.rate.iloc[0]}
    return out


def f10_closure_by_age():
    """6-month closure rate by card-age bin on the rule-9 universe, at the train and test cutoffs."""
    out = {}
    for cut in (C.CUTOFF_TRAIN, C.CUTOFF_TEST):
        u, k = prep.snapshot_universe(cut), slug(cut.date())
        rate = u.groupby("card_age_bin", observed=True).closed_6m.mean()
        out |= {f"f10_{k}_cards": len(u), f"f10_{k}_closers": int(u.closed_6m.sum())}
        out |= {f"f10_{k}_closure_{slug(b)}": r for b, r in rate.items()}
        out[f"f10_{k}_young_over_old"] = rate[C.CARD_AGE_LABELS[0]] / rate[C.CARD_AGE_LABELS[-1]]
    return out


def f11_post_closure():
    """Closers who kept shopping at MetroMart after their close date: how many, how much, and how they pay."""
    d = prep.load()
    post = d.txn[d.txn.close_date.notna() & (d.txn.date > d.txn.close_date)]
    mix = post.groupby("payment_short").net.sum() / post.net.sum()
    assert HSIC not in mix.index, "HSIC row after its card closed"
    return {"f11_closed_cards": int(d.cust.is_closed.sum()), "f11_still_shopping": post.customer_id.nunique(),
            "f11_post_close_net": post.net.sum()} | {f"f11_mix_{slug(k)}": v for k, v in mix.items()}


# ---------------------------------------------------------------- persistence (F13, slide 9 footnote)
def f13_persistence():
    """FY25 -> FY26 correlation of purchase count and net spend per customer, on the stayers."""
    t = prep.load().txn
    s = t[t.customer_id.isin(stayers())]
    g = s.groupby(["customer_id", "fy"]).agg(purchases=("is_sale", "sum"), net=("net", "sum")).unstack(fill_value=0)
    r = {k: np.corrcoef(g[(k, FY_A)], g[(k, FY_B)])[0, 1] for k in ("purchases", "net")}
    return {"f13_r_purchases": r["purchases"], "f13_r_net": r["net"], "f13_n": len(g)}


F_FUNCS = [f1_sow_trend, f2_bridge, f3_mix_shift, f4_did, f5_ticket_bands, f6_ticket_signal, f7_wallet_capped,
           f8_reward_paradox, f9_closure_trend, f10_closure_by_age, f11_post_closure, f13_persistence, f14_per_card]


def plain(v):
    """numpy scalars -> Python types (numbers contract)."""
    return v.item() if isinstance(v, np.generic) else v


def run():
    out = {}
    for f in F_FUNCS + SHREYASH_FUNCS:
        out |= {k: plain(v) for k, v in f().items()}
    return out


# ---------------------------------------------------------------- F12, F15 (Shreyash)
SHREYASH_FUNCS = []      # list f12_* / f15_* functions here; run() picks them up


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:42s} {v:.4f}" if isinstance(v, float) else f"{k:42s} {v}")
