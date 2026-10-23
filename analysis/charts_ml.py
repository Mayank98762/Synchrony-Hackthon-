"""Charts for slides 8 (closures) and 9 (who to prioritise).

Reads the aggregate tables and key_numbers.json written by run_all, plus two small aggregates
from prep (closure rate by card age, closures per open card by quarter). Writes PNGs to
outputs/charts/. Uses Shreyash's analysis/style.py when it exists, else the fallback.

    python -m analysis.charts_ml        (after run_all)
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from analysis import config as C, prep

try:
    from analysis import style
except ImportError:
    from analysis import _style_fallback as style

TABLES = C.OUTPUTS / "tables"
SOURCE = "Source: HSIC × MetroMart case data."
AGE_NAMES = {"<6m": "Under 6 months", "6-12m": "6–12 months", "1-2y": "1–2 years", "2-3y": "2–3 years", "3y+": "3+ years"}
MODEL_NAMES = {"B0 random": "Random guess", "B1 recency": "Months since last HSIC use", "B2 card age": "Card age alone",
               "LR-profile": "Logistic regression: profile", "LR-usage": "Logistic regression: usage only",
               "LR-all": "Logistic regression: all features", "HGB": "Gradient boosting: all features"}
BOXES = {"B": ("Protect first", "young · high frequency"), "C": ("Activate", "young · low/mid frequency"),
         "D": ("Grow", "mature · high frequency"), "E": ("Nudge", "mature · low/mid frequency")}


def _c(key):
    return style.COLORS[key]


def _figure(title, subtitle, source, top=0.86, **kw):
    """Title, subtitle and source line sit outside the plot area, which constrained layout keeps inside `rect`."""
    fig, ax = plt.subplots(layout="constrained", **kw)
    fig.get_layout_engine().set(rect=(0, 0.05, 1, top - 0.05))
    fig.text(0.01, 0.975, title, va="top", fontsize=16, fontweight="bold", color=_c("ink"))
    fig.text(0.01, 0.915, subtitle, va="top", fontsize=11, color=_c("muted"))
    fig.text(0.01, 0.012, f"{source} {SOURCE}", fontsize=8.5, color=_c("muted"))
    return fig, ax


def _pct(x, digits=1):
    return f"{x * 100:.{digits}f}%"


def _key_numbers():
    raw = json.loads((C.OUTPUTS / "key_numbers.json").read_text(encoding="utf-8"))
    return {k: v["value"] for k, v in raw.items()}


# ---------------------------------------------------------------- slide 8: closures
def closure_by_card_age():
    u = prep.snapshot_universe(C.CUTOFF_TEST)
    g = u.groupby("card_age_bin", observed=True).closed_6m.agg(["mean", "size"]).reindex(C.CARD_AGE_LABELS)
    fig, ax = _figure("Young cards close far more often",
                      "Share of cards open on 31 Jan 2026 that closed by 31 Jul 2026, by card age",
                      f"All {len(u):,} open cards. Measured.")
    x = np.arange(len(g))
    colors = [_c("hsic")] + [_c("muted")] * (len(g) - 1)
    ax.bar(x, g["mean"], width=0.62, color=colors)
    for i, (rate, n) in enumerate(zip(g["mean"], g["size"])):
        ax.text(i, rate + 0.003, _pct(rate), ha="center", va="bottom", fontsize=13, fontweight="bold", color=_c("ink"))
    ax.set_xticks(x, [f"{AGE_NAMES[b]}\n{n:,} cards" for b, n in zip(g.index, g["size"])])
    ratio = g["mean"].iloc[0] / g["mean"].iloc[-1]
    top = g["mean"].iloc[0]
    ax.text(len(g) - 1.4, top * 0.95, f"Cards under 6 months close at\n{ratio:.1f}× the rate of cards over 3 years",
            ha="center", va="top", fontsize=13, color=_c("secondary"), linespacing=1.4)
    ax.set_ylim(0, top * 1.18)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.tick_params(axis="x", length=0)
    return style.save(fig, 8, "closure_by_card_age"), {"ratio": ratio, "rates": g["mean"].round(4).to_dict()}


def closures_per_quarter():
    """F9 definition: cards closed in the calendar quarter ÷ cards open at its start."""
    cust = prep.load().cust
    cust = cust[cust.has_card]
    rows = []
    for q in pd.period_range("2024Q3", "2026Q2", freq="Q"):
        start, end = q.start_time, q.end_time.normalize()
        open_start = (cust.open_date < start) & (cust.close_date.isna() | (cust.close_date >= start))
        closed = open_start & cust.close_date.between(start, end)
        rows.append((q, closed.sum() / open_start.sum()))
    s = pd.Series(dict(rows))
    fig, ax = _figure("Closures per open card doubled in two years",
                      "Cards closed in the quarter ÷ cards open at the start of the quarter",
                      "Calendar quarters. Measured.")
    x = np.arange(len(s))
    ax.plot(x, s.values, color=_c("hsic"), lw=2.2, marker="o", ms=7, mec=_c("bg"), mew=1.5, zorder=3)
    for i in (0, len(s) - 1):
        ax.annotate(_pct(s.iloc[i]), (x[i], s.iloc[i]), xytext=(0, 12), textcoords="offset points",
                    ha="center", fontsize=13, fontweight="bold", color=_c("ink"))
    labels = [f"{q.start_time:%b}–{q.end_time:%b}\n{q.year}" for q in s.index]
    ax.set_xticks(x, labels)
    ax.set_ylim(0, s.max() * 1.25)
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.01))
    ax.set_xlim(-0.4, len(s) - 0.6)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.tick_params(axis="x", length=0)
    return style.save(fig, 8, "closures_per_quarter"), {"first": s.iloc[0], "last": s.iloc[-1]}


def closure_model_auc():
    t = pd.read_csv(C.MODEL_EVAL / "closure_comparison.csv").sort_values("roc_auc")
    fig, ax = _figure("No learned model beats card age alone",
                      "How well each method ranks the cards that went on to close (ROC-AUC; 0.5 = random)",
                      "Trained on cards open on 31 Jul 2025, tested once on cards open on 31 Jan 2026 (29,198 cards). Measured.",
                      figsize=(10, 5.625))
    y = np.arange(len(t))
    hero = t.model.eq("B2 card age").to_numpy()
    colors = np.where(hero, _c("hsic"), _c("muted"))
    ax.hlines(y, 0.5, t.roc_auc, color=colors, lw=2)
    ax.scatter(t.roc_auc, y, s=90, color=colors, edgecolor=_c("bg"), linewidth=1.5, zorder=3)
    for yi, (auc, h) in enumerate(zip(t.roc_auc, hero)):
        ax.text(auc + 0.004, yi, f"{auc:.3f}", va="center", fontsize=11.5,
                fontweight="bold" if h else "normal", color=_c("ink"))
    ax.axvline(0.5, color=_c("axis"), lw=1, ls=(0, (3, 3)))
    ax.set_yticks(y, [MODEL_NAMES[m] for m in t.model])
    for lbl, h in zip(ax.get_yticklabels(), hero):
        if h:
            lbl.set_fontweight("bold")
            lbl.set_color(_c("ink"))
    ax.set_xlim(0.48, 0.70)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    return style.save(fig, 8, "closure_model_auc"), {}


# ---------------------------------------------------------------- slide 9: who to prioritise
def kmeans_control(kn):
    k = pd.read_csv(TABLES / "segments_kmeans_clusters.csv")
    fig, ax = _figure("SoW clusters don't survive a year",
                      f"{len(k)} K-means clusters on FY25 card behaviour: each cluster's FY25 SoW vs the same customers' FY26 SoW",
                      f"{k.customers.sum():,} customers with enough purchases in both years. Measured.")
    for _, r in k.iterrows():
        ax.plot([0, 1], [r.sow_fy25, r.sow_fy26], color=_c("hsic"), lw=1.8, alpha=0.75,
                marker="o", ms=7, mec=_c("bg"), mew=1.2)
    lo25, hi25 = k.sow_fy25.min(), k.sow_fy25.max()
    lo26, hi26 = k.sow_fy26.min(), k.sow_fy26.max()
    for xb, lo, hi, side, label in ((-0.09, lo25, hi25, "right", f"{kn['seg_kmeans_fy25_sow_spread_pp']:.0f}pp\nspread"),
                                     (1.09, lo26, hi26, "left", f"{kn['seg_kmeans_fy26_sow_spread_pp']:.1f}pp\nspread")):
        ax.plot([xb, xb], [lo, hi], color=_c("secondary"), lw=1.2)
        for yv in (lo, hi):
            ax.plot([xb - 0.012, xb + 0.012], [yv, yv], color=_c("secondary"), lw=1.2)
        ax.text(xb + (-0.03 if side == "right" else 0.03), (lo + hi) / 2, label, ha=side, va="center",
                fontsize=13, fontweight="bold", color=_c("ink"))
    ax.text(0.5, 0.80, f"Next year's SoW explained by cluster: {kn['seg_kmeans_eta2'] * 100:.2f}%",
            ha="center", fontsize=12, color=_c("secondary"))
    ax.set_xticks([0, 1], ["FY25 (clusters built here)", "FY26 (same customers)"], fontsize=12)
    ax.set_xlim(-0.35, 1.35)
    ax.set_ylim(0, 0.88)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.set_ylabel("SoW")
    ax.tick_params(axis="x", length=0)
    return style.save(fig, 9, "kmeans_control"), {}


def box_outcomes():
    t = pd.read_csv(TABLES / "segments_box_table.csv").set_index("segment").loc[list(BOXES)][::-1]
    fig, axes = _figure("SoW is the same in every box; risk and value are not",
                        "Boxes built on 31 Jan 2026; outcomes measured Feb–Jul 2026 (bars show 95% confidence intervals)",
                        "Open cards only. Measured.", top=0.78, ncols=3, sharey=True)
    panels = [("sow", "sow", "FY26 SoW", "same everywhere", _pct),
              ("closure_6m", "closure", "6-month closure rate", "set by card age", _pct),
              ("nonhsic_per_cust", "nonhsic", "Off-card spend per customer", "set by frequency", lambda v: f"₹{v:,.0f}")]
    y = np.arange(len(t))
    for ax, (col, ci, name, verdict, fmt) in zip(axes, panels):
        lo, hi = t[f"{ci}_lo"], t[f"{ci}_hi"]
        ax.barh(y, t[col], height=0.6, color=_c("hsic"))
        ax.errorbar(t[col], y, xerr=[t[col] - lo, hi - t[col]], fmt="none", ecolor=_c("ink"), elinewidth=1, capsize=3)
        for yi, (v, h) in enumerate(zip(t[col], hi)):
            ax.text(h + hi.max() * 0.03, yi, fmt(v), va="center", fontsize=11, color=_c("ink"))
        ax.set_xlim(0, hi.max() * 1.45)
        ax.text(0, 1.10, name, transform=ax.transAxes, fontsize=12.5, fontweight="bold", color=_c("ink"))
        ax.text(0, 1.03, verdict, transform=ax.transAxes, fontsize=11, color=_c("secondary"))
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", visible=True)
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="both", length=0)
        ax.xaxis.set_major_formatter((lambda v, _: f"₹{v / 1000:.0f}k") if col == "nonhsic_per_cust"
                                     else (lambda v, _: f"{v * 100:.0f}%"))
    axes[0].set_yticks(y, [f"{s} · {BOXES[s][0]}\n{BOXES[s][1]}" for s in t.index])
    return style.save(fig, 9, "box_outcomes"), {}


def priority_matrix(kn):
    t = pd.read_csv(TABLES / "segments_box_table.csv").set_index("segment")
    sizes = pd.read_csv(TABLES / "segments_sizes.csv").set_index("segment").customers_at_score
    fig, ax = _figure("Low SoW is the whole book: prioritise by risk and value",
                      "Columns: closure risk (card age). Rows: value (purchase frequency at MetroMart, all payment methods)",
                      "Customers on 31 Jul 2026. Closure and off-card spend: boxes built on 31 Jan 2026, measured Feb–Jul 2026. Measured.")
    ax.set_axis_off()
    ax.set_xlim(0, 3.25)
    ax.set_ylim(0, 2.25)
    cells = {"D": (0, 1), "B": (1, 1), "E": (0, 0), "C": (1, 0)}
    offers = {"B": "Onboarding protection (O7)\n+ reward visibility (O3)", "C": "Activation milestone\n+ Prime trial (O7)",
              "D": "Threshold bonus (O8)\n+ reward visibility (O3)", "E": "Product fixes only (O1–O5),\nno paid incentive"}
    tag = {"B": "Highest priority"}
    pad = 0.05
    for s, (cx, cy) in cells.items():
        hero = s == "B"
        ax.add_patch(FancyBboxPatch((cx + pad, cy + pad), 1 - 2 * pad, 1 - 2 * pad, boxstyle="round,pad=0,rounding_size=0.04",
                                    fc=_c("bg"), ec=_c("hsic") if hero else _c("axis"), lw=2.2 if hero else 1))
        x0, ytop = cx + 0.1, cy + 0.86
        ax.text(x0, ytop, f"{s} · {BOXES[s][0]}", fontsize=14, fontweight="bold", va="top", color=_c("ink"))
        ax.text(x0, ytop - 0.15, f"{sizes[s]:,} customers", fontsize=11, va="top", color=_c("secondary"))
        if hero:
            ax.text(cx + 0.9, ytop - 0.15, tag[s], fontsize=10.5, fontweight="bold", va="top", ha="right", color=_c("hsic"))
        r = t.loc[s]
        ax.text(x0, ytop - 0.30, f"Closure {_pct(r.closure_6m)}  ·  Off-card ₹{r.nonhsic_per_cust:,.0f}\nSoW {_pct(r.sow)}",
                fontsize=10.5, va="top", color=_c("ink"), linespacing=1.4)
        ax.text(x0, ytop - 0.55, offers[s], fontsize=10, va="top", color=_c("secondary"), linespacing=1.3)
    # side panel: outside the grid
    ax.add_patch(FancyBboxPatch((2.1, 0.05), 1.1, 1.9, boxstyle="round,pad=0,rounding_size=0.04",
                                fc=_c("bg"), ec=_c("accent"), lw=1.6, ls=(0, (4, 3))))
    ax.text(2.2, 1.84, "Outside the grid", fontsize=10, va="top", color=_c("muted"))
    ax.text(2.2, 1.70, "A · Closed,\nstill shopping", fontsize=14, fontweight="bold", va="top", color=_c("ink"), linespacing=1.15)
    ax.text(2.2, 1.36, f"{kn['seg_A_n_score']:,} customers", fontsize=11, va="top", color=_c("secondary"))
    ax.text(2.2, 1.18, f"₹{kn['seg_A_post_close_net'] / 1e6:.1f}M spent at MetroMart\nafter closing the card",
            fontsize=10.5, va="top", color=_c("ink"), linespacing=1.4)
    ax.text(2.2, 0.90, "HSIC SoW: 0%, the most\nliteral low-SoW group", fontsize=10.5, va="top", color=_c("ink"), linespacing=1.4)
    ax.text(2.2, 0.62, "Win-back (O6)", fontsize=10, va="top", color=_c("secondary"))
    # axis labels
    for cx, label in ((0.5, "Mature card (12 months +)"), (1.5, "Young card (under 12 months)")):
        ax.text(cx, 2.08, label, ha="center", fontsize=11.5, fontweight="bold", color=_c("secondary"))
    for cy, label in ((1.5, "High\nfrequency"), (0.5, "Low/mid\nfrequency")):
        ax.text(-0.02, cy, label, ha="right", va="center", fontsize=11.5, fontweight="bold", color=_c("secondary"))
    ax.set_xlim(-0.32, 3.25)
    return style.save(fig, 9, "priority_matrix"), {}


def run():
    style.apply()
    kn = _key_numbers()
    paths, info = [], {}
    for fn, args in ((closure_by_card_age, ()), (closures_per_quarter, ()), (closure_model_auc, ()),
                     (kmeans_control, (kn,)), (box_outcomes, ()), (priority_matrix, (kn,))):
        path, extra = fn(*args)
        plt.close("all")
        paths.append(path)
        info[fn.__name__] = extra
    return paths, info


if __name__ == "__main__":
    paths, info = run()
    for p in paths:
        print(p.relative_to(C.ROOT))
    for name, extra in info.items():
        if extra:
            print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in extra.items()})
