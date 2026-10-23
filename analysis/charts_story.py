"""Charts for slides 4-7 (the decline; where it went; universal attrition; hypotheses tested). Owner: Mayank.

Writes outputs/charts/<slide:02d>_<name>.png, 16:9, 200 dpi. Numbers come from outputs/key_numbers.json and
Devansh's outputs/tables/ (X1 band table, K-means clusters), so run `python analysis/run_all.py` first.
shortcut: local style mirrors the dataviz reference palette; swap the block below for `from analysis import style`
(style.apply(), style.METHOD_COLORS, style.save) once Shreyash's analysis/style.py lands.

    python -m analysis.charts_story
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from analysis import config as C  # noqa: E402
from analysis import experiments_f as F, experiments_h as H  # noqa: E402

TABLES = C.OUTPUTS / "tables"

# ---------------------------------------------------------------- local style (shortcut, see docstring)
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, BLUE_LIGHT, NEG, POS, CRITICAL = "#2a78d6", "#86b6ef", "#e34948", "#1baf7a", "#d03b3b"
METHOD_COLORS = {"HSIC": "#2a78d6", "Cash/UPI": "#eb6834", "Wallet": "#1baf7a", "Debit": "#eda100", "Other CC": "#e87ba4"}
SEQ = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"])
SIZE, SIZE_TALL = (10, 5.625), (13.333, 7.5)   # both 16:9
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 11, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": AXIS, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 1, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 14, "axes.titlelocation": "left", "axes.titlepad": 14,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "legend.frameon": False, "lines.linewidth": 2,
    "lines.solid_capstyle": "round"})


def save(fig, slide, name):
    """Same signature as style.save: outputs/charts/{slide:02d}_{name}.png."""
    C.CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.CHARTS / f"{slide:02d}_{name}.png", dpi=200)
    plt.close(fig)


def source(fig, text):
    """Footnote with the label (Measured / Hypothesis) and the definition behind the chart."""
    fig.text(.01, .01, text, color=MUTED, fontsize=8.5, ha="left", va="bottom")
    fig.tight_layout(rect=(0, .04, 1, 1))


def signed(v, dp=1):
    """'+0.4', '−0.3', and '0.0' rather than '-0.0', with a true minus sign."""
    v = round(v, dp) + 0.0
    return (f"{v:+.{dp}f}" if v else f"{0:.{dp}f}").replace("-", "−")


def numbers():
    """Values from the last run_all.py, by key."""
    path = C.OUTPUTS / "key_numbers.json"
    n = {k: v["value"] for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
    missing = {"f1_sow_fy25", "x3_verdict", "x1_variance_ratio_fy25", "seg_kmeans_eta2"} - set(n)
    assert not missing, f"{path} has no {sorted(missing)}: run `python analysis/run_all.py` first"
    return n


# ---------------------------------------------------------------- slide 4
def chart_sow_trend(n):
    sq = F.quarterly_sow_table() * 100
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(sq))
    ax.plot(x, sq.to_numpy(), color=BLUE, marker="o", ms=8, mec=SURF, mew=2)
    for i in (0, len(sq) - 1):
        ax.annotate(f"{sq.iloc[i]:.1f}%", (x[i], sq.iloc[i]), xytext=(0, 12), textcoords="offset points", ha="center", fontweight="bold")
    for fy, (lo, hi) in {F.FY_A: (0, 3), F.FY_B: (4, 7)}.items():
        v = n[f"f1_sow_fy{fy % 100}"] * 100
        ax.hlines(v, lo - .3, hi + .3, color=MUTED, lw=1)
        ax.text(hi + .3, v + .8, f"FY{fy % 100} {v:.1f}%", color=INK2, ha="right", fontsize=10)
    ax.set_xticks(x, list(sq.index)); ax.set_ylim(0, 40); ax.set_ylabel("HSIC share of wallet (%)")
    ax.set_title(f"HSIC share of wallet halved: {sq.iloc[0]:.1f}% → {sq.iloc[-1]:.1f}% in eight quarters "
                 f"({signed(n['f1_slope_pp_per_quarter'])}pp a quarter)")
    source(fig, "Measured · HSIC ÷ total MetroMart net ₹ while the card is active, ratio of sums · FY = Aug–Jul")
    save(fig, 4, "sow_trend")


def chart_per_card(n):
    g = F.per_card_monthly_table()
    x = g.index.to_timestamp()
    fig, ax = plt.subplots(figsize=SIZE)
    marks = [g.index.get_loc(pd.Period("2024-08", "M")), g.index.get_loc(pd.Period("2026-05", "M"))]   # the F14 months
    for col, c, lab in [("net_per_card", MUTED, "MetroMart spend per card"), ("hsic_per_card", BLUE, "HSIC spend per card")]:
        ax.plot(x, g[col], color=c, label=lab)
        for i in marks:
            ax.plot(x[i], g[col].iloc[i], "o", color=c, ms=8, mec=SURF, mew=2)
            ax.annotate(f"₹{g[col].iloc[i]:,.0f}", (x[i], g[col].iloc[i]), xytext=(0, 12), textcoords="offset points",
                        ha="center", fontweight="bold")
    ax.set_xlim(x[0] - pd.Timedelta(days=30), x[-1] + pd.Timedelta(days=30)); ax.set_ylim(0, 1300)
    ax.set_ylabel("Net ₹ per active card per month"); ax.legend(loc="lower left")
    ax.set_title("Customers kept shopping and changed how they pay: spend per card flat, HSIC per card halved")
    source(fig, f"Measured · cards whose active window covers the month: {n['f14_aug24_cards']:,} (Aug 2024) → "
                f"{n['f14_may26_cards']:,} (May 2026) · net of returns")
    save(fig, 4, "per_card")


def chart_bridge(n):
    b = F.bridge_table() * 100
    labels = {"FY25 SoW": "FY25 SoW", "Leavers": "Card closures", "Stayers": f"Continuously open\ncards ({n['f2_stayers_n']:,})",
              "Joiners": "New cards", "FY26 SoW": "FY26 SoW"}
    fig, ax = plt.subplots(figsize=SIZE)
    level = b.iloc[0]
    for i, (k, v) in enumerate(b.items()):
        if i in (0, len(b) - 1):
            ax.bar(i, v, width=.5, color=BLUE)
            ax.text(i, v + .6, f"{v:.1f}%", ha="center", fontweight="bold")
        else:
            ax.bar(i, abs(v), bottom=min(level, level + v), width=.5, color=NEG if v < 0 else POS)
            ax.text(i, max(level, level + v) + .6, f"{signed(v, 2)}pp", ha="center")
            level += v
    ax.set_xticks(range(len(b)), [labels[k] for k in b.index])
    ax.set_ylim(0, 36); ax.set_ylabel("HSIC share of wallet (%)"); ax.grid(axis="x", visible=False)
    ax.set_title("The whole decline comes from cards that stayed open")
    source(fig, "Measured · Bridge: FY25 all → continuously open cards FY25 → same cards FY26 → FY26 all; reconciles exactly")
    save(fig, 4, "bridge")


# ---------------------------------------------------------------- slide 5
def chart_mix_shift(n):
    keys = ["Cash/UPI", "Debit", "Other CC", "Wallet"]
    v = pd.Series({k: n[f"f3_{F.slug(k)}_share_of_loss"] * 100 for k in keys})
    fig, ax = plt.subplots(figsize=SIZE)
    y = np.arange(len(v))[::-1]
    ax.barh(y, v.to_numpy(), height=.5, color=[METHOD_COLORS[k] for k in keys])
    for yi, (k, val) in zip(y, v.items()):
        ax.text(val + .8, yi, f"{val:.0f}%  ({signed(n[f'f3_{F.slug(k)}_change_pp'])}pp of spend)", va="center")
    ax.set_yticks(y, ["Cash/UPI", "Debit card", "Other bank credit card", "MetroMart Wallet"])
    ax.set_xlim(0, 60); ax.set_xlabel("Share of HSIC's lost share of wallet (%)"); ax.grid(axis="y", visible=False)
    ax.set_title(f"Cash/UPI took almost half of HSIC's lost share ({signed(n['f3_hsic_change_pp'])}pp)")
    source(fig, f"Measured · payment-mix shift FY25 → FY26 on the {n['f2_stayers_n']:,} continuously open cards · "
                "why Cash/UPI (immediacy?) is a Hypothesis (H-imm)")
    save(fig, 5, "mix_shift")


def chart_ticket_bands(n):
    bands = [F.slug(b) for b in C.TICKET_LABELS]
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(bands))
    for off, fy, c in [(-.14, 25, BLUE_LIGHT), (.14, 26, BLUE)]:
        vals = [n[f"f5_hsic_share_fy{fy}_{b}"] * 100 for b in bands]
        ax.bar(x + off, vals, width=.26, color=c, label=f"FY{fy}")
        for xi, val in zip(x + off, vals):
            ax.text(xi, val + .5, f"{val:.1f}%", ha="center", fontsize=10)
    names = ["Under ₹1k", "₹1–3k", "₹3–10k", "Capped ₹9,999.99"]
    ax.set_xticks(x, [f"{nm}\nCash/UPI {signed(n[f'f5_cash_upi_gain_pp_{b}'])}pp" for nm, b in zip(names, bands)]); ax.set_ylim(0, 35)
    ax.set_ylabel("HSIC share of purchases (%)"); ax.legend(loc="upper left", ncol=2); ax.grid(axis="x", visible=False)
    ax.set_title("HSIC lost about a third of its share in every ticket band; Cash/UPI gained in every band")
    source(fig, f"Measured · share of active-window Sale rows by ticket size · MetroMart Wallet carries "
                f"{n['f7_wallet_share_capped_fy25']:.1%} → {n['f7_wallet_share_capped_fy26']:.1%} of capped purchases")
    save(fig, 5, "ticket_bands")


def chart_capped_mix(n):
    m = F.capped_mix_table()[list(METHOD_COLORS)] * 100
    names = {"HSIC": "HSIC", "Cash/UPI": "Cash/UPI", "Wallet": "MetroMart Wallet", "Debit": "Debit card", "Other CC": "Other bank CC"}
    fig, ax = plt.subplots(figsize=SIZE)
    y = [1, 0]
    left = np.zeros(len(m))
    for k, c in METHOD_COLORS.items():
        ax.barh(y, m[k], left=left, height=.5, color=c, edgecolor=SURF, linewidth=2, label=names[k])
        for yi, lft, v in zip(y, left, m[k]):
            if v >= 7:   # label only where it fits inside the segment
                ax.text(lft + v / 2, yi, f"{v:.1f}%", ha="center", va="center", color=INK if k == "Debit" else "white", fontweight="bold")
        left += m[k].to_numpy()
    ax.set_yticks(y, [f"FY{fy % 100}" for fy in m.index]); ax.set_xlim(0, 100); ax.set_xlabel("Share of capped ₹9,999.99 purchases (%)")
    ax.grid(axis="y", visible=False); ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(.5, -.18), fontsize=9.5)
    ax.set_title(f"Wallet carries half of the biggest baskets ({m.loc[F.FY_B, 'Wallet']:.0f}%); HSIC, the card with financing, "
                 f"{m.loc[F.FY_B, 'HSIC']:.0f}%")
    source(fig, "Measured · active-window Sale rows at exactly ₹9,999.99 (the data's cap, which understates big-ticket spend)")
    save(fig, 5, "capped_mix")


# ---------------------------------------------------------------- slide 6
def chart_slices(n):
    d = H.slice_table().reset_index(drop=True)
    fig, ax = plt.subplots(figsize=SIZE_TALL)
    y = np.arange(len(d))[::-1]
    ax.hlines(y, d.sow_fy26 * 100, d.sow_fy25 * 100, color=AXIS, lw=2)
    ax.plot(d.sow_fy25 * 100, y, "o", color=BLUE_LIGHT, ms=8, mec=SURF, mew=2, label="FY25")
    ax.plot(d.sow_fy26 * 100, y, "o", color=BLUE, ms=8, mec=SURF, mew=2, label="FY26")
    ax.set_yticks(y, [f"{a}: {b}" for a, b in zip(d.dimension, d.level)], fontsize=8.5)
    ax.set_xlim(10, 35); ax.set_xlabel("HSIC share of wallet (%)"); ax.legend(loc="lower left")
    lo, hi = -d.change_pp.max(), -d.change_pp.min()
    ax.set_title(f"Every slice lost {lo:.0f}–{hi:.0f}pp of share: no group is spared, so silent attrition is universal")
    source(fig, "Measured · FY25 vs FY26 SoW, active window · membership, age, limit, APR, vintage, category, future closers")
    save(fig, 6, "slices")


def chart_gate(n):
    tiles = [("Variance ratio", f"{(n['x1_variance_ratio_fy25'] + n['x1_variance_ratio_fy26']) / 2:.2f}",
              f"FY25 {n['x1_variance_ratio_fy25']:.3f} · FY26 {n['x1_variance_ratio_fy26']:.3f}",
              f"Needs ≥ {C.GATE['variance_ratio_min']:.2f} both years"),
             ("Split-half reliability", signed(n["x1_split_half_r"], 3),
              f"95% CI {signed(n['x1_split_half_ci_lo'], 3)} to {signed(n['x1_split_half_ci_hi'], 3)}",
              f"Needs ≥ {C.GATE['split_half_min']:.2f}"),
             ("Year-over-year persistence", signed(n["x1_persistence_r"], 3),
              f"95% CI {signed(n['x1_persistence_ci_lo'], 3)} to {signed(n['x1_persistence_ci_hi'], 3)}",
              f"Needs ≥ {C.GATE['persistence_min']:.2f}")]
    fig, axs = plt.subplots(1, 3, figsize=SIZE)
    for ax, (lab, val, sub, need) in zip(axs, tiles):
        ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.add_patch(FancyBboxPatch((.04, .1), .92, .78, boxstyle="round,pad=0,rounding_size=.04", fc="white", ec=GRID, lw=1))
        ax.text(.12, .78, lab, color=INK2, fontsize=12, va="top")
        ax.text(.12, .62, val, color=INK, fontsize=40, fontweight="bold", va="top")
        ax.text(.12, .38, sub, color=MUTED, fontsize=10, va="top")
        ax.text(.12, .29, need, color=INK2, fontsize=10, va="top")
        ax.text(.12, .19, "✕  Fails the gate", color=CRITICAL, fontsize=11, fontweight="bold", va="top")
    fig.suptitle("The heterogeneity gate: customers don't differ in how often they reach for the card",
                 x=.01, ha="left", fontweight="bold", fontsize=14)
    source(fig, f"Measured · per-customer HSIC row share, {n['x1_gate_n_fy25']:,} customers with ≥ {C.GATE['min_rows']} active rows · "
                "a variable that fails is not used for targeting")
    save(fig, 6, "gate")


def chart_band_movement(n):
    counts = pd.read_csv(TABLES / "x1_sow_band_movement.csv", index_col=0)
    m = counts.div(counts.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=SIZE)
    ax.imshow(m.to_numpy(), cmap=SEQ, vmin=0, vmax=50, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.to_numpy()[i, j]
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=13, fontweight="bold", color="white" if v >= 25 else INK)
    ax.set_xticks(range(4), list(m.columns)); ax.set_yticks(range(4), list(m.index))
    ax.set_xlabel("FY26 band"); ax.set_ylabel("FY25 band"); ax.grid(False)
    ax.tick_params(length=0); ax.xaxis.set_label_position("top"); ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"Whatever band a customer starts in, next year looks the same: {n['x1_band_to_zero_min']:.0%}–"
                 f"{n['x1_band_to_zero_max']:.0%} fall to Zero", fontsize=13, pad=34)
    source(fig, f"Measured · {n['x1_sow_filter_n']:,} cardholders with ≥ {C.MIN_PURCHASES_PER_PERIOD} purchases in each FY · "
                f"Zero = no net HSIC spend; Low / Mid / High = terciles of non-zero FY25 SoW (cuts {n['x1_band_edges_low_mid']:.1%}, "
                f"{n['x1_band_edges_mid_high']:.1%}), same cuts in FY26 · row shares")
    save(fig, 6, "band_movement")


# ---------------------------------------------------------------- slide 7
def chart_silent_null(n):
    d = H.silent_attrition_table()
    fig, ax = plt.subplots(figsize=SIZE)
    x = np.arange(len(d))
    err = np.vstack([d.excess_time - d.excess_time_lo, d.excess_time_hi - d.excess_time]) * 100
    for off, col, c, lab, e in [(-.14, "excess_fixed", MUTED, "vs own past HSIC share (the usual count)", None),
                                (.14, "excess_time", BLUE, "vs the portfolio trend in the same months", err)]:
        ax.bar(x + off, d[col] * 100, width=.26, color=c, label=lab, yerr=e, ecolor=INK2, capsize=4)
        for xi, v in zip(x + off, d[col] * 100):
            ax.text(xi, max(v, 0) + 1.2, f"{signed(v)}pp", ha="center", fontsize=10)
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_xticks(x, [f"6 months after {c.date()}" for c in d.cutoff]); ax.set_ylim(-3, 28)
    ax.set_ylabel("Excess zero-HSIC cardholders (pp)"); ax.legend(loc="upper left"); ax.grid(axis="x", visible=False)
    ax.set_title("“Silent attriters” vanish against the trend: +21pp by the usual count, ≈0 once calendar-matched")
    source(fig, "Measured · cards open throughout, ≥ 1 HSIC row in the 12-month lookback, ≥ 1 active row in the 6-month horizon · "
                "error bars: 95% CI over customers")
    save(fig, 7, "silent_null")


def chart_decay(n):
    g = H.pre_closure_table().sort_index(ascending=False)
    x = -g.index.to_numpy()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=SIZE, sharex=True)
    a1.plot(x, g.raw * 100, color=BLUE, marker="o", ms=8, mec=SURF, mew=2, label="Cards that later close")
    a1.plot(x, g.expected * 100, color=MUTED, label="Whole portfolio, same months")
    a1.set_ylim(15, 32); a1.set_ylabel("HSIC share of purchases (%)"); a1.legend(loc="lower left", fontsize=9)
    a1.set_title("Raw: looks like decay", fontsize=12)
    a2.fill_between(x, -g.chance_band * 100, g.chance_band * 100, color=MUTED, alpha=.15, lw=0, label="95% band of chance")
    a2.plot(x, g.excess * 100, color=BLUE, marker="o", ms=8, mec=SURF, mew=2, label="Closers minus portfolio")
    a2.axhline(0, color=AXIS, lw=1); a2.set_ylim(-5, 5); a2.set_ylabel("Excess HSIC share (pp)")
    a2.legend(loc="lower left", fontsize=9); a2.set_title("Calendar-adjusted: no decay", fontsize=12)
    for a in (a1, a2):
        a.set_xlabel("Months before closure")
    fig.suptitle("The pre-closure “decay” is the calendar: closures cluster late, when everyone's SoW is lower",
                 x=.01, ha="left", fontweight="bold", fontsize=14)
    source(fig, f"Measured · active-window rows of every closed card · 30-day months before the close date · "
                f"slope {signed(n['x4_slope_pp_per_month'], 2)}pp a month (95% CI {signed(n['x4_slope_ci_lo_pp'], 2)} to "
                f"{signed(n['x4_slope_ci_hi_pp'], 2)})")
    save(fig, 7, "decay_raw_vs_adj")


def chart_kmeans(n):
    k = pd.read_csv(TABLES / "segments_kmeans_clusters.csv").sort_values("sow_fy25")
    fig, ax = plt.subplots(figsize=SIZE)
    for _, r in k.iterrows():
        ax.plot([0, 1], [r.sow_fy25 * 100, r.sow_fy26 * 100], color=AXIS, lw=2, zorder=1)
    ax.scatter(np.zeros(len(k)), k.sow_fy25 * 100, s=k.customers / 8, color=BLUE_LIGHT, edgecolor=SURF, lw=2, zorder=2)
    ax.scatter(np.ones(len(k)), k.sow_fy26 * 100, s=k.customers / 8, color=BLUE, edgecolor=SURF, lw=2, zorder=2)
    label_y = (k.sow_fy25 * 100).to_numpy(copy=True)
    for i in range(1, len(label_y)):          # keep labels ≥ 3.5pp apart (sorted ascending)
        label_y[i] = max(label_y[i], label_y[i - 1] + 3.5)
    for ly, (_, r) in zip(label_y, k.iterrows()):
        ax.text(-.06, ly, f"{r.sow_fy25:.0%} · {r.customers:,.0f} customers", ha="right", va="center", fontsize=9, color=INK2)
    ax.text(1.06, k.sow_fy26.mean() * 100, f"all {k.sow_fy26.min():.0%}–{k.sow_fy26.max():.0%}", ha="left", va="center",
            fontsize=11, fontweight="bold")
    ax.set_xlim(-.5, 1.5); ax.set_ylim(-5, 90); ax.set_xticks([0, 1], ["FY25 (clusters built)", "FY26 (same customers)"])
    ax.set_ylabel("Mean customer SoW in the cluster (%)"); ax.grid(axis="x", visible=False)
    ax.set_title(f"K-means finds {n['seg_kmeans_k']} tidy clusters {n['seg_kmeans_fy25_sow_spread_pp']:.0f}pp apart; "
                 f"a year later they sit {n['seg_kmeans_fy26_sow_spread_pp']:.1f}pp apart")
    source(fig, f"Measured · {n['seg_kmeans_customers']:,} customers clustered on FY25 behaviour · stable (ARI {n['seg_kmeans_ari']:.2f}) "
                f"but explains {n['seg_kmeans_eta2']:.2%} of FY26 SoW (η², 95% CI {n['seg_kmeans_eta2_lo']:.2%}–"
                f"{n['seg_kmeans_eta2_hi']:.2%}) · dot size = customers")
    save(fig, 7, "kmeans")


CHARTS = [chart_sow_trend, chart_per_card, chart_bridge, chart_mix_shift, chart_ticket_bands, chart_capped_mix,
          chart_slices, chart_gate, chart_band_movement, chart_silent_null, chart_decay, chart_kmeans]

if __name__ == "__main__":
    n = numbers()
    for c in CHARTS:
        c(n)
        print("wrote", c.__name__)
