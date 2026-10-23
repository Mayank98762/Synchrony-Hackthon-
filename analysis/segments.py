"""Who to prioritise (selection_log.md §6): K-means negative control, then the frequency × card-age 2×2.

Boxes are built at 2026-01-31, outcomes measured over Feb-Jul 2026, and production assignment is
done at 2026-07-31. Only aggregates are written: the repo is public.

    python -m analysis.segments
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from analysis import config as C, prep
from analysis.experiments_ml import customer_sow_by_fy

TABLES = C.OUTPUTS / "tables"
GRID = ["B", "C", "D", "E"]
NAMES = {"A": "Closed, still shopping", "B": "Protect first", "C": "Activate", "D": "Grow", "E": "Nudge",
         "F": "Non-cardholder", "Z": "Unassigned"}


# ---------------------------------------------------------------- K-means negative control
def kmeans_features():
    """FY25 ₹ SoW, FY25 HSIC row share, and its H1 -> H2 change, for customers passing the SoW filter."""
    d = prep.load()
    act = prep.active(d.txn)
    sow = customer_sow_by_fy(act)
    fy25 = act[(act.fy == C.FISCAL_YEARS[0]) & act.customer_id.isin(sow.index)]
    share = fy25.groupby("customer_id").is_hsic.mean()
    by_half = fy25.groupby(["customer_id", "half"]).is_hsic.mean().unstack()
    X = pd.DataFrame({"sow_fy25": sow[C.FISCAL_YEARS[0]], "row_share_fy25": share,
                      "half_change": (by_half["H2"] - by_half["H1"]).fillna(0)}).dropna()
    return X, sow.loc[X.index, C.FISCAL_YEARS[1]]


def eta_squared(labels, y):
    grand = y.mean()
    between = sum(len(g) * (g.mean() - grand) ** 2 for _, g in y.groupby(labels))
    return float(between / ((y - grand) ** 2).sum())


def kmeans_control():
    X, sow_next = kmeans_features()
    Z = StandardScaler().fit_transform(X)
    rng = np.random.default_rng(C.SEED)

    sil = {}
    for k in C.KMEANS_K_RANGE:
        labels = KMeans(k, n_init=C.KMEANS_N_INIT, random_state=C.SEED).fit_predict(Z)
        sil[k] = silhouette_score(Z, labels, sample_size=5000, random_state=C.SEED)
    k = max(sil, key=sil.get)
    model = KMeans(k, n_init=C.KMEANS_N_INIT, random_state=C.SEED).fit(Z)
    labels = model.labels_

    aris = []
    for _ in range(C.KMEANS_STABILITY_RESAMPLES):
        idx = rng.integers(0, len(Z), len(Z))
        refit = KMeans(k, n_init=C.KMEANS_N_INIT, random_state=C.SEED).fit(Z[idx])
        aris.append(adjusted_rand_score(labels, refit.predict(Z)))

    y = sow_next.reset_index(drop=True)
    lab = pd.Series(labels)
    eta = eta_squared(lab, y)
    boot = []
    for _ in range(C.BOOTSTRAP_N):
        idx = rng.integers(0, len(y), len(y))
        boot.append(eta_squared(lab.iloc[idx].reset_index(drop=True), y.iloc[idx].reset_index(drop=True)))
    lo, hi = np.percentile(boot, [2.5, 97.5])

    clusters = X.assign(cluster=labels, sow_fy26=sow_next.values).groupby("cluster").agg(
        customers=("sow_fy25", "size"), sow_fy25=("sow_fy25", "mean"), sow_fy26=("sow_fy26", "mean"))
    TABLES.mkdir(parents=True, exist_ok=True)
    clusters.to_csv(TABLES / "segments_kmeans_clusters.csv")
    pd.Series(sil, name="silhouette").rename_axis("k").to_csv(TABLES / "segments_kmeans_silhouette.csv")

    real = np.mean(aris) >= C.KMEANS_ARI_MIN and lo >= C.KMEANS_ETA2_MIN
    return {
        "seg_kmeans_customers": int(len(X)), "seg_kmeans_k": int(k), "seg_kmeans_silhouette": float(sil[k]),
        "seg_kmeans_ari": float(np.mean(aris)), "seg_kmeans_eta2": eta,
        "seg_kmeans_eta2_lo": float(lo), "seg_kmeans_eta2_hi": float(hi),
        "seg_kmeans_fy25_sow_spread_pp": float((clusters.sow_fy25.max() - clusters.sow_fy25.min()) * 100),
        "seg_kmeans_fy26_sow_spread_pp": float((clusters.sow_fy26.max() - clusters.sow_fy26.min()) * 100),
        "seg_kmeans_verdict": "real structure" if real else "clusters do not predict next year's SoW",
    }


# ---------------------------------------------------------------- the 2×2 and segments A-F
def assign(cutoff, freq_scale=1.0, young_years=C.YOUNG_CARD_YEARS):
    """Segment letter per customer at a cutoff (first match wins: A, B, C, D, E, F, else Z).

    freq_scale / young_years shift the two cuts for the boundary-sensitivity check.
    Returns the customer table with `segment`, `is_young_seg`, `high_freq`, plus the frequency cut used.
    """
    d = prep.load()
    cust = d.cust.copy()
    tx = d.txn

    closed = cust.close_date.notna() & (cust.close_date <= cutoff)
    post = tx[tx.close_date.notna() & (tx.date > tx.close_date) & (tx.date <= cutoff)]
    post_net = post.groupby("customer_id").net.sum()
    shopping_after = cust.customer_id.map(post_net).fillna(0) > 0

    is_open = prep.open_at(cust, cutoff)
    age = prep.card_age_years(cust, cutoff)
    freq = cust.customer_id.map(prep.purchase_frequency(tx, cutoff)).fillna(0)
    cut = freq[is_open].quantile(C.FREQ_TOP_QUANTILE) * freq_scale
    high = freq > cut
    young = age < young_years

    cust["segment"] = np.select(
        [closed & shopping_after, is_open & young & high, is_open & young & ~high,
         is_open & ~young & high, is_open & ~young & ~high, ~cust.has_card],
        ["A", "B", "C", "D", "E", "F"], "Z")
    cust["is_young_seg"], cust["high_freq"], cust["is_open"] = young, high, is_open
    assert len(cust) == C.EXPECTED_ROWS["customers"] and cust.segment.notna().all()
    return cust, float(cut)


def _boot_ratio(num, den, n=C.BOOTSTRAP_N, rng=None):
    idx = rng.integers(0, len(num), (n, len(num)))
    r = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    return tuple(map(float, np.percentile(r, [2.5, 97.5])))


def _boot_mean(x, n=C.BOOTSTRAP_N, rng=None):
    idx = rng.integers(0, len(x), (n, len(x)))
    return tuple(map(float, np.percentile(x[idx].mean(axis=1), [2.5, 97.5])))


def _boot_diff(a, b, n=C.BOOTSTRAP_N, rng=None):
    da = a[rng.integers(0, len(a), (n, len(a)))].mean(axis=1)
    db = b[rng.integers(0, len(b), (n, len(b)))].mean(axis=1)
    return float(a.mean() - b.mean()), *map(float, np.percentile(da - db, [2.5, 97.5]))


def outcomes(cust, cutoff):
    """Per-customer outcomes over the 6-month horizon after the cutoff."""
    d = prep.load()
    h0, h1 = prep.horizon(cutoff)
    act = prep.active(d.txn)
    act = act[prep.in_window(act.date, h0, h1)]
    g = act.groupby("customer_id")
    o = pd.DataFrame({"net": g.net.sum(), "rows": g.size(), "hsic_rows": g.is_hsic.sum()})
    o["hsic_net"] = act[act.is_hsic].groupby("customer_id").net.sum().reindex(o.index).fillna(0)
    out = cust.merge(o, left_on="customer_id", right_index=True, how="left").fillna(
        {"net": 0, "rows": 0, "hsic_rows": 0, "hsic_net": 0})
    out["nonhsic_net"] = out.net - out.hsic_net
    out["closed_6m"] = prep.closed_in(out, h0, h1).astype(float)
    return out


def box_table(o):
    rng = np.random.default_rng(C.SEED)
    rows = []
    for s in GRID:
        b = o[o.segment == s]
        hs, tot = b.hsic_net.to_numpy(), b.net.to_numpy()
        cl, nh = b.closed_6m.to_numpy(), b.nonhsic_net.to_numpy()
        rows.append({
            "segment": s, "name": NAMES[s], "customers": len(b),
            "sow": hs.sum() / tot.sum(), **dict(zip(["sow_lo", "sow_hi"], _boot_ratio(hs, tot, rng=rng))),
            "closure_6m": cl.mean(), **dict(zip(["closure_lo", "closure_hi"], _boot_mean(cl, rng=rng))),
            "nonhsic_per_cust": nh.mean(), **dict(zip(["nonhsic_lo", "nonhsic_hi"], _boot_mean(nh, rng=rng))),
            "prime_share": b.is_prime.mean(),
            "p_hsic": b.hsic_rows.sum() / b.rows.sum(),
            "rows_3m": b.rows.sum() / len(b) / 2,
        })
    return pd.DataFrame(rows).set_index("segment")


def run():
    out = kmeans_control()
    rng = np.random.default_rng(C.SEED)

    # Build at the test cutoff, measure Feb-Jul 2026.
    cust, cut = assign(C.CUTOFF_TEST)
    open_cards = cust[cust.is_open]
    young_top, mature_top = open_cards[open_cards.is_young_seg].high_freq.mean(), open_cards[~open_cards.is_young_seg].high_freq.mean()
    gap = abs(young_top - mature_top)
    assert gap <= C.FREQ_INDEPENDENCE_TOL, f"2x2 axes not independent: {gap:.3f}"

    o = outcomes(cust, C.CUTOFF_TEST)
    table = box_table(o)
    grid = o[o.segment.isin(GRID)]

    sows = table.sow.to_numpy()
    sow_gap = float(sows.max() - sows.min())
    age_diff = _boot_diff(grid[grid.is_young_seg].closed_6m.to_numpy(), grid[~grid.is_young_seg].closed_6m.to_numpy(), rng=rng)
    freq_diff = _boot_diff(grid[grid.high_freq].nonhsic_net.to_numpy(), grid[~grid.high_freq].nonhsic_net.to_numpy(), rng=rng)
    age_bin = prep.card_age_bin(grid, C.CUTOFF_TEST)
    young = grid[grid.is_young_seg]
    split = _boot_diff(young[age_bin[young.index] == "<6m"].closed_6m.to_numpy(),
                       young[age_bin[young.index] == "6-12m"].closed_6m.to_numpy(), rng=rng)
    split_reported = split[1] > 0 or split[2] < 0
    if split_reported:
        sub = young.assign(age_bin=age_bin[young.index].astype(str)).groupby(["segment", "age_bin"]).agg(
            customers=("closed_6m", "size"), closure_6m=("closed_6m", "mean"), nonhsic_per_cust=("nonhsic_net", "mean"))
        sub.to_csv(TABLES / "segments_young_split.csv")

    # Segment A outcomes in the horizon: MetroMart spend after closure, all methods.
    a_ids = cust.loc[cust.segment == "A", "customer_id"]
    d = prep.load()
    h0, h1 = prep.horizon(C.CUTOFF_TEST)
    a_spend = d.txn[d.txn.customer_id.isin(a_ids) & prep.in_window(d.txn.date, h0, h1)].net.sum()

    # Boundary sensitivity: share of open cards that change box when a cut moves.
    base = cust.set_index("customer_id").segment
    boundary = {}
    for label, kw in {"freq_minus10": {"freq_scale": 1 - C.BOUNDARY_SHIFT}, "freq_plus10": {"freq_scale": 1 + C.BOUNDARY_SHIFT},
                      "young_0_9y": {"young_years": 1 - C.BOUNDARY_SHIFT}, "young_1_1y": {"young_years": 1 + C.BOUNDARY_SHIFT}}.items():
        moved, _ = assign(C.CUTOFF_TEST, **kw)
        m = moved.set_index("customer_id").segment
        in_grid = base.isin(GRID)
        boundary[label] = float((m[in_grid] != base[in_grid]).mean())

    # Production assignment at the score cutoff: sizes only.
    score, score_cut = assign(C.CUTOFF_SCORE)
    sizes_score = score.segment.value_counts().reindex(list(NAMES), fill_value=0)
    a_score = score.loc[score.segment == "A", "customer_id"]
    post_all = d.txn[d.txn.customer_id.isin(a_score) & (d.txn.date > d.txn.close_date)].net.sum()

    TABLES.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLES / "segments_box_table.csv")
    cust.segment.value_counts().reindex(list(NAMES), fill_value=0).rename("customers").rename_axis("segment").to_frame().assign(
        customers_at_score=sizes_score.values, name=[NAMES[s] for s in NAMES]).to_csv(TABLES / "segments_sizes.csv")
    pd.Series(boundary, name="share_changing_box").rename_axis("shift").to_csv(TABLES / "segments_boundary.csv")

    out.update({
        "seg_build_cutoff": str(C.CUTOFF_TEST.date()), "seg_freq_cut": cut, "seg_freq_cut_score": score_cut,
        "seg_young_top_share": float(young_top), "seg_mature_top_share": float(mature_top), "seg_independence_gap": float(gap),
        "seg_sow_max_gap_pp": sow_gap * 100,
        "seg_sow_separates": bool(sow_gap > C.SOW_SAME_TOL),
        "seg_age_closure_diff": age_diff[0], "seg_age_closure_diff_lo": age_diff[1], "seg_age_closure_diff_hi": age_diff[2],
        "seg_age_separates_risk": bool(age_diff[1] > 0),
        "seg_freq_nonhsic_diff": freq_diff[0], "seg_freq_nonhsic_diff_lo": freq_diff[1], "seg_freq_nonhsic_diff_hi": freq_diff[2],
        "seg_freq_separates_value": bool(freq_diff[1] > 0),
        "seg_young_split_diff": split[0], "seg_young_split_lo": split[1], "seg_young_split_hi": split[2],
        "seg_young_split_reported": bool(split_reported),
        "seg_A_n": int(len(a_ids)), "seg_A_horizon_net": float(a_spend), "seg_A_horizon_net_per_cust": float(a_spend / len(a_ids)),
        "seg_A_n_score": int(len(a_score)), "seg_A_post_close_net": float(post_all),
        "seg_F_n": int((cust.segment == "F").sum()), "seg_Z_n": int((cust.segment == "Z").sum()),
    })
    for k, v in boundary.items():
        out[f"seg_boundary_{k}"] = v
    for s, r in table.iterrows():
        for col in ["customers", "sow", "sow_lo", "sow_hi", "closure_6m", "closure_lo", "closure_hi",
                    "nonhsic_per_cust", "nonhsic_lo", "nonhsic_hi", "prime_share", "p_hsic", "rows_3m"]:
            key = "n" if col == "customers" else col
            out[f"seg_{s}_{key}"] = int(r[col]) if col == "customers" else float(r[col])
    for s, n in sizes_score.items():
        out[f"seg_{s}_n_score"] = int(n)
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:34s} {v:.4f}" if isinstance(v, float) else f"{k:34s} {v}")
    print(pd.read_csv(TABLES / "segments_box_table.csv").round(3).to_string(index=False))
