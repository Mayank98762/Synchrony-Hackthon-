# Selection log: decision rules for the final run

**Fixed:** 23 Oct 2026, before the first final run of `run_all.py`.
**Honesty note:** the 23 Oct exploratory experiments (PROJECT_PLAN §4–§5) had already been run when these rules were written, so this is **not pre-registration** and the deck must not call it that. What it guarantees is narrower: these thresholds and selection rules were fixed before the final pipeline produced the reported numbers, and they are not changed afterwards. Any change goes in the change log at the bottom, with a reason, *before* the run it affects.

Every constant named here lives in `analysis/config.py`. If this file and `config.py` ever disagree, that is a bug: fix `config.py`, never the rule.

---

## 1. Shared definitions (PROJECT_PLAN §3 rule 9)

| Term | Definition | `config` / `prep` |
|---|---|---|
| Active row | `open_date ≤ date ≤ close_date`, both inclusive; NaT close = still open | `prep.active` |
| SoW | HSIC net ÷ total net over active rows, ratio of sums | `prep.sow` |
| 6-month window | (cutoff, cutoff + 6 calendar months], end inclusive | `HORIZON_MONTHS`, `prep.horizon` |
| 12-month lookback | (cutoff − 12 calendar months, cutoff] | `LOOKBACK_MONTHS`, `prep.lookback` |
| Card age | (cutoff − open_date) in days ÷ 365.25 | `DAYS_PER_YEAR` |
| Card-age bins | `<6m`, `6-12m`, `1-2y`, `2-3y`, `3y+` (right-closed) | `CARD_AGE_BINS` |
| Young card | Card age < 1 year | `YOUNG_CARD_YEARS` |
| Closure-model universe | All cards open at the cutoff (opened ≤ cutoff, not closed on or before it) | `prep.open_at` |
| Purchase | Active-window Sale row | `prep.purchases` |
| Purchase frequency | All MetroMart Sale rows (any method, card open or not) in the 12-month lookback | `prep.purchase_frequency` |
| High frequency | Purchase frequency strictly above the 2/3 quantile of the universe | `FREQ_TOP_QUANTILE` |
| Customer-level SoW filter | ≥ 3 purchases in each period compared | `MIN_PURCHASES_PER_PERIOD` |
| SoW bands | Zero = 0; Low / Mid / High = terciles of the non-zero FY25 values; FY25 cut points reused in FY26 | — |
| Silent-attrition universe | Card open from lookback start to horizon end; ≥ 1 HSIC row in the lookback; ≥ 1 active row in the horizon | — |
| Ticket bands | `<1k`, `1k-3k`, `3k-10k`, `capped` (= ₹9,999.99) | `TICKET_BANDS` |
| Snapshots | Train 2025-07-31, test 2026-01-31, score 2026-07-31 | `CUTOFF_*` |

`SEED = 42` for every random step (bootstraps, K-means, holdout assignment).

---

## 2. Heterogeneity gate (§3 rule 3)

Run on per-customer HSIC row share, customers with ≥ `GATE["min_rows"]` (4) active rows in the period.

| Test | Pass if |
|---|---|
| Variance ratio (observed ÷ binomial-expected variance), FY25 and FY26 | ≥ 1.10 in both years |
| Split-half r (odd vs even purchases by `txn_id`, same FY) | ≥ 0.10 |
| Persistence r (FY25 → FY26) | ≥ 0.20 |

- **The gate passes only if all three pass.** A variable that fails is not used for targeting.
- **If customer-level SoW passes the gate,** the "whole book is low-SoW" framing is withdrawn and the slide says so.

---

## 3. Silent attrition (X3)

- **Cutoffs:** 2025-01-31, 2025-07-31, 2026-01-31.
- **Two nulls:**
  - *fixed-share:* (1 − own lookback HSIC row share)^(horizon rows);
  - *time-aware:* (1 − portfolio HSIC row share in the horizon)^(horizon rows).
- **Excess** = observed zero-HSIC rate − expected, with a 95% normal-approximation CI over customers.
- **Verdict:**
  - **"Concentrated"** if the time-aware excess is ≥ 2pp *and* its CI excludes 0 at two or more cutoffs.
  - **"Universal"** otherwise. Never "rejected".

---

## 4. Pre-closure decay (X4)

- Closers' HSIC row share by month before closure (0–12), minus the portfolio share in the same calendar month.
- **Decay is supported** if the OLS slope of the adjusted excess on months-before-closure has a 95% CI that excludes 0 *and* the mean adjusted excess over months 0–2 is ≤ −2pp. Otherwise: no decay beyond the calendar trend.

---

## 5. Closure model (X5, X6, F10)

- **Data:**
  - **universe:** rule 9 (all open cards, including those under 6 months);
  - **training:** fit on the 2025-07-31 snapshot, tested once on the 2026-01-31 snapshot;
  - **label:** card closes in the 6-month window.
- **Features:**
  - **usage, from the lookback:** row count; HSIC row count; HSIC row share; HSIC net share; months since the last HSIC row (13 if none); months since the last row; change in HSIC share between the two halves of the lookback; log net spend;
  - **profile:** card age, Prime, age, credit limit, APR.
- **Excluded:** gender (fairness slice only), segment labels, anything dated after the cutoff.
- **Leakage asserts:** max feature date ≤ cutoff < min label date.
- **Candidates:**

| ID | Model |
|---|---|
| B0 | Random scores (`SEED`) |
| B1 | Recency rule: months since the last HSIC row |
| B2 | Card-age rule: younger = riskier |
| LR-profile / LR-usage / LR-all | L2 logistic regression, standardised, `class_weight="balanced"` |
| HGB | `HistGradientBoostingClassifier`, `class_weight="balanced"`; grid `max_depth ∈ {2, 3}`, `learning_rate ∈ {0.05, 0.1}`, `l2_regularization ∈ {0, 1}`, `max_iter = 200` |

- **Tuning:** only on the training snapshot, with 5-fold `StratifiedKFold` (`SEED`) and PR-AUC as the score. The test snapshot is scored once, after the choice is made.
- **Choice among learned models:** the most interpretable model (LR-all, then HGB) within 1 SE of the best cross-validated PR-AUC.
- **Ship decision (test snapshot):** compute the paired bootstrap difference in ROC-AUC vs **B2** (1,000 resamples).
  - Ship the chosen model if the 95% CI of the difference is entirely above 0.
  - **Otherwise ship B2 (card age) and say so.**
  - PR-AUC and top-decile capture are reported for every candidate either way.
- **Usage carries closure signal** only if LR-usage's ROC-AUC CI excludes 0.5 *and* its lower bound is ≥ 0.55.

---

## 6. Segmentation (§7)

**K-means negative control**
- **Features:** customer-level FY25 SoW (₹), FY25 HSIC row share, H1 → H2 FY25 change in HSIC row share. Customers must pass the rule-9 SoW filter. Features are standardised.
- **k:** chosen from 3–8 by best silhouette, with `n_init = 20`.
- **Stability:** mean ARI over 20 bootstrap refits, against the full-data labels.
- **Outcome separation:** η² of FY26 customer SoW on the FY25 cluster label, with a 1,000-resample bootstrap CI.
- **K-means "finds real structure"** only if ARI ≥ 0.70 *and* the lower CI bound of η² is ≥ 0.01. If it does, the "whole book" framing is withdrawn (as in §2).

**Frequency × card-age 2×2**
- **Build:** boxes are built at **2026-01-31**; outcomes are measured over Feb–Jul 2026; production assignment is at **2026-07-31**.
- **Boxes:** B = young + high frequency · C = young + other · D = mature + high frequency · E = mature + other.
- **Outside the grid:**
  - **A** = card closed on or before the cutoff, with any MetroMart net spend after its close date;
  - **F** = no card.
- **Order:** first match wins, in the order A, B, C, D, E, F.
- **Outcomes per box:**
  - SoW (ratio of sums, active rows);
  - 6-month closure rate;
  - non-HSIC net ₹ per customer;
  - Prime share.

  Every outcome is reported with a 1,000-resample bootstrap CI.
- **Assertions:**
  - **Independence:** |young − mature share in the high-frequency group| ≤ 3pp, or the run fails.
  - **"SoW doesn't separate the boxes"** if every pairwise box difference in SoW is within ±2pp. Otherwise the slide reports the difference.
  - **"Card age separates risk"** if the young − mature closure-rate difference has a CI that excludes 0.
  - **"Frequency separates value"** if the high − other non-HSIC ₹ difference has a CI that excludes 0.
- **Splitting B and C:** each is reported split into `<6m` and `6-12m` if the closure-rate difference between those two groups has a CI that excludes 0.
- **Boundary sensitivity:** share of customers who change box when the tercile cut moves by ±10% and the young cut moves to 0.9 / 1.1 years.

---

## 7. Hypothesis-test verdicts for the other experiments

| ID | Supported / "rejected" if |
|---|---|
| X8 Prime vs Non-Prime | Rejected if \|Prime − Non-Prime SoW\| ≤ 2pp in both FYs |
| X9 Category leakage | Rejected if the max − min category SoW is ≤ 3pp in both FYs |
| X10 Credit limit binds | Rejected if < 1% of customer-months spend ≥ 50% of their limit at MetroMart |
| X11 Festive peaks | Rejected if no month's sales index exceeds 115 (mean = 100) |
| X12 Wallet cannibalises | Rejected if the Wallet takes < 25% of the stayers' HSIC loss |
| X13 Never-activated segment | Rejected if observed − chance zero-HSIC share is ≤ 2pp |
| X14 Mix as a segment | Rejected if FY25 → FY26 persistence r < 0.20 |
| X17 Returns by method | No signal if max − min return-row share across methods ≤ 1pp |

---

## 8. Economics (§8): rules `economics.py` must follow

- **Net margin per ₹** = interchange + revolve income − reward rate × (1 − co-funding), using the scenario values in `config.SCENARIOS`.
- **Reward rate** is the rate on *the spend being shifted*:
  - the pipeline-measured FY26 effective rate (≈ 1.399%, never hard-coded) for general spend;
  - 5% / 3% for Prime Grocery / Electronics, including O3's Prime-first target.
- **`never`:** if the incentive per incremental ₹ is ≥ the net margin per ₹ (or the required shift is > 100%), the scenario result is `never`, never a number.
- **Break-even revolve rate** is also reported per offer: the revolve income (% of spend) at which the offer breaks even with all other inputs at base. It is assumption-free on the revolve side.
- **Retention value** = 12 months of the card's expected net margin × the change in closure probability (Simulated).

---

## 9. Pilot design

- **Holdout:** 10% per offer and segment, randomised with `SEED`.
- **Power:** α = 0.05, power = 0.80, so MDE = 2.8·√(2p(1−p)/n).
- **Scale** only if the CI of the lift excludes 0 *and* net value > 0. A null result is reported as a refuted hypothesis.

---

## 10. Reproduction tolerances (§14)

- **23 Oct exploratory numbers:** ±0.2pp unless the plan states otherwise.
- **EDA cross-checks:** counts must be identical and rates must match to 3 decimals.
- **A failed reproduction stops the run.** The cause is found and logged; the tolerance is never widened to make the check pass.

---

## Change log

| Date / time | Rule | Change | Reason |
|---|---|---|---|
| 23 Oct, after the first `closure_model` run | §5 "usage carries closure signal" | **Rule unchanged; two checks added to the report.** (1) Paired bootstrap of LR-all − LR-profile on test ROC-AUC. (2) LR-usage ROC-AUC within young (< 1y) and mature cards. Usage counts as signal only if it clears the existing bar *and* (1)'s CI is above 0 | The rule says "only if", so clearing 0.55 is necessary, not sufficient. On the rule-9 universe, LR-usage scored 0.567 (CI 0.553–0.581), which clears the bar, but it adds −0.0004 (CI −0.0023 to +0.0014) beyond the profile and drops to 0.525 / 0.517 within young / mature cards. Usage is standing in for card age. Both numbers are reported, not just the verdict |
| 23 Oct, during the first `segments` run | §1 customer-level SoW; §6 K-means features | **Customer-level SoW is clipped to [0, 1]**, and the number of clipped customer-FY values is reported (`x1_sow_values_clipped`: 1,885 of 24,654) | Returns can push HSIC net below 0, and a near-zero total net makes the ratio explode (FY25 cluster means reached 389×). Unclipped, K-means spent clusters on those outliers. Clipping follows plan v4's original rule. SoW bands are unaffected (≤ 0 → Zero, > 1 → High either way) |
| 23 Oct, first `segments` run | §6 segment A | **No change.** "Any MetroMart net spend after close" is implemented as post-close net > 0 by the cutoff. That gives 5,903 customers at 2026-07-31 vs F11's 6,227, which counts *any* post-close row, including 324 customers whose post-close net is ≤ 0 (returns ≥ purchases; 89 made only returns) | Recorded so the deck uses one number per claim: F11 (6,227, ₹91.2M) for the finding on slide 8; segment A (5,903, ₹92.3M) for slides 9–11 |
| 23 Oct, first `segments` run | §6 boundary sensitivity | **No change.** Moving the frequency cut +10% (5 → 5.5) changes nothing, because purchase counts are integers and "> 5" and "> 5.5" select the same customers. The −10% move (→ 4.5) shifts 12.3% of grid customers | Reported as-is so the 0% isn't read as robustness |
| 24 Oct, merging Mayank's modules | Plan §5 F9 (closures per open card) | **Definition fixed.** The numerator now counts only closures of cards open at the quarter start, so it is a subset of the denominator; the first version also counted the 193 cards opened and closed inside Apr–Jun 2026 (1.8% → 4.0%). The fix reproduces the 23 Oct 1.7% → 3.4%. The first EDA's `closure_hazard` used the wider count, and `verify_second.py` now checks it against that count | Slide 8 says 1.7% → 3.4%; the chart reads the same table as the `f9_*` keys |
