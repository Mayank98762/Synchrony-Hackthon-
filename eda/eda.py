"""MetroMart-HSIC deep EDA: SoW, silent attrition, closures, rewards, segments.

Run:  C:\\Users\\asus\\anaconda3\\python.exe eda\\eda.py   (from repo root)
Reads the 4 case CSVs read-only; writes everything to outputs/eda/.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, silhouette_score
from sklearn.cluster import KMeans

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "eda"
TAB, CH = OUT / "tables", OUT / "charts"
for d in (TAB, CH):
    d.mkdir(parents=True, exist_ok=True)
DATA_START, DATA_END = pd.Timestamp("2024-08-01"), pd.Timestamp("2026-07-31")
LOW_SOW = 0.15          # "low SoW" threshold on trailing-12m spend SoW
NUM = {}                # every number quoted in the report


def num(key, val):
    NUM[key] = float(val) if isinstance(val, (np.floating, np.integer)) else val
    return val


def save(df, name, index=True):
    df.to_csv(TAB / f"{name}.csv", index=index)
    return df


def sow(df):
    return df.h.sum() / df.net.sum()


# ---------------------------------------------------------------- chart style
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
S = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
METHOD_COLOR = {"HSIC Bank Credit Card": S[0], "Cash/UPI": S[1], "MetroMart Wallet": S[2],
                "Debit Card": S[3], "Other Bank Credit Card": S[6]}
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": .6, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 11, "axes.titlecolor": INK,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "legend.frameon": False})


def fig_save(fig, name):
    fig.tight_layout()
    fig.savefig(CH / f"{name}.png", dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------- 1. load, validate, enrich
cust = pd.read_csv(ROOT / "Customer Data.csv", parse_dates=["Credit_Card_Open_Date", "Credit_Card_Closed_Date"])
txn = pd.read_csv(ROOT / "Transactions Data.csv", parse_dates=["Transaction_Date"])
cat = pd.read_csv(ROOT / "Category Code.csv")
pay = pd.read_csv(ROOT / "Payment Code.csv")

assert cust.Customer_ID.is_unique and txn.Transaction_ID.is_unique
assert txn.Customer_ID.isin(cust.Customer_ID).all(), "orphan transactions"
assert txn.Category_Code.isin(cat.Category_Code).all() and txn.Payment_Code.isin(pay.Payment_Code).all()
assert txn.loc[txn.Transaction_Type == "Return", "Number_of_Transactions"].isna().all()
assert txn.loc[txn.Transaction_Type == "Sale", "Number_of_Transactions"].notna().all()
assert (txn.Transaction_Amount > 0).all()
assert txn.Transaction_Date.between(DATA_START, DATA_END).all()
assert not (cust.Credit_Card_Closed_Date < cust.Credit_Card_Open_Date).any()
assert (cust.Credit_Card_Open_Date.isna() == cust.Credit_Card_Limit.isna()).all()

dq = pd.DataFrame({
    "check": ["customers", "transactions", "returns (rows)", "returns with null n_txn", "customers without card",
              "closed cards", "cards opened after data end", "rows capped at 9,999.99", "duplicate transaction rows (excl. ID)",
              "customers without transactions"],
    "value": [len(cust), len(txn), (txn.Transaction_Type == "Return").sum(),
              txn.Number_of_Transactions.isna().sum(), cust.Credit_Card_Open_Date.isna().sum(),
              cust.Credit_Card_Closed_Date.notna().sum(), (cust.Credit_Card_Open_Date > DATA_END).sum(),
              (txn.Transaction_Amount >= 9999.99).sum(), txn.drop(columns="Transaction_ID").duplicated().sum(),
              (~cust.Customer_ID.isin(txn.Customer_ID)).sum()]})
save(dq, "01_data_quality", index=False)

t = txn.merge(cust, on="Customer_ID").merge(cat, on="Category_Code").merge(pay, on="Payment_Code")
t["is_ret"] = t.Transaction_Type == "Return"
t["net"] = np.where(t.is_ret, -t.Transaction_Amount, t.Transaction_Amount)
t["n_txn"] = t.Number_of_Transactions.fillna(0)          # case rule: returns = 0 transactions
t["ym"] = t.Transaction_Date.dt.to_period("M")
t["FY"] = np.where(t.Transaction_Date.dt.month >= 8, t.Transaction_Date.dt.year + 1, t.Transaction_Date.dt.year)
t["half"] = "FY" + (t.FY % 100).astype(str) + np.where(t.Transaction_Date.dt.month.isin([8, 9, 10, 11, 12, 1]), "-H1", "-H2")
t["has_card"] = t.Credit_Card_Open_Date.notna()
t["active"] = t.has_card & (t.Transaction_Date >= t.Credit_Card_Open_Date) & (
    t.Credit_Card_Closed_Date.isna() | (t.Transaction_Date <= t.Credit_Card_Closed_Date))
t["is_h"] = t.Payment_Code == 3
t["h"] = t.net * t.is_h
t["prime"] = t.Membership_Type == "Prime"
t["rate"] = np.select([t.prime & (t.Category_Code == 1), t.prime & (t.Category_Code == 2)], [.05, .03], .01)
t["reward"] = t.h * t.rate                                  # returns claw back
t["credit_ym"] = t.ym + 1                                   # credited next billing cycle
assert not (t.is_h & ~t.active).any(), "HSIC rows outside active window"
assert np.isclose(t[~t.is_ret].Transaction_Amount.sum() - t[t.is_ret].Transaction_Amount.sum(), t.net.sum())
a = t[t.active].copy()                                      # SoW universe: active-card rows only
num("rows_active", len(a)); num("rows_total", len(t))
num("cardholders", cust.Credit_Card_Open_Date.notna().sum())
num("phase_rows", t.assign(p=np.select([~t.has_card, t.Transaction_Date < t.Credit_Card_Open_Date, t.active],
                                       ["no card", "before open", "active"], "after close")).p.value_counts().to_dict())

# ---------------------------------------------------------------- 2. portfolio SoW
fy = a.groupby("FY")[["h", "net"]].sum().assign(sow=lambda d: d.h / d.net)
fy["customers"] = a.groupby("FY").Customer_ID.nunique()
save(fy, "02_sow_by_fy")
num("sow_fy25", fy.sow[2025]); num("sow_fy26", fy.sow[2026])
mon = a.groupby("ym").agg(h=("h", "sum"), net=("net", "sum"), cust=("Customer_ID", "nunique"),
                          rows=("net", "size"), hrows=("is_h", "sum"))
mon["sow"], mon["row_share"] = mon.h / mon.net, mon.hrows / mon.rows
mon["net_per_cust"] = mon.net / mon.cust
save(mon, "02_sow_by_month")
num("sow_first_month", mon.sow.iloc[0]); num("sow_last_month", mon.sow.iloc[-1])
slope = np.polyfit(np.arange(len(mon)), mon.sow.values, 1)[0]
num("sow_slope_pp_per_month", slope * 100)
half = save(a.groupby("half")[["h", "net"]].sum().assign(sow=lambda d: d.h / d.net), "02_sow_by_half")

mix = a.pivot_table(index="ym", columns="Payment_Method", values="net", aggfunc="sum")
mix = mix.div(mix.sum(1), axis=0)
save(mix, "02_active_mix_by_month")
fymix = lambda d: d.pivot_table(index="FY", columns="Payment_Method", values="net", aggfunc="sum").pipe(
    lambda x: x.div(x.sum(1), axis=0))
mix_fy = fymix(a)
bench = fymix(t[~t.has_card])                               # non-cardholders = market benchmark
nonh = fymix(a[~a.is_h])                                    # mix of the non-HSIC remainder
save(pd.concat({"cardholders_active": mix_fy, "non_cardholders": bench, "cardholders_nonHSIC_only": nonh}),
     "02_mix_by_fy")
num("mix_change_pp", ((mix_fy.loc[2026] - mix_fy.loc[2025]) * 100).round(2).to_dict())
num("bench_change_pp", ((bench.loc[2026] - bench.loc[2025]) * 100).round(2).to_dict())

fig, ax = plt.subplots(figsize=(9, 4))
x = mon.index.to_timestamp()
ax.plot(x, mon.sow * 100, color=S[0], lw=2, marker="o", ms=4)
ax.axvline(pd.Timestamp("2025-08-01"), color=INK2, lw=1, ls="--")
ax.text(pd.Timestamp("2025-08-10"), mon.sow.max() * 100, "FY26 →", color=INK2, va="top")
ax.text(pd.Timestamp("2024-08-10"), mon.sow.max() * 100, "FY25", color=INK2, va="top")
for i in (0, len(mon) - 1):
    ax.annotate(f"{mon.sow.iloc[i]:.1%}", (x[i], mon.sow.iloc[i] * 100), textcoords="offset points", xytext=(0, 8), ha="center", color=INK)
ax.set_ylabel("HSIC SoW, % of active net spend"); ax.set_ylim(0, 40)
ax.set_title(f"HSIC Share of Wallet fell from {mon.sow.iloc[0]:.0%} to {mon.sow.iloc[-1]:.0%} in 24 months (≈{slope*100:.1f}pp a month)")
fig_save(fig, "01_sow_monthly")

fig, ax = plt.subplots(figsize=(9, 4.2))
nudge = {"Debit Card": -.7, "Other Bank Credit Card": .7}   # the two end within 0.1pp of each other
for m_ in mix.columns:
    ax.plot(x, mix[m_] * 100, color=METHOD_COLOR[m_], lw=2)
    ax.text(x[-1] + pd.Timedelta(days=12), mix[m_].iloc[-1] * 100 + nudge.get(m_, 0), f"{m_} {mix[m_].iloc[-1]:.0%}", color=INK2, va="center", fontsize=9)
ax.set_xlim(x[0], x[-1] + pd.Timedelta(days=200)); ax.set_ylabel("% of active cardholder net spend")
ax.set_title("HSIC's lost share went to Cash/UPI, Debit and Other-bank cards; Wallet held steady")
fig_save(fig, "02_payment_mix_monthly")

# ---------------------------------------------------------------- 3. SoW by attribute (is the decline concentrated?)
a["age_band"] = pd.cut(a.Age, [17, 25, 35, 45, 60], labels=["18-25", "26-35", "36-45", "46-60"])
a["limit_band"] = pd.qcut(a.Credit_Card_Limit, 4, labels=["L1 low", "L2", "L3", "L4 high"])
a["apr_band"] = pd.qcut(a.Credit_Card_APR, 4, labels=["APR Q1 low", "Q2", "Q3", "APR Q4 high"])
a["tenure_m"] = (a.ym - a.Credit_Card_Open_Date.dt.to_period("M")).apply(lambda p: p.n)
a["tenure_band"] = pd.cut(a.tenure_m, [-1, 5, 11, 23, 35, 100], labels=["0-5m", "6-11m", "12-23m", "24-35m", "36m+"])
a["open_year"] = a.Credit_Card_Open_Date.dt.year.astype(str)
rows = []
for col in ["Membership_Type", "Gender", "age_band", "limit_band", "apr_band", "tenure_band", "open_year", "Category"]:
    g = a.groupby([col, "FY"], observed=True)[["h", "net"]].sum()
    g = (g.h / g.net).unstack()
    for k, r in g.iterrows():
        rows.append({"dimension": col, "level": k, "sow_fy25": r.get(2025), "sow_fy26": r.get(2026)})
by_attr = pd.DataFrame(rows)
by_attr["change_pp"] = (by_attr.sow_fy26 - by_attr.sow_fy25) * 100
save(by_attr, "03_sow_by_attribute", index=False)
chg = by_attr.dropna().change_pp
num("attr_change_pp_range", [round(chg.min(), 1), round(chg.max(), 1)])

fig, ax = plt.subplots(figsize=(8, 9))
b = by_attr.dropna().reset_index(drop=True)
yy = np.arange(len(b))[::-1]
ax.hlines(yy, b.sow_fy26 * 100, b.sow_fy25 * 100, color=GRID, lw=3)
ax.scatter(b.sow_fy25 * 100, yy, color=S[0], s=36, label="FY25", zorder=3)
ax.scatter(b.sow_fy26 * 100, yy, color=S[1], s=36, label="FY26", zorder=3)
ax.set_yticks(yy, [f"{d.split('_')[0]}: {l}" for d, l in zip(b.dimension, b.level)], fontsize=8)
ax.set_xlabel("HSIC SoW (%)"); ax.legend(loc="lower right")
ax.set_title("The SoW drop is the same size in every segment, cohort and category")
fig_save(fig, "03_sow_by_attribute_dumbbell")

# ---------------------------------------------------------------- 4. is HSIC usage a customer trait? (noise vs signal)
pm_rows = a.groupby(["ym", "Payment_Code"]).size().unstack()
pm_rows = pm_rows.div(pm_rows.sum(1), axis=0)                # monthly row-share per method (time-varying null)
full_ids = cust[(cust.Credit_Card_Open_Date < DATA_START) & cust.Credit_Card_Closed_Date.isna()].Customer_ID
f = a[a.Customer_ID.isin(full_ids)].copy()
num("full_window_customers", len(full_ids))
disp = {}
for pc, name in zip(pay.Payment_Code, pay.Payment_Method):
    p = f.ym.map(pm_rows[pc])
    g = pd.DataFrame({"x": f.Payment_Code == pc, "e": p, "v": p * (1 - p), "c": f.Customer_ID}).groupby("c").sum()
    disp[name] = ((g.x - g.e) ** 2 / g.v).mean()             # ≈1 => no customer-level preference beyond chance
num("dispersion_by_method", {k: round(v, 3) for k, v in disp.items()})

cf = f.groupby(["Customer_ID", "FY"]).agg(h=("h", "sum"), net=("net", "sum"), rows=("net", "size"),
                                          hrows=("is_h", "sum")).unstack()
cf = cf[(cf["rows"] >= 3).all(axis=1) & (cf["net"] > 0).all(axis=1)]
cf_s25, cf_s26 = cf[("h", 2025)] / cf[("net", 2025)], cf[("h", 2026)] / cf[("net", 2026)]
num("corr_customer_sow_fy25_fy26", np.corrcoef(cf_s25, cf_s26)[0, 1]); num("corr_n", len(cf))
q = pd.qcut(cf_s25.rank(method="first"), 4, labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"])
rtm = pd.DataFrame({"q": q, "h25": cf[("h", 2025)], "n25": cf[("net", 2025)], "h26": cf[("h", 2026)], "n26": cf[("net", 2026)]}
                   ).groupby("q", observed=True).sum()
rtm = pd.DataFrame({"customers": q.value_counts().sort_index(), "sow_fy25": rtm.h25 / rtm.n25, "sow_fy26": rtm.h26 / rtm.n26})
save(rtm, "04_regression_to_mean")
# persistence of other behaviours (what IS a customer trait?)
allc = t.groupby(["Customer_ID", "FY"]).agg(rows=("net", "size"), net=("net", "sum")).unstack(fill_value=0)
gro = t.assign(g=t.Category_Code == 1).groupby(["Customer_ID", "FY"]).g.mean().unstack().dropna()
tick = t[~t.is_ret].groupby(["Customer_ID", "FY"]).Transaction_Amount.mean().unstack().dropna()
pers = pd.Series({
    "HSIC SoW (cardholders, full window)": np.corrcoef(cf_s25, cf_s26)[0, 1],
    "Visit rows per FY": np.corrcoef(allc[("rows", 2025)], allc[("rows", 2026)])[0, 1],
    "Net spend per FY": np.corrcoef(allc[("net", 2025)], allc[("net", 2026)])[0, 1],
    "Grocery share of rows": np.corrcoef(gro[2025], gro[2026])[0, 1],
    "Average ticket": np.corrcoef(tick[2025], tick[2026])[0, 1]}, name="corr_FY25_vs_FY26")
save(pers, "04_behaviour_persistence")
num("persistence", pers.round(3).to_dict())
# empirical-Bayes reliability of customer SoW (beta-binomial method of moments on rows)
n_, x_ = cf[("rows", 2026)], cf[("hrows", 2026)]
p0 = x_.sum() / n_.sum()
between_var = max(((x_ / n_ - p0) ** 2).mean() - (p0 * (1 - p0) / n_).mean(), 0)
num("eb_between_customer_var", between_var)
num("eb_reliability_median", between_var / (between_var + p0 * (1 - p0) / n_.median()))

fig, ax = plt.subplots(figsize=(7.5, 4))
xx = np.arange(4)
ax.bar(xx - .2, rtm.sow_fy25 * 100, .38, color=S[0], label="FY25 (used to rank)")
ax.bar(xx + .2, rtm.sow_fy26 * 100, .38, color=S[1], label="FY26 (next year)")
for i, v in enumerate(rtm.sow_fy26):
    ax.text(i + .2, v * 100 + 1, f"{v:.0%}", ha="center", color=INK, fontsize=9)
ax.set_xticks(xx, rtm.index); ax.set_xlabel("Customer FY25 SoW quartile"); ax.set_ylabel("SoW (%)")
ax.set_title("Last year's low-SoW customers are not this year's: every quartile reverts to ~19%"); ax.legend()
fig_save(fig, "04_regression_to_mean")

# ---------------------------------------------------------------- 5. silent attrition vs chance
def zero_hsic_test(hist_start, eval_start, eval_end):
    """Open cards active over hist+eval with >=2 eval rows and >=1 hist row; observed vs expected zero-HSIC."""
    ids = cust[(cust.Credit_Card_Open_Date <= hist_start) &
               (cust.Credit_Card_Closed_Date.isna() | (cust.Credit_Card_Closed_Date > eval_end))].Customer_ID
    s = a[a.Customer_ID.isin(ids)]
    hist = s[(s.Transaction_Date >= hist_start) & (s.Transaction_Date < eval_start)].groupby("Customer_ID").is_h.agg(["sum", "size"])
    ev = s[(s.Transaction_Date >= eval_start) & (s.Transaction_Date <= eval_end)].copy()
    ev["p"] = ev.ym.map(pm_rows[3])
    e = ev.groupby("Customer_ID").agg(rows=("is_h", "size"), hs=("is_h", "sum"), logq=("p", lambda p: np.log1p(-p).sum()))
    e = e[e.rows >= 2].join(hist, how="inner")
    q_time = np.exp(e.logq)                                     # P(zero HSIC) if everyone shares the monthly rate
    q_fixed = (1 - e["sum"] / e["size"]) ** e.rows              # P(zero HSIC) if own history persisted
    obs = (e.hs == 0).mean()
    return {"window": f"{eval_start:%b %Y}-{eval_end:%b %Y}", "customers": len(e), "observed_zero_hsic": obs,
            "expected_time_adjusted": q_time.mean(), "se_time_adjusted": np.sqrt((q_time * (1 - q_time)).sum()) / len(e),
            "expected_fixed_history": q_fixed.mean(),
            "excess_vs_time_adjusted_pp": (obs - q_time.mean()) * 100,
            "excess_vs_fixed_history_pp": (obs - q_fixed.mean()) * 100}

M = pd.DateOffset
null = pd.DataFrame([zero_hsic_test(pd.Timestamp(h), pd.Timestamp(h) + M(months=6), pd.Timestamp(h) + M(months=12) - M(days=1))
                     for h in ["2024-08-01", "2025-02-01", "2025-08-01"]])
save(null, "05_silent_attrition_null_model", index=False)
num("null_model", null.round(4).to_dict("records"))

fig, ax = plt.subplots(figsize=(8, 4))
xx = np.arange(len(null))
for k, (col, lab, c_) in enumerate([("observed_zero_hsic", "Observed", S[0]),
                                    ("expected_time_adjusted", "Expected: same monthly rate for all", S[2]),
                                    ("expected_fixed_history", "Expected: own past usage persists", S[3])]):
    ax.bar(xx + (k - 1) * .27, null[col] * 100, .25, color=c_, label=lab)
ax.set_xticks(xx, null.window); ax.set_ylabel("% of active shoppers with zero HSIC use")
ax.set_title("'Silent' zero-HSIC customers are no more common than chance plus the portfolio trend predicts")
ax.legend(fontsize=8, loc="upper left")
fig_save(fig, "05_silent_attrition_null")

# ---------------------------------------------------------------- 6. explicit attrition: closures
cards = cust[cust.Credit_Card_Open_Date.notna()].copy()
qs = pd.period_range("2024Q3", "2026Q2", freq="Q")
haz = pd.DataFrame([{"quarter": str(p),
                     "open_at_start": ((cards.Credit_Card_Open_Date < p.start_time) & (cards.Credit_Card_Closed_Date.isna() | (cards.Credit_Card_Closed_Date >= p.start_time))).sum(),
                     "closed": cards.Credit_Card_Closed_Date.between(p.start_time, p.end_time).sum()} for p in qs])
haz["hazard"] = haz.closed / haz.open_at_start
save(haz, "06_closure_hazard_by_quarter", index=False)
num("closure_hazard_first_q", haz.hazard.iloc[0]); num("closure_hazard_last_q", haz.hazard.iloc[-1])
life = ((cards.Credit_Card_Closed_Date.fillna(DATA_END) - cards.Credit_Card_Open_Date).dt.days / 30.44)
cards["life"], cards["ev"] = life, cards.Credit_Card_Closed_Date.notna()
ten = pd.DataFrame([{"tenure": f"{lo}-{lo+5}m", "at_risk": (life >= lo).sum(),
                     "closed": ((life >= lo) & (life < lo + 6) & cards.ev).sum()} for lo in range(0, 54, 6)])
ten["hazard_6m"] = ten.closed / ten.at_risk
save(ten, "06_closure_hazard_by_tenure", index=False)
num("hazard_0_6m", ten.hazard_6m.iloc[0]); num("hazard_24_30m", ten.hazard_6m.iloc[4])
crate = {c_: cards.groupby(c_).ev.mean().round(3).to_dict() for c_ in ["Membership_Type", "Gender"]}
crate["age_band"] = cards.groupby(pd.cut(cards.Age, [17, 25, 35, 45, 60]), observed=True).ev.mean().round(3).values.tolist()
num("closure_rate_by_attr", crate)

# pre-closure usage vs same-month portfolio
cl = a[a.Credit_Card_Closed_Date.notna() & (a.Credit_Card_Closed_Date <= DATA_END)].copy()
cl["months_before"] = (cl.Credit_Card_Closed_Date.dt.to_period("M") - cl.ym).apply(lambda p: p.n).clip(upper=12)
cl["expected"] = cl.ym.map(pm_rows[3])
pre = cl.groupby("months_before").agg(observed=("is_h", "mean"), expected=("expected", "mean"), rows=("is_h", "size"))
pre["se"] = np.sqrt(pre.expected * (1 - pre.expected) / pre.rows)
save(pre, "06_pre_closure_hsic_share")
# post-closure shopping
closed_in = cards[cards.Credit_Card_Closed_Date.notna()]
post = t[t.Credit_Card_Closed_Date.notna() & (t.Transaction_Date > t.Credit_Card_Closed_Date)]
num("closed_cards", len(closed_in)); num("closed_still_shopping", post.Customer_ID.nunique())
num("closed_in_window", closed_in.Credit_Card_Closed_Date.between(DATA_START, DATA_END).sum())
num("post_close_net_fy26", post[post.FY == 2026].net.sum())
num("post_close_mix", post.groupby("Payment_Method").net.sum().div(post.net.sum()).round(3).to_dict())
# visit rate before vs after closure, for closures inside the window (per customer-month)
cw = closed_in[closed_in.Credit_Card_Closed_Date.between(DATA_START + M(months=3), DATA_END - M(months=3))]
tw = t[t.Customer_ID.isin(cw.Customer_ID)]
pre_m = ((cw.Credit_Card_Closed_Date - DATA_START).dt.days / 30.44).sum()
post_m = ((DATA_END - cw.Credit_Card_Closed_Date).dt.days / 30.44).sum()
num("rows_per_month_before_close", (tw.Transaction_Date <= tw.Credit_Card_Closed_Date).sum() / pre_m)
num("rows_per_month_after_close", (tw.Transaction_Date > tw.Credit_Card_Closed_Date).sum() / post_m)
num("rows_per_month_all_customers", len(t) / len(cust) / 24)

fig, axs = plt.subplots(1, 2, figsize=(11, 4))
axs[0].plot(haz.quarter, haz.hazard * 100, color=S[7], lw=2, marker="o")
axs[0].set_ylabel("% of open cards closed in quarter"); axs[0].set_title("Closure rate more than doubled in 2 years")
axs[0].tick_params(axis="x", rotation=45)
axs[1].bar(ten.tenure, ten.hazard_6m * 100, color=S[7])
axs[1].set_ylabel("% closing within the next 6 months"); axs[1].set_title("New cards close most often (first 6 months)")
axs[1].tick_params(axis="x", rotation=45)
fig_save(fig, "06_closure_hazard")

fig, ax = plt.subplots(figsize=(8, 4))
pp = pre.sort_index(ascending=False)
lbl = [f"-{i}" if 0 < i < 12 else ("≤-12" if i else "close month") for i in pp.index]
ax.fill_between(lbl, (pp.observed - 1.96 * pp.se) * 100, (pp.observed + 1.96 * pp.se) * 100, color=S[0], alpha=.15, lw=0)
ax.plot(lbl, pp.observed * 100, color=S[0], lw=2, marker="o", label="Customers who later close (95% band)")
ax.plot(lbl, pp.expected * 100, color=INK2, lw=1.5, ls="--", label="Portfolio, same calendar months")
ax.set_xlabel("Months before card closure"); ax.set_ylabel("HSIC share of rows (%)"); ax.legend()
ax.set_title("No early-warning signal: closers use HSIC like everyone else until they close")
fig_save(fig, "06_pre_closure_decay")

# closure prediction: time-split, behaviour + profile features
def snapshot(cut):
    cut = pd.Timestamp(cut); lo = cut - M(months=6)
    ids = cards[(cards.Credit_Card_Open_Date <= cut) & (cards.Credit_Card_Closed_Date.isna() | (cards.Credit_Card_Closed_Date > cut))]
    w = a[(a.Transaction_Date > lo) & (a.Transaction_Date <= cut)]
    g = w.groupby("Customer_ID").agg(rows6=("net", "size"), net6=("net", "sum"), hshare6=("is_h", "mean"))
    last = a[a.Transaction_Date <= cut].groupby("Customer_ID").Transaction_Date.max()
    lasth = a[(a.Transaction_Date <= cut) & a.is_h].groupby("Customer_ID").Transaction_Date.max()
    d = ids.set_index("Customer_ID")[["Age", "Credit_Card_Limit", "Credit_Card_APR", "Credit_Card_Open_Date", "Credit_Card_Closed_Date", "Membership_Type", "Gender"]].join(g)
    d["rows6"] = d.rows6.fillna(0); d["net6"] = d.net6.fillna(0); d["hshare6"] = d.hshare6.fillna(0)
    d["recency_m"] = ((cut - last.reindex(d.index)).dt.days / 30.44).fillna(36)
    d["hsic_recency_m"] = ((cut - lasth.reindex(d.index)).dt.days / 30.44).fillna(36)
    d["tenure_m"] = (cut - d.Credit_Card_Open_Date).dt.days / 30.44
    d["prime"] = (d.Membership_Type == "Prime").astype(int); d["male"] = (d.Gender == "Male").astype(int)
    d["y"] = (d.Credit_Card_Closed_Date <= cut + M(months=6)).astype(int)
    return d

FEAT = ["Age", "Credit_Card_Limit", "Credit_Card_APR", "tenure_m", "prime", "male", "rows6", "net6", "hshare6", "recency_m", "hsic_recency_m"]
tr, te = snapshot("2025-07-31"), snapshot("2026-01-31")
res = {}
for name, model, cols in [("tenure only (LR)", make_pipeline(StandardScaler(), LogisticRegression()), ["tenure_m"]),
                          ("behaviour only (LR)", make_pipeline(StandardScaler(), LogisticRegression()), ["rows6", "net6", "hshare6", "recency_m", "hsic_recency_m"]),
                          ("all features (LR)", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)), FEAT),
                          ("all features (GBM)", HistGradientBoostingClassifier(random_state=SEED, max_depth=3, learning_rate=.05, max_iter=200), FEAT)]:
    model.fit(tr[cols], tr.y)
    p = model.predict_proba(te[cols])[:, 1]
    top = te.y.values[np.argsort(-p)[:len(p) // 10]].mean()
    res[name] = {"test_auc": roc_auc_score(te.y, p), "test_pr_auc": average_precision_score(te.y, p), "top_decile_lift": top / te.y.mean()}
lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(tr[FEAT], tr.y)
coef = pd.Series(lr[-1].coef_[0], index=FEAT).sort_values()
save(pd.DataFrame(res).T, "06_closure_model_comparison")
save(coef.rename("std_coef"), "06_closure_lr_coefficients")
num("closure_models", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in res.items()})
num("closure_base_rate_test", te.y.mean())

# ---------------------------------------------------------------- 7. rewards
pc = a.groupby(["Membership_Type", "Category", "FY"])[["h", "net"]].sum()
pc["sow"] = pc.h / pc.net
save(pc, "07_sow_prime_by_category")
heat = pc.groupby(["Membership_Type", "Category"])[["h", "net"]].sum().pipe(lambda d: d.h / d.net).unstack(0)
# difference-in-differences: does the 5%/3% Prime rate lift HSIC use? customer bootstrap CI
a["boost_cat"] = a.Category_Code.isin([1, 2])
cb = a.groupby(["Customer_ID", "prime", "boost_cat"])[["h", "net"]].sum().unstack("boost_cat", fill_value=0).reset_index()
cb.columns = ["Customer_ID", "prime", "h_o", "h_b", "n_o", "n_b"]
def did(d):
    s = d.groupby("prime")[["h_o", "h_b", "n_o", "n_b"]].sum()
    return (s.h_b / s.n_b - s.h_o / s.n_o).diff().iloc[-1]   # (Prime: boost-other) - (NonPrime: boost-other)
rng = np.random.default_rng(SEED)
boots = [did(cb.iloc[rng.integers(0, len(cb), len(cb))]) for _ in range(300)]
num("prime_did_pp", did(cb) * 100); num("prime_did_ci_pp", list(np.percentile(boots, [2.5, 97.5]) * 100))
# money: rewards paid, and cashback customers forgo by paying another way ("left on the table")
a["forgone"] = np.where(a.is_h, 0, a.net * a.rate)
rw = a.groupby("FY").agg(rewards=("reward", "sum"), forgone=("forgone", "sum"), hsic=("h", "sum"))
save(rw, "07_rewards_by_fy")
num("rewards_fy25", rw.rewards[2025]); num("rewards_fy26", rw.rewards[2026]); num("forgone_fy26", rw.forgone[2026])
lot = a[a.FY == 2026].groupby(["Membership_Type", "Category"]).forgone.sum().unstack(0).sort_values("Prime", ascending=False)
save(lot, "07_forgone_cashback_fy26")
num("forgone_fy26_prime_grocery_electronics", lot.loc[["Grocery", "Electronics"], "Prime"].sum())
# reinforcement: does a reward credit (HSIC use last month) raise HSIC use this month?
cm = a.groupby(["Customer_ID", "ym"]).agg(hr=("is_h", "mean"), hn=("h", "sum")).reset_index()
nxt = cm.assign(ym=cm.ym - 1).rename(columns={"hr": "hr_next"})[["Customer_ID", "ym", "hr_next"]]
pair = cm.merge(nxt, on=["Customer_ID", "ym"])
pair["credited"] = pair.hn > 0
reinf = pair.groupby(["ym", "credited"]).hr_next.mean().unstack()
w = pair.groupby("ym").size()
num("reinforcement_diff_pp", ((reinf[True] - reinf[False]) * w).sum() / w.sum() * 100)
num("reinforcement_pairs", len(pair))

fig, ax = plt.subplots(figsize=(8, 4.5))
hm = heat.loc[cat.Category]
im = ax.imshow(hm.values * 100, cmap="Blues", vmin=15, vmax=30, aspect="auto")
ax.set_xticks([0, 1], ["Non-Prime (1% all)", "Prime (5% Grocery, 3% Electronics)"]); ax.set_yticks(range(len(hm)), hm.index)
for i in range(hm.shape[0]):
    for j in range(2):
        ax.text(j, i, f"{hm.values[i, j]:.1%}", ha="center", va="center", color=INK, fontsize=9)
ax.grid(False); fig.colorbar(im, ax=ax, label="HSIC SoW, FY25+FY26 (%)")
ax.set_title("Reward paradox: Prime's 5%/3% categories get no extra HSIC share")
fig_save(fig, "07_reward_paradox_heatmap")

# ---------------------------------------------------------------- 8. ticket size & big-ticket
bands = [0, 500, 1000, 2000, 4000, 8000, 9999.98, 10000]
labels = ["<500", "500-1k", "1-2k", "2-4k", "4-8k", "8-10k", "capped 9,999.99"]
a["ticket"] = pd.cut(a.Transaction_Amount, bands, labels=labels)
tk = a.groupby(["ticket", "Payment_Method"], observed=True).size().unstack()
tk = tk.div(tk.sum(1), axis=0)
save(tk, "08_method_mix_by_ticket")
num("hsic_share_small_ticket", tk.loc["<500", "HSIC Bank Credit Card"]); num("debit_share_small_ticket", tk.loc["<500", "Debit Card"])
num("wallet_share_capped", tk.loc["capped 9,999.99", "MetroMart Wallet"]); num("hsic_share_capped", tk.loc["capped 9,999.99", "HSIC Bank Credit Card"])
big = a[a.Category_Code.isin([2, 5, 7])]
num("big_ticket_cat_sow", sow(big))
num("ticket_median_by_method", a[~a.is_ret].groupby("Payment_Method").Transaction_Amount.median().round(0).to_dict())

fig, ax = plt.subplots(figsize=(9, 4))
left = np.zeros(len(tk))
for m_ in ["HSIC Bank Credit Card", "MetroMart Wallet", "Cash/UPI", "Debit Card", "Other Bank Credit Card"]:
    ax.barh(tk.index.astype(str), tk[m_] * 100, left=left, color=METHOD_COLOR[m_], label=m_, edgecolor="#fcfcfb", lw=1.5)
    left += tk[m_].values * 100
ax.invert_yaxis(); ax.set_xlabel("% of active cardholder rows"); ax.set_xlim(0, 100)
ax.legend(ncol=3, fontsize=8, loc="upper center", bbox_to_anchor=(.5, -.18)); ax.grid(axis="y", visible=False)
ax.set_title("Debit wins small baskets, Wallet wins big tickets; HSIC is weakest under ₹500")
fig_save(fig, "08_method_mix_by_ticket")

# ---------------------------------------------------------------- 9. SoW bridge FY25 -> FY26
cfy = a.groupby(["Customer_ID", "FY"]).net.sum().unstack()
stay = cfy[(cfy[2025] > 0) & (cfy[2026] > 0)].index
num("stayers", len(stay))
s_all25, s_all26 = sow(a[a.FY == 2025]), sow(a[a.FY == 2026])
st = a[a.Customer_ID.isin(stay)]
s_st25, s_st26 = sow(st[st.FY == 2025]), sow(st[st.FY == 2026])
bridge = pd.Series({"FY25 SoW": s_all25, "Leaver/closer effect": s_st25 - s_all25, "Stayer behaviour": s_st26 - s_st25,
                    "Joiner effect": s_all26 - s_st26, "FY26 SoW": s_all26})
assert np.isclose(bridge.iloc[0] + bridge.iloc[1:4].sum(), bridge.iloc[4])
save(bridge.rename("value"), "09_sow_bridge")
num("bridge", (bridge * 100).round(2).to_dict())
stm = fymix(st)
num("stayer_mix_change_pp", ((stm.loc[2026] - stm.loc[2025]) * 100).round(2).to_dict())

fig, ax = plt.subplots(figsize=(8, 4))
vals = bridge.values * 100; base = 0
for i, (k, v) in enumerate(zip(bridge.index, vals)):
    if i in (0, 4):
        ax.bar(i, v, color=S[0]); ax.text(i, v + .5, f"{v:.1f}%", ha="center", color=INK)
    else:
        ax.bar(i, v, bottom=base, color=S[7] if v < 0 else S[2]); ax.text(i, max(base, base + v) + .5, f"{v:+.2f}pp", ha="center", color=INK)
    base = v if i == 0 else base + v
ax.set_ylim(0, 34); ax.set_xticks(range(5), bridge.index, fontsize=9); ax.set_ylabel("HSIC SoW (%)")
ax.set_title("Almost all of the decline is existing cardholders changing how they pay")
fig_save(fig, "09_sow_bridge")

# ---------------------------------------------------------------- 10. customer-level table + segments
def assign_segments(asof):
    asof = pd.Timestamp(asof)
    lo12, lo6 = asof - M(months=12), asof - M(months=6)
    c = cust.set_index("Customer_ID").copy()
    w = t[t.Transaction_Date <= asof]
    w12 = w[w.Transaction_Date > lo12]
    aw = w[w.active]
    g12 = w12.groupby("Customer_ID").agg(rows12=("net", "size"), net12=("net", "sum"))
    ga12 = w12[w12.active].groupby("Customer_ID").agg(arows12=("net", "size"), anet12=("net", "sum"), ah12=("h", "sum"))
    g6 = w[w.Transaction_Date > lo6].groupby("Customer_ID").agg(rows6=("net", "size"))
    gh6 = w[(w.Transaction_Date > lo6) & w.is_h].groupby("Customer_ID").size().rename("hrows6")
    gaw = aw.assign(lq=np.log1p(-aw.ym.map(pm_rows[3]))).groupby("Customer_ID").agg(arows=("net", "size"), hrows=("is_h", "sum"), log_p_zero=("lq", "sum"))
    post_ = w[w.Credit_Card_Closed_Date.notna() & (w.Transaction_Date > w.Credit_Card_Closed_Date) & (w.Transaction_Date > lo12)].groupby("Customer_ID").net.agg(["size", "sum"])
    post_.columns = ["post_rows12", "post_net12"]
    # declining flag: last 6m vs the 12 months before that, each with >=2 active rows
    prev = aw[(aw.Transaction_Date > asof - M(months=18)) & (aw.Transaction_Date <= lo6)].groupby("Customer_ID").agg(pn=("net", "sum"), ph=("h", "sum"), pr=("net", "size"))
    rec = aw[aw.Transaction_Date > lo6].groupby("Customer_ID").agg(rn=("net", "sum"), rh=("h", "sum"), rr=("net", "size"))
    c = c.join([g12, ga12, g6, gh6, gaw, post_, prev, rec]).fillna({k: 0 for k in ["rows12", "net12", "arows12", "anet12", "ah12", "rows6", "hrows6", "arows", "hrows", "log_p_zero", "post_rows12", "post_net12", "pr", "rr"]})
    c["sow12"] = np.where(c.anet12 > 0, c.ah12 / c.anet12, np.nan)
    c["declining"] = (c.pr >= 2) & (c.rr >= 2) & (c.pn > 0) & (c.rn > 0) & ((c.ph / c.pn - c.rh / c.rn) >= LOW_SOW)
    # chance of zero HSIC over the whole active window if this customer used HSIC like the portfolio did each month
    c["p_zero_hsic_by_chance"] = np.exp(c.log_p_zero)
    c["tenure_m"] = (asof - c.Credit_Card_Open_Date).dt.days / 30.44
    closed = c.Credit_Card_Closed_Date.notna() & (c.Credit_Card_Closed_Date <= asof)
    card = c.Credit_Card_Open_Date.notna() & (c.Credit_Card_Open_Date <= asof)
    spend = c.net12.where(c.net12 > 0, 0)
    c["value_tier"] = pd.qcut(spend.rank(method="first"), 3, labels=["Low value", "Mid value", "High value"])
    low = (c.sow12 < LOW_SOW) | c.sow12.isna()
    conds = [~card, closed & (c.post_rows12 > 0), closed, c.tenure_m < 6, c.rows6 == 0,
             low & (c.value_tier != "Low value"), low]
    names = ["No card (acquisition pool)", "Closed - still shopping (win-back)", "Closed - gone", "New card (<6m, onboarding)",
             "Dormant (card open, no visits 6m)", "High-potential low-SoW", "Low-value low-SoW"]
    c["segment"] = np.select(conds, names, "Engaged core (SoW >=15%)")
    c["sow_state"] = np.select([~card | closed, c.hrows6.eq(0) & c.rows6.gt(0), low], ["n/a", "zero HSIC 6m", "low"], "engaged")
    return c

ORDER = ["Engaged core (SoW >=15%)", "High-potential low-SoW", "Low-value low-SoW", "Dormant (card open, no visits 6m)",
         "New card (<6m, onboarding)", "Closed - still shopping (win-back)", "Closed - gone", "No card (acquisition pool)"]
now = assign_segments(DATA_END)
fwd_seg = assign_segments("2026-01-31")
# forward outcomes Feb-Jul 2026 for the 2026-01-31 segments (backtest: do segments predict anything?)
fw = t[t.Transaction_Date > pd.Timestamp("2026-01-31")]
fo = fw.groupby("Customer_ID").agg(f_net=("net", "sum"), f_rows=("net", "size"))
fa = fw[fw.active].groupby("Customer_ID").agg(f_anet=("net", "sum"), f_ah=("h", "sum"))
fwd_seg = fwd_seg.join([fo, fa]).fillna({"f_net": 0, "f_rows": 0, "f_anet": 0, "f_ah": 0})
fwd_seg["f_closed"] = fwd_seg.Credit_Card_Closed_Date.between(pd.Timestamp("2026-02-01"), DATA_END)
bt = fwd_seg.groupby("segment").agg(customers=("f_net", "size"), fwd_net_per_cust=("f_net", "mean"), fwd_shopping=("f_rows", lambda r: (r > 0).mean()),
                                    fwd_closure_rate=("f_closed", "mean"), f_ah=("f_ah", "sum"), f_anet=("f_anet", "sum"))
bt["fwd_sow"] = bt.f_ah / bt.f_anet
bt = bt.drop(columns=["f_ah", "f_anet"]).reindex(ORDER)
save(bt, "10_segment_backtest_2026-01-31")
# same backtest for single tags: does the label predict forward SoW / spend?
openc = fwd_seg[fwd_seg.segment.isin(ORDER[:3])]
tag_bt = pd.concat({col: openc.groupby(col, observed=True).agg(customers=("f_net", "size"), fwd_net_per_cust=("f_net", "mean"),
                                                               f_ah=("f_ah", "sum"), f_anet=("f_anet", "sum"))
                    for col in ["value_tier", "sow_state", "declining", "Membership_Type"]})
tag_bt["fwd_sow"] = tag_bt.f_ah / tag_bt.f_anet
save(tag_bt.drop(columns=["f_ah", "f_anet"]), "10_tag_backtest_2026-01-31")
num("tag_backtest", tag_bt.drop(columns=["f_ah", "f_anet"]).round(4).reset_index().astype(str).to_dict("records"))
# individually provable silent attriters: zero HSIC although chance of that is <5%; compare with chance
op = now[now.segment.isin(ORDER[:4]) & (now.arows > 0)]
sig = op[op.p_zero_hsic_by_chance < .05]
num("customers_with_enough_rows_to_test", len(sig))
num("confident_zero_hsic_observed", int((sig.hrows == 0).sum()))
num("confident_zero_hsic_expected_by_chance", sig.p_zero_hsic_by_chance.sum())
num("min_rows_to_prove_silence", int(np.ceil(np.log(.05) / np.log(1 - mon.row_share.iloc[-6:].mean()))))
num("median_active_rows_per_open_card_6m", now.loc[now.segment.isin(ORDER[:3]), "rows6"].median())

seg = now.groupby("segment").agg(customers=("net12", "size"), prime_share=("Membership_Type", lambda s: (s == "Prime").mean()),
                                 net12_total=("net12", "sum"), active_net12=("anet12", "sum"), hsic_net12=("ah12", "sum"),
                                 post_close_net12=("post_net12", "sum"), median_tenure_m=("tenure_m", "median"), avg_age=("Age", "mean"))
seg["sow12"] = seg.hsic_net12 / seg.active_net12
seg["non_hsic_net12"] = seg.net12_total - seg.hsic_net12          # spend HSIC could still win
seg["share_of_customers"] = seg.customers / seg.customers.sum()
seg = seg.reindex(ORDER)
save(seg, "10_segment_summary_2026-07-31")
xt = pd.crosstab(now.segment, now.value_tier).reindex(ORDER)
save(xt, "10_segment_by_value_tier")
vt = now[now.segment.isin(ORDER[:5])].groupby("value_tier", observed=True).agg(customers=("net12", "size"), net12=("net12", "sum"), ah12=("ah12", "sum"))
vt["share_of_non_hsic_spend"] = (vt.net12 - vt.ah12) / (vt.net12 - vt.ah12).sum()
save(vt, "10_value_tier_concentration")
num("segments_now", seg.customers.to_dict())
num("high_value_share_of_open_card_non_hsic_spend", vt.share_of_non_hsic_spend.get("High value"))

# K-means on behaviour at 2026-01-31: does a data-driven method find low-SoW groups that persist?
km = fwd_seg[fwd_seg.segment.isin(ORDER[:3])].copy()
km["prime"] = (km.Membership_Type == "Prime").astype(int)
kf = ["rows12", "anet12", "sow12", "tenure_m", "Age", "Credit_Card_Limit", "prime"]
X = StandardScaler().fit_transform(km[kf].fillna(0).assign(anet12=lambda d: np.log1p(d.anet12.clip(lower=0))))
sil = {k: silhouette_score(X, KMeans(k, n_init=10, random_state=SEED).fit_predict(X), sample_size=5000, random_state=SEED) for k in range(3, 8)}
k_best = max(sil, key=sil.get)
km["cluster"] = KMeans(k_best, n_init=10, random_state=SEED).fit_predict(X)
kc = km.groupby("cluster").agg(customers=("rows12", "size"), rows12=("rows12", "mean"), anet12=("anet12", "mean"), prime=("prime", "mean"),
                               tenure_m=("tenure_m", "mean"), h=("ah12", "sum"), n=("anet12", "sum"), f_ah=("f_ah", "sum"), f_anet=("f_anet", "sum"),
                               fwd_net_per_cust=("f_net", "mean"))
kc["sow12_in_sample"] = kc.h / kc.n; kc["fwd_sow"] = kc.f_ah / kc.f_anet
save(kc.drop(columns=["h", "n", "f_ah", "f_anet"]), "10_kmeans_clusters_backtest")
num("kmeans_k", k_best); num("kmeans_silhouette", {k: round(v, 3) for k, v in sil.items()})
num("kmeans_fwd_sow_range", [kc.fwd_sow.min(), kc.fwd_sow.max()]); num("kmeans_insample_sow_range", [kc.sow12_in_sample.min(), kc.sow12_in_sample.max()])
num("backtest", bt.round(4).reset_index().to_dict("records"))

fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
b2 = bt.dropna(subset=["fwd_sow"]).drop(index="No card (acquisition pool)", errors="ignore")
axs[0].barh(b2.index, b2.fwd_sow * 100, color=S[0]); axs[0].set_xlabel("Forward HSIC SoW, Feb-Jul 2026 (%)")
axs[0].set_title("Forward SoW: segments barely differ")
axs[1].barh(b2.index, b2.fwd_net_per_cust, color=S[2]); axs[1].set_xlabel("Forward MetroMart net spend per customer (₹)")
axs[1].set_title("Forward spend: segments differ a lot")
axs[0].invert_yaxis()
for ax_, col, fmt in [(axs[0], "fwd_sow", "{:.0%}"), (axs[1], "fwd_net_per_cust", "₹{:,.0f}")]:
    for i, v in enumerate(b2[col]):
        ax_.text(v * (100 if col == "fwd_sow" else 1), i, " " + fmt.format(v), va="center", fontsize=8, color=INK)
fig.suptitle("Backtest: segments defined at 31 Jan 2026, outcomes measured Feb-Jul 2026", color=INK, fontweight="bold")
fig_save(fig, "10_segment_backtest")

# customer-level output
cust_out = now[["Age", "Gender", "Membership_Type", "Credit_Card_Open_Date", "Credit_Card_Closed_Date", "Credit_Card_Limit", "Credit_Card_APR",
                "segment", "value_tier", "sow_state", "declining", "p_zero_hsic_by_chance", "rows12", "net12", "anet12", "ah12", "sow12", "rows6", "hrows6", "post_net12", "tenure_m"]].copy()
cy = a.groupby(["Customer_ID", "FY"])[["h", "net"]].sum().unstack()
for y in (2025, 2026):
    cust_out[f"active_net_fy{y%100}"] = cy[("net", y)]
    cust_out[f"hsic_net_fy{y%100}"] = cy[("h", y)]
    cust_out[f"sow_fy{y%100}"] = cy[("h", y)] / cy[("net", y)].where(cy[("net", y)] > 0)   # undefined if net <= 0
cust_out["forgone_cashback_fy26"] = a[a.FY == 2026].groupby("Customer_ID").forgone.sum().reindex(cust_out.index).fillna(0)
cust_out["sow_shrunk_fy26"] = p0 + (between_var / (between_var + p0 * (1 - p0) / cust_out.rows12.clip(lower=1))) * (cust_out.sow_fy26.fillna(p0) - p0)
cust_out.to_csv(OUT / "customer_sow_segments.csv")

# ---------------------------------------------------------------- 11. seasonality (campaign timing)
seas = t.groupby(t.Transaction_Date.dt.month).net.sum() / 2
save(seas.rename("avg_net_per_calendar_month"), "11_seasonality")
cat_mix = a.groupby("Category").net.sum().div(a.net.sum()).sort_values(ascending=False)
save(cat_mix.rename("share_active_net"), "11_category_mix")
num("category_mix", cat_mix.round(3).to_dict())
num("return_rate_rows", t.is_ret.mean())

(OUT / "eda_numbers.json").write_text(json.dumps(NUM, indent=2, default=str))
print(json.dumps(NUM, indent=1, default=str))
