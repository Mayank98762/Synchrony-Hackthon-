"""Offer economics and pilot design (PROJECT_PLAN §8, selection_log §8-§9, HANDOFF_SHREYASH §2). Owner: Shreyash.

All flows are per year, on FY26 active spend, net of the rewards HSIC funds:

    net margin per ₹ moved to HSIC    m = interchange + revolve income − reward rate × (1 − MetroMart co-funding)
    value per incremental ₹           u = m − extra incentive × (1 − co-funding)
    break-even shift                  s* = incentive paid on spend that would have happened anyway ÷ (eligible ₹ × u)

s* is the share of an offer's eligible non-HSIC spend that must move to HSIC for it to pay back. It is "never" when
u ≤ 0 or s* > 100%, and 0 when the offer costs nothing unless spend moves. Operating and fixed costs (POS changes,
messaging, a UPI partnership) aren't in the data and are left out, so every s* is a floor. Scenario inputs come from
config.SCENARIOS (Assumed); results are Simulated (prefixes o<N>_, econ_, mde_); measured inputs are `econin_*`.

    python -m analysis.economics
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from analysis import config as C, prep, segments

FY = C.FISCAL_YEARS[1]                                   # FY26
FY_START = pd.Timestamp("2025-08-01")
TABLES = C.OUTPUTS / "tables"
GRID = ["B", "C", "D", "E"]

# Offer design (plan §8) and the two inputs the plan leaves open, both Assumed and reported as assumed_* keys.
COST_OF_FUNDS = 0.08                 # O1: crediting the reward a month early costs a month of funding
EMI_SUBVENTION = 0.03                # O4: interest cost of a no-cost EMI as a share of the basket, before co-funding
O5_BONUS, O5_COUNT, O5_TICKET = 50, 5, 1000
O6_BOOST, O6_MONTHS = 0.03, 3
O7_MILESTONE, O7_DAYS, O7_TRIAL_MONTHS = 3, 60, 3
O8_BONUS = 0.01


def margin(s, reward_rate):
    """Net margin per ₹ of HSIC spend, after the share of rewards HSIC funds."""
    return s["interchange"] + s["revolve_income"] - reward_rate * (1 - s["cofunding"])


def breakeven(eligible, unit, cannibal):
    """Share of eligible spend that must move for net value ≥ 0, or "never" (selection_log §8)."""
    if unit <= 0:
        return "never"
    s = cannibal / (eligible * unit)
    return "never" if s > 1 else s


def value_at(shift, eligible, unit, cannibal):
    """Net value per year if `shift` of the eligible spend moves to HSIC."""
    return shift * eligible * unit - cannibal


def card_years(cust):
    """Years each card was open inside FY26: the exposure for per-card rates."""
    lo = cust.open_date.clip(lower=FY_START)
    hi = cust.close_date.fillna(C.DATA_END).clip(upper=C.DATA_END)
    return ((hi - lo).dt.days + 1).clip(lower=0) / C.DAYS_PER_YEAR


def pools():
    """FY26 spend pools on active rows (cards open), all measured."""
    d = prep.load()
    a = prep.active(d.txn)
    a = a[a.fy == FY]
    non, hs = a[~a.is_hsic], a[a.is_hsic]
    big = ["3k-10k", "capped"]
    cards = d.cust[d.cust.has_card]
    years = card_years(cards)
    nonprime_years = years[~cards.is_prime].sum()
    nph = hs[~hs.is_prime]
    p = {
        "reward_rate": hs.reward.sum() / hs.net.sum(),
        "hsic": hs.net.sum(), "nonhsic": non.net.sum(),
        "cash_upi": non.loc[non.payment_short == "Cash/UPI", "net"].sum(),
        "prime_grocery": non.loc[non.is_prime & non.category_code.eq(C.GROCERY), "net"].sum(),
        "prime_electronics": non.loc[non.is_prime & non.category_code.eq(C.ELECTRONICS), "net"].sum(),
        "big_nonhsic": non.loc[non.ticket_band.isin(big), "net"].sum(),
        "big_hsic": hs.loc[hs.ticket_band.isin(big), "net"].sum(),
        "small_nonhsic": non.loc[non.ticket_band.eq("<1k"), "net"].sum(),
        "card_years": years.sum(),
        "np_grocery_per_card_year": nph.loc[nph.category_code.eq(C.GROCERY), "net"].sum() / nonprime_years,
        "np_electronics_per_card_year": nph.loc[nph.category_code.eq(C.ELECTRONICS), "net"].sum() / nonprime_years,
    }
    p["other_1pct"] = p["nonhsic"] - p["prime_grocery"] - p["prime_electronics"]
    p["hsic_per_card_year"] = p["hsic"] / p["card_years"]
    return p


def segment_a(score):
    """Segment A at the score cutoff: count, and MetroMart net spend after closure over FY26 (all methods)."""
    ids = score.loc[score.segment == "A", "customer_id"]
    t = prep.load().txn
    start, end = prep.lookback(C.CUTOFF_SCORE)
    post = t[t.customer_id.isin(ids) & (t.date > t.close_date) & prep.in_window(t.date, start, end)]
    return len(ids), post.net.sum()


def young_cards(score):
    """Cards under 1 year at the score cutoff (B + C), their Non-Prime share, and their 12-month closure rate."""
    y = score[score.segment.isin(["B", "C"])]
    box = pd.read_csv(TABLES / "segments_box_table.csv", index_col="segment")
    n = box.customers[["B", "C"]]
    c6 = (box.closure_6m[["B", "C"]] * n).sum() / n.sum()
    return len(y), float((~y.is_prime).mean()), 1 - (1 - c6) ** 2


def o5_reach():
    """FY26 customer-months that would earn the streak bonus with no change in behaviour (point 3 of the review)."""
    p = prep.purchases(prep.load().txn)
    s = p[(p.fy == FY) & p.is_hsic & (p.amount < O5_TICKET)]
    per_month = s.groupby(["customer_id", "month"]).size()
    return int((per_month >= O5_COUNT).sum()), int(per_month.max())


def o7_milestone():
    """Cards opened in the data window (with 60 days observable): share reaching 3, and 1, HSIC purchases in 60 days."""
    d = prep.load()
    c = d.cust[d.cust.has_card & d.cust.open_date.between(C.DATA_START, C.DATA_END - pd.Timedelta(days=O7_DAYS))]
    p = prep.purchases(d.txn)
    p = p[p.is_hsic & p.customer_id.isin(c.customer_id)]
    n = p[(p.date - p.open_date).dt.days < O7_DAYS].groupby("customer_id").size().reindex(c.customer_id, fill_value=0)
    return len(c), float((n >= O7_MILESTONE).mean()), float((n >= 1).mean())


def o8_noise(build):
    """Segment D (built at the test cutoff): FY26 HSIC spend, non-HSIC spend, and the HSIC spend above each customer's
    own trailing 3-month average with no change in behaviour, which the threshold bonus would pay on anyway."""
    ids = build.loc[build.segment == "D", "customer_id"].to_numpy()
    a = prep.active(prep.load().txn)
    a = a[a.customer_id.isin(ids)]
    months = pd.period_range(C.DATA_START, C.DATA_END, freq="M")
    h = a[a.is_hsic].groupby(["customer_id", "month"]).net.sum().unstack(fill_value=0.0)
    h = h.reindex(index=ids, columns=months, fill_value=0.0)
    trailing = h.T.shift(1).rolling(3).mean().T
    fy26 = [m for m in months if m >= pd.Period(FY_START, "M")]
    # The bonus pays on purchases, not returns, above a baseline that can't go below zero.
    above = (h[fy26].clip(lower=0) - trailing[fy26].clip(lower=0)).clip(lower=0)
    return {"customers": len(ids), "hsic": float(h[fy26].clip(lower=0).to_numpy().sum()),
            "nonhsic": float(a[(a.fy == FY) & ~a.is_hsic].net.sum()), "noise": float(above.to_numpy().sum())}


def mde():
    """Minimum detectable change in HSIC row share per box: 10% holdout, α = 0.05, power 0.8, 3 months of purchases.
    Each purchase is close to an independent coin flip (X1), so the binomial closed form applies."""
    box = pd.read_csv(TABLES / "segments_box_table.csv", index_col="segment")
    sizes = pd.read_csv(TABLES / "segments_sizes.csv", index_col="segment")
    z = norm.ppf(1 - C.ALPHA / 2) + norm.ppf(C.POWER)
    h = C.HOLDOUT_SHARE

    def one(p, n):
        return z * np.sqrt(p * (1 - p) * (1 / (n * (1 - h)) + 1 / (n * h)))

    out, rows, hits = {}, 0.0, 0.0
    for s in GRID:
        n, p = sizes.customers_at_score[s] * box.rows_3m[s], box.p_hsic[s]
        out |= {f"mde_{s}": one(p, n), f"mde_{s}_rel": one(p, n) / p, f"mde_{s}_purchases_3m": n, f"mde_{s}_p": p}
        rows, hits = rows + n, hits + n * p
    out |= {"mde_grid": one(hits / rows, rows), "mde_grid_purchases_3m": rows, "mde_z": z}
    return out


def offers(p, a_spend, d):
    """Break-even shift, value per incremental ₹ and value per 1% of eligible spend moved, by offer and scenario."""
    r = p["reward_rate"]
    g, e = p["prime_grocery"], p["prime_electronics"]
    r_ge = (C.PRIME_RATES[C.GROCERY] * g + C.PRIME_RATES[C.ELECTRONICS] * e) / (g + e)
    # id: (eligible ₹, reward rate on the moved spend, extra incentive per ₹ moved, existing HSIC ₹ that also gets it)
    rows = {
        "o3": (g + e, r_ge, 0.0, 0.0),                          # reward visibility, Prime Grocery + Electronics first
        "o3_other": (p["other_1pct"], C.NON_PRIME_RATE, 0.0, 0.0),  # reward visibility on 1% baskets
        "o1": (p["nonhsic"], r, r * COST_OF_FUNDS / 12, p["hsic"]),
        "o2": (p["cash_upi"], r, 0.0, 0.0),
        "o4": (p["big_nonhsic"], r, EMI_SUBVENTION, p["big_hsic"]),  # upper bound: every ₹3k+ HSIC basket takes the EMI
        "o6": (a_spend, r, O6_MONTHS / 12 * (O6_BOOST - r), 0.0),  # boost over the normal rate, first 3 of 12 months
        "o8": (d["nonhsic"], r, O8_BONUS, d["noise"]),
    }
    out = {}
    base = C.SCENARIOS["base"]
    for oid, (elig, rate, inc, existing) in rows.items():
        for name, s in C.SCENARIOS.items():
            inc_net = inc * (1 - s["cofunding"])
            unit, cannibal = margin(s, rate) - inc_net, existing * inc_net
            out[f"{oid}_unit_{name}"] = unit
            out[f"{oid}_breakeven_{name}"] = breakeven(elig, unit, cannibal)
            out[f"{oid}_value_per_1pct_{name}"] = value_at(0.01, elig, unit, cannibal)
        # Revolve income at which each moved ₹ breaks even, other inputs at base (assumption-free on revolve);
        # also with no MetroMart co-funding, since 50% is the most generous input.
        out[f"{oid}_breakeven_revolve"] = max(0.0, (rate + inc) * (1 - base["cofunding"]) - base["interchange"])
        out[f"{oid}_breakeven_revolve_nocofund"] = max(0.0, rate + inc - base["interchange"])
        out[f"econin_{oid}_eligible"] = elig
    return out


def young_offer(p, young):
    """O7 Prime trial for Non-Prime young cards: cost per card vs the margin of a card kept open for 12 months.
    Break-even = share of trial cards whose closure it must prevent; "never" if above their 12-month closure rate."""
    n_young, nonprime_share, closure_12m = young
    extra = ((C.PRIME_RATES[C.GROCERY] - C.NON_PRIME_RATE) * p["np_grocery_per_card_year"]
             + (C.PRIME_RATES[C.ELECTRONICS] - C.NON_PRIME_RATE) * p["np_electronics_per_card_year"]) * O7_TRIAL_MONTHS / 12
    out = {"econin_o7_young_cards": n_young, "econin_o7_nonprime_share": nonprime_share,
           "econin_o7_closure_12m": closure_12m}
    for name, s in C.SCENARIOS.items():
        cost = extra * (1 - s["cofunding"])
        value = p["hsic_per_card_year"] * margin(s, p["reward_rate"])
        need = cost / value if value > 0 else np.inf
        # Not a spend shift, so not named o7_breakeven_<scenario> (the dashboard's break-even-shift column reads those).
        out |= {f"o7_trial_cost_per_card_{name}": cost, f"o7_value_per_saved_card_{name}": value,
                f"o7_breakeven_saved_{name}": "never" if need > closure_12m else need}
    return out


def self_check(p):
    """Sanity checks from PROJECT_PLAN §14: a loss-making offer returns "never", 0% shift is the baseline, and the
    handoff's hand-worked margins reproduce."""
    assert breakeven(1.0, -0.01, 0.0) == "never" and breakeven(1.0, 0.01, 0.02) == "never", "loss must return never"
    assert np.isclose(breakeven(100.0, 0.01, 0.5), 0.5)
    assert np.isclose(value_at(0.0, 1e6, 0.02, 123.0), -123.0), "0% shift must leave only the incentive on existing spend"
    for name, rate, want in [("conservative", 0.05, -0.035), ("base", 0.05, 0.0025), ("optimistic", 0.05, 0.015),
                             ("conservative", 0.03, -0.015), ("base", 0.03, 0.0125), ("optimistic", 0.03, 0.025)]:
        assert np.isclose(margin(C.SCENARIOS[name], rate), want), f"margin {name} @ {rate} != handoff table"
    assert 0.0139 < p["reward_rate"] < 0.0141, "FY26 effective reward rate moved: check prep.reward"


def charts(p, out):
    import matplotlib.pyplot as plt
    try:
        from analysis import style
    except ImportError:
        from analysis import _style_fallback as style
    style.apply()
    paths = []

    # 11_net_margin_waterfall: what HSIC keeps per ₹100 moved, base case, general spend vs Prime grocery.
    s, cons = C.SCENARIOS["base"], C.SCENARIOS["conservative"]
    fig, axes = plt.subplots(1, 2, sharey=True)
    cases = [(f"General spend (average reward {p['reward_rate']:.2%})", p["reward_rate"]),
             ("Prime grocery (5% reward)", C.PRIME_RATES[C.GROCERY])]
    levels = [0.0]
    for ax, (title, rate) in zip(axes, cases):
        steps = [("Interchange", s["interchange"]), ("Revolve\nincome", s["revolve_income"]), ("Rewards", -rate),
                 ("MetroMart\nco-funds", rate * s["cofunding"])]
        level = 0.0
        for i, (_, v) in enumerate(steps):
            end = level + v
            ax.bar(i, v * 100, bottom=level * 100, width=0.55,
                   color=style.COLORS["hsic"] if v >= 0 else style.COLORS["negative"])
            # value label outside the bar end: above a rise, below a fall
            y, va = (end * 100 + 0.12, "bottom") if v >= 0 else (end * 100 - 0.12, "top")
            ax.text(i, y, f"{v * 100:+.2f}", ha="center", va=va, fontsize=10, color=style.COLORS["ink"])
            levels.append(end)
            level = end
        ax.bar(len(steps), level * 100, width=0.55, color=style.COLORS["secondary"])
        ax.text(len(steps), max(level, 0) * 100 + 0.12, f"{level * 100:.2f}", ha="center", va="bottom", fontsize=11,
                fontweight="bold", color=style.COLORS["ink"])
        ax.axhline(0, color=style.COLORS["axis"], lw=0.8)
        ax.set_xticks(range(len(steps) + 1), [lab for lab, _ in steps] + ["Net\nmargin"], fontsize=9)
        ax.set_title(title, fontsize=11, pad=10)
    axes[0].set_ylim(min(levels) * 100 - 0.8, max(levels) * 100 + 0.8)
    axes[0].set_ylabel("₹ kept per ₹100 moved to HSIC")
    fig.suptitle("What HSIC keeps on each ₹100 moved to the card (base case)", x=0.06, ha="left", fontsize=14,
                 fontweight="bold")
    fig.text(0.06, 0.02, f"Assumed, base case: interchange {s['interchange']:.2%}, revolve income {s['revolve_income']:.0%} "
             f"of spend, MetroMart co-funds {s['cofunding']:.0%} of rewards. Reward rate measured on FY26 HSIC spend. "
             f"Conservative case: general {margin(cons, p['reward_rate']) * 100:+.2f}, "
             f"Prime grocery {margin(cons, C.PRIME_RATES[C.GROCERY]) * 100:+.2f}.",
             fontsize=8, color=style.COLORS["secondary"], wrap=True)
    fig.subplots_adjust(top=0.82, bottom=0.2, wspace=0.08)
    paths.append(style.save(fig, 11, "net_margin_waterfall"))
    plt.close(fig)

    # 11_breakeven: share of eligible spend that must move for each offer to pay back, by scenario; "never" as a marker.
    labels = [("o3", "O3 Reward visibility: Prime Grocery + Electronics"), ("o3_other", "O3 Reward visibility: 1% baskets"),
              ("o1", "O1 Instant cashback at the till"), ("o2", "O2 HSIC card on UPI"),
              ("o4", "O4 No-cost EMI on ₹3,000+ baskets"), ("o6", "O6 Win-back for closed cards"),
              ("o8", "O8 Threshold bonus (segment D)")]
    fig, ax = plt.subplots()
    names = list(C.SCENARIOS)
    for i, (oid, _) in enumerate(labels):
        for j, name in enumerate(names):
            v, y = out[f"{oid}_breakeven_{name}"], i + (j - 1) * 0.22
            if v == "never":
                ax.plot(104, y, marker="x", color=style.COLORS["critical"], ms=7, mew=2)
                ax.text(106, y, "never", va="center", fontsize=8, color=style.COLORS["secondary"])
            else:
                ax.plot(v * 100, y, "o", color=style.SCENARIO_COLORS[name], ms=8, mec=style.COLORS["bg"], mew=2)
    ax.set_yticks(range(len(labels)), [lab for _, lab in labels], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-3, 115)
    ax.set_xticks(range(0, 101, 20), [f"{x}%" for x in range(0, 101, 20)])
    ax.grid(axis="x", visible=True)
    ax.grid(axis="y", visible=False)
    for name in names:
        ax.plot([], [], "o", color=style.SCENARIO_COLORS[name], ms=8, label=name.capitalize())
    ax.plot([], [], "x", color=style.COLORS["critical"], mew=2, label="Never breaks even")
    ax.legend(loc="lower right", fontsize=9, ncol=4, bbox_to_anchor=(1, 1.0))
    ax.set_xlabel("Share of the offer's eligible non-HSIC spend that must move to HSIC to pay back\n"
                  "(0% = pays back from the first rupee moved)")
    ax.set_title("Break-even shift by offer and scenario", pad=28)
    fig.text(0.02, 0.02, "Simulated. Scenario inputs are Assumed (interchange, revolve income, MetroMart co-funding); "
             "operating costs are not included, so each point is a floor.", fontsize=8, color=style.COLORS["secondary"])
    fig.subplots_adjust(left=0.33, right=0.97, top=0.82, bottom=0.17)
    paths.append(style.save(fig, 11, "breakeven"))
    plt.close(fig)
    return paths


def run():
    p = pools()
    self_check(p)
    score, _ = segments.assign(C.CUTOFF_SCORE)
    build, _ = segments.assign(C.CUTOFF_TEST)
    a_n, a_spend = segment_a(score)
    d = o8_noise(build)
    o5_hits, o5_max = o5_reach()
    o7_cards, o7_reach3, o7_reach1 = o7_milestone()

    out = {f"econin_{k}": v for k, v in p.items()}
    out |= {"econin_o6_customers": a_n, "econin_o8_customers": d["customers"], "econin_o8_hsic": d["hsic"],
            "econin_o8_noise": d["noise"], "econin_o8_noise_share": d["noise"] / d["hsic"],
            "assumed_cost_of_funds": COST_OF_FUNDS, "assumed_emi_subvention": EMI_SUBVENTION}
    for name, s in C.SCENARIOS.items():
        for tag, rate in [("general", p["reward_rate"]), ("one_pct", C.NON_PRIME_RATE),
                          ("prime_grocery", C.PRIME_RATES[C.GROCERY]), ("prime_electronics", C.PRIME_RATES[C.ELECTRONICS])]:
            out[f"econ_margin_{tag}_{name}"] = margin(s, rate)
    out |= offers(p, a_spend, d)
    out |= young_offer(p, young_cards(score))
    # O5 (streak) and O7's milestone: reach under rule 9 (one row = one purchase). Recorded, not priced, until point 3
    # of the review settles how a "purchase" is counted.
    out |= {"o5_reach_customer_months": o5_hits, "o5_max_small_hsic_purchases_in_a_month": o5_max,
            "o7_new_cards_observed": o7_cards, "o7_milestone_reach": o7_reach3, "o7_first_use_60d_share": o7_reach1}
    out |= {f"o5_breakeven_{name}": "no one qualifies" for name in C.SCENARIOS} if o5_hits == 0 else {}
    out |= mde()
    charts(p, out)
    return {k: (v.item() if isinstance(v, np.generic) else v) for k, v in out.items()}


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:44s} {v:.6g}" if isinstance(v, float) else f"{k:44s} {v}")
