"""Closure early warning (selection_log.md §5): baselines vs learned models, out of time.

Train on the 2025-07-31 snapshot, test once on 2026-01-31, score 2026-07-31. The learned model
ships only if it beats the card-age rule (B2) on test ROC-AUC with a bootstrap CI above 0.
Also produces X5 (does usage predict closure?) and X6 (HGB vs LR).

    python -m analysis.closure_model
"""
from itertools import product

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from analysis import config as C, prep

PROFILE = ["card_age_years", "is_prime", "age", "credit_limit", "apr"]
USAGE = ["rows", "hs_rows", "hs_share", "hs_net_share", "m_since_hsic", "m_since_txn", "d_share", "log_net"]
FEATURE_SETS = {"LR-profile": PROFILE, "LR-usage": USAGE, "LR-all": PROFILE + USAGE}
INTERPRETABILITY = ["LR-all", "HGB"]          # selection_log §5: most interpretable first

TABLES = C.OUTPUTS / "tables"


# ---------------------------------------------------------------- snapshot
def _months(delta):
    return delta.dt.days / 30


def build_snapshot(cutoff):
    """One row per card open at the cutoff: usage from the 12-month lookback, profile, 6-month closure label."""
    d = prep.load()
    u = prep.snapshot_universe(cutoff)
    start, end = prep.lookback(cutoff)
    mid = prep.months_after(cutoff, -C.HORIZON_MONTHS)
    tx = d.txn[d.txn.customer_id.isin(u.customer_id) & prep.in_window(d.txn.date, start, end)]
    assert tx.date.max() <= cutoff, "feature row dated after the cutoff"

    g = tx.groupby("customer_id")
    f = pd.DataFrame({"rows": g.size(), "hs_rows": g.is_hsic.sum(), "net": g.net.sum(), "last": g.date.max()})
    f["hs_net"] = tx[tx.is_hsic].groupby("customer_id").net.sum().reindex(f.index).fillna(0)
    f["last_hsic"] = tx[tx.is_hsic].groupby("customer_id").date.max().reindex(f.index)
    recent = tx[tx.date > mid].groupby("customer_id").is_hsic.mean()
    earlier = tx[tx.date <= mid].groupby("customer_id").is_hsic.mean()

    u = u.merge(f, left_on="customer_id", right_index=True, how="left")
    u["rows"] = u.rows.fillna(0)
    u["hs_rows"] = u.hs_rows.fillna(0)
    u["hs_share"] = (u.hs_rows / u.rows).where(u.rows > 0, 0.0)
    u["hs_net_share"] = (u.hs_net / u.net).where(u.net > 0, 0.0).fillna(0.0)
    u["m_since_hsic"] = _months(cutoff - u.last_hsic).fillna(C.MONTHS_SINCE_NONE)
    u["m_since_txn"] = _months(cutoff - u["last"]).fillna(C.MONTHS_SINCE_NONE)
    u["d_share"] = (u.customer_id.map(recent) - u.customer_id.map(earlier)).fillna(0.0)
    u["log_net"] = np.log1p(u.net.fillna(0).clip(lower=0))
    u["is_prime"] = u.is_prime.astype(int)

    if cutoff < C.DATA_END:
        closers = u.loc[u.closed_6m.astype(bool), "close_date"]
        assert closers.min() > cutoff, "label dated on or before the cutoff"
        u["y"] = u.closed_6m.astype(int)
    return u.drop(columns=["net", "hs_net", "last", "last_hsic"])


# ---------------------------------------------------------------- models and metrics
def _lr():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))


def _hgb(**params):
    return HistGradientBoostingClassifier(max_iter=C.HGB_MAX_ITER, class_weight="balanced", random_state=C.SEED, **params)


def top_decile_capture(y, score):
    k = int(len(score) * 0.1)
    top = np.argsort(-score, kind="stable")[:k]
    return float(y[top].sum() / y.sum())


def metrics(y, score):
    return {"roc_auc": float(roc_auc_score(y, score)), "pr_auc": float(average_precision_score(y, score)),
            "top_decile_capture": top_decile_capture(y, score)}


def paired_bootstrap(y, score_a, score_b, n=C.BOOTSTRAP_N):
    """95% CI of ROC-AUC(a) − ROC-AUC(b), resampling cards with replacement."""
    rng = np.random.default_rng(C.SEED)
    diffs = np.empty(n)
    for i in range(n):
        idx = rng.integers(0, len(y), len(y))
        diffs[i] = roc_auc_score(y[idx], score_a[idx]) - roc_auc_score(y[idx], score_b[idx])
    return float(roc_auc_score(y, score_a) - roc_auc_score(y, score_b)), *map(float, np.percentile(diffs, [2.5, 97.5]))


def bootstrap_auc(y, score, n=C.BOOTSTRAP_N):
    rng = np.random.default_rng(C.SEED)
    aucs = [roc_auc_score(y[idx], score[idx]) for idx in (rng.integers(0, len(y), len(y)) for _ in range(n))]
    return tuple(map(float, np.percentile(aucs, [2.5, 97.5])))


def tune_hgb(X, y, folds):
    """Small grid on the training snapshot only, scored by CV PR-AUC."""
    best = None
    for values in product(*C.HGB_GRID.values()):
        params = dict(zip(C.HGB_GRID, values))
        s = cross_val_score(_hgb(**params), X, y, cv=folds, scoring="average_precision")
        if best is None or s.mean() > best[1].mean():
            best = (params, s)
    return best


def lr_odds_ratios(train):
    """Unweighted logistic regression on standardised features, for odds ratios with 95% CIs."""
    cols = PROFILE + USAGE
    X = (train[cols] - train[cols].mean()) / train[cols].std()
    fit = sm.Logit(train.y.to_numpy(), sm.add_constant(X)).fit(disp=0)
    ci = fit.conf_int()
    return pd.DataFrame({"coef_std": fit.params, "odds_ratio": np.exp(fit.params),
                         "or_ci_lo": np.exp(ci[0]), "or_ci_hi": np.exp(ci[1]), "p_value": fit.pvalues}).drop(index="const")


def gain_table(y, score, bins=10):
    """Closure rate by score decile (decile 1 = highest risk), for the slide 8 chart."""
    order = pd.Series(score).rank(method="first", ascending=False)
    decile = np.ceil(order / len(order) * bins).astype(int)
    t = pd.DataFrame({"decile": decile, "y": y}).groupby("decile").y.agg(cards="size", closers="sum", closure_rate="mean")
    t["cum_capture"] = t.closers.cumsum() / t.closers.sum()
    return t


# ---------------------------------------------------------------- the experiment
def run():
    train, test = build_snapshot(C.CUTOFF_TRAIN), build_snapshot(C.CUTOFF_TEST)
    y_tr, y_te = train.y.to_numpy(), test.y.to_numpy()
    folds = StratifiedKFold(C.CV_FOLDS, shuffle=True, random_state=C.SEED)
    all_cols = PROFILE + USAGE

    # Cross-validation on the training snapshot only.
    cv = {name: cross_val_score(_lr(), train[cols], y_tr, cv=folds, scoring="average_precision")
          for name, cols in FEATURE_SETS.items()}
    hgb_params, cv["HGB"] = tune_hgb(train[all_cols], y_tr, folds)
    best = max(cv[m].mean() for m in INTERPRETABILITY)
    chosen = next(m for m in INTERPRETABILITY
                  if cv[m].mean() >= best - cv[m].std(ddof=1) / np.sqrt(C.CV_FOLDS))

    # One scoring pass on the test snapshot.
    rng = np.random.default_rng(C.SEED)
    scores = {
        "B0 random": rng.random(len(test)),
        "B1 recency": test.m_since_hsic.to_numpy(),
        "B2 card age": -test.card_age_years.to_numpy(),
    }
    fitted = {}
    for name, cols in FEATURE_SETS.items():
        fitted[name] = _lr().fit(train[cols], y_tr)
        scores[name] = fitted[name].predict_proba(test[cols])[:, 1]
    fitted["HGB"] = _hgb(**hgb_params).fit(train[all_cols], y_tr)
    scores["HGB"] = fitted["HGB"].predict_proba(test[all_cols])[:, 1]

    table = pd.DataFrame({name: metrics(y_te, s) for name, s in scores.items()}).T
    table["cv_pr_auc_mean"] = pd.Series({m: s.mean() for m, s in cv.items()})
    table["cv_pr_auc_se"] = pd.Series({m: s.std(ddof=1) / np.sqrt(C.CV_FOLDS) for m, s in cv.items()})

    # Ship decision: chosen model vs the card-age rule.
    diff, lo, hi = paired_bootstrap(y_te, scores[chosen], scores["B2 card age"])
    shipped = chosen if lo > 0 else "B2 card age"
    hgb_lr = paired_bootstrap(y_te, scores["HGB"], scores["LR-all"])
    usage_lo, usage_hi = bootstrap_auc(y_te, scores["LR-usage"])
    usage_clears_bar = usage_lo > 0.5 and usage_lo >= C.USAGE_SIGNAL_MIN_AUC
    # The bar is necessary, not sufficient: usage must also add something beyond the profile
    # (card age above all), and keep its AUC within card-age groups. Young cards have little HSIC history.
    incr = paired_bootstrap(y_te, scores["LR-all"], scores["LR-profile"])
    young = test.is_young.to_numpy()
    usage_young = roc_auc_score(y_te[young], scores["LR-usage"][young])
    usage_mature = roc_auc_score(y_te[~young], scores["LR-usage"][~young])
    usage_signal = usage_clears_bar and incr[1] > 0

    # Fairness slice: gender is never a feature, only checked here.
    gender = test.gender.to_numpy()
    by_gender = {g: metrics(y_te[gender == g], scores[shipped][gender == g]) for g in np.unique(gender)}

    # Deployment scores at 2026-07-31 (kept in memory; never written per customer, the repo is public).
    score_snap = build_snapshot(C.CUTOFF_SCORE)
    if shipped == "B2 card age":
        deploy = -score_snap.card_age_years.to_numpy()
    else:
        both = pd.concat([train, test])
        cols = all_cols if shipped == "HGB" else FEATURE_SETS[shipped]
        model = _hgb(**hgb_params) if shipped == "HGB" else _lr()
        deploy = model.fit(both[cols], both.y).predict_proba(score_snap[cols])[:, 1]

    C.MODEL_EVAL.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    table.rename_axis("model").to_csv(C.MODEL_EVAL / "closure_comparison.csv")
    pd.DataFrame([
        {"comparison": f"{chosen} - B2 card age", "roc_auc_diff": diff, "ci_lo": lo, "ci_hi": hi},
        {"comparison": "HGB - LR-all", "roc_auc_diff": hgb_lr[0], "ci_lo": hgb_lr[1], "ci_hi": hgb_lr[2]},
    ]).to_csv(C.MODEL_EVAL / "closure_bootstrap.csv", index=False)
    lr_odds_ratios(train).rename_axis("feature").to_csv(TABLES / "closure_lr_odds_ratios.csv")
    gain_table(y_te, scores[shipped]).to_csv(TABLES / "closure_gain_by_decile.csv")

    t = table.loc
    out = {
        "cm_train_cards": int(len(train)), "cm_train_closers": int(y_tr.sum()), "cm_train_base_rate": float(y_tr.mean()),
        "cm_test_cards": int(len(test)), "cm_test_closers": int(y_te.sum()), "cm_test_base_rate": float(y_te.mean()),
        "cm_hgb_params": str(hgb_params),
        "cm_chosen_learned": chosen, "cm_shipped": shipped,
        "cm_vs_b2_roc_diff": diff, "cm_vs_b2_ci_lo": lo, "cm_vs_b2_ci_hi": hi,
        "cm_score_cards": int(len(score_snap)),
    }
    if shipped == "B2 card age":
        out["cm_score_top_decile_card_age_max_years"] = float(-np.quantile(deploy, 0.9))
    else:
        out["cm_score_top_decile_threshold"] = float(np.quantile(deploy, 0.9))
    for name in table.index:
        key = name.split()[0].lower().replace("-", "_")
        out[f"cm_{key}_roc_auc"] = float(t[name, "roc_auc"])
        out[f"cm_{key}_pr_auc"] = float(t[name, "pr_auc"])
        out[f"cm_{key}_top_decile"] = float(t[name, "top_decile_capture"])
    for g, m in by_gender.items():
        out[f"cm_{g.lower()}_roc_auc"] = m["roc_auc"]
        out[f"cm_{g.lower()}_top_decile"] = m["top_decile_capture"]
    out.update({
        "x5_recency_roc_auc": float(t["B1 recency", "roc_auc"]),
        "x5_usage_roc_auc": float(t["LR-usage", "roc_auc"]),
        "x5_usage_ci_lo": usage_lo, "x5_usage_ci_hi": usage_hi,
        "x5_profile_roc_auc": float(t["LR-profile", "roc_auc"]),
        "x5_usage_clears_bar": bool(usage_clears_bar),
        "x5_usage_roc_auc_young": float(usage_young), "x5_usage_roc_auc_mature": float(usage_mature),
        "x5_usage_increment_roc": incr[0], "x5_usage_increment_ci_lo": incr[1], "x5_usage_increment_ci_hi": incr[2],
        "x5_verdict": "usage predicts closure" if usage_signal else (
            "usage adds no closure signal beyond card age" if usage_clears_bar else "usage carries no closure signal"),
        "x6_hgb_roc_auc": float(t["HGB", "roc_auc"]), "x6_lr_roc_auc": float(t["LR-all", "roc_auc"]),
        "x6_hgb_minus_lr": hgb_lr[0], "x6_ci_lo": hgb_lr[1], "x6_ci_hi": hgb_lr[2],
        "x6_verdict": "HGB beats LR" if hgb_lr[1] > 0 else "HGB does not beat LR",
    })
    return out


if __name__ == "__main__":
    for k, v in run().items():
        print(f"{k:34s} {v:.4f}" if isinstance(v, float) else f"{k:34s} {v}")
    print(pd.read_csv(C.MODEL_EVAL / "closure_comparison.csv").round(4).to_string(index=False))
