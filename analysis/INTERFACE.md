# `analysis` interface (hour-0.5 handoff)

Everything below is importable from the repo root inside the `synchrony` conda env:

```python
from analysis import config as C, prep

d = prep.load()                # validated + enriched, cached: d.cust, d.txn, d.categories, d.payments
act = prep.active(d.txn)       # rows inside an open card window (the only rows SoW may use)
prep.sow(act[act.fy == 2026])  # 0.1948
```

Run a module as `python -m analysis.<module>` from the repo root, e.g. `python -m analysis.prep` (smoke test, ~8 s).
Never mutate `d.cust` / `d.txn` in place: `load()` is cached and shared. Use `.copy()` or `.assign()`.

## `d.cust`: one row per customer (45,000)

| Column | Type | Notes |
|---|---|---|
| `customer_id` | int | |
| `age` | int | 18–60 |
| `gender` | str | Fairness slice only; **never a model feature** |
| `membership` | str | `"Prime"` / `"Non-Prime"` |
| `is_prime` | bool | |
| `open_date`, `close_date` | datetime | NaT if no card / still open |
| `credit_limit`, `apr` | float | NaN if no card |
| `has_card` | bool | False for the 6,836 non-cardholders |
| `is_closed` | bool | 7,664 closed cards |

## `d.txn`: one row per transaction (444,118)

| Column | Type | Notes |
|---|---|---|
| `customer_id`, `txn_id` | int | |
| `date` | datetime | 2024-08-01 to 2026-07-31 |
| `month` | Period[M] | |
| `fy` | int | 2025 or 2026 (FY runs Aug–Jul, named by the year it ends) |
| `fq`, `fq_label` | int, str | Fiscal quarter 1–4 (Q1 = Aug–Oct); label `"FY25 Q1"` |
| `half` | str | `"H1"` = Aug–Jan, `"H2"` = Feb–Jul |
| `category_code`, `category` | int, str | 1 Grocery, 2 Electronics, … |
| `payment_code`, `payment_method`, `payment_short` | int, str, str | Short names: Debit, Other CC, HSIC, Cash/UPI, Wallet |
| `txn_type`, `is_sale`, `is_return` | str, bool, bool | |
| `amount` | float | Always positive, as delivered |
| `net` | float | +amount for a Sale, −amount for a Return. **Use this for SoW** |
| `n_txn` | int | Purchases in the row; **0 for Returns** (brief) |
| `is_hsic` | bool | `payment_code == 3` |
| `ticket_band`, `is_capped` | category, bool | `<1k`, `1k-3k`, `3k-10k`, `capped` (= ₹9,999.99) |
| `is_prime`, `has_card`, `open_date`, `close_date` | | Joined from `d.cust` |
| `is_active` | bool | open_date ≤ date ≤ close_date (both inclusive; NaT close = open) |
| `reward_rate` | float | The customer's rate for this category (5 / 3 / 1% Prime, 1% Non-Prime) |
| `reward` | float | `net × reward_rate` on active HSIC rows, else 0 (returns claw back) |
| `reward_credit_month` | Period[M] | `month + 1` |

## Helpers in `prep`

| Function | Returns |
|---|---|
| `active(txn)` | Rows with `is_active` |
| `purchases(txn)` | Rule 9 "purchase": active-window Sale rows |
| `sow(rows)` | HSIC net ÷ total net (ratio of sums); NaN if total ≤ 0 |
| `months_after(date, n)` | Calendar-month offset (rule 9) |
| `in_window(dates, start, end)` | Boolean mask for (start, end] |
| `lookback(cutoff)`, `horizon(cutoff)` | (start, end) for the 12-month lookback / 6-month horizon |
| `open_at(cust, cutoff)` | Mask: card open at the cutoff (closure-model universe) |
| `closed_in(cust, start, end)` | Mask: closed in (start, end] |
| `card_age_years`, `card_age_bin`, `is_young` | Card age at a cutoff (days ÷ 365.25; bins `<6m … 3y+`; young = < 1 year) |
| `purchase_frequency(txn, cutoff)` | Sale rows in the 12 months up to the cutoff, **all payment methods, card open or not** (rule 9). Series by `customer_id`; absent = 0 |
| `snapshot_universe(cutoff)` | Cards open at the cutoff + `card_age_years`, `card_age_bin`, `is_young`, `closed_6m` (NaN at 2026-07-31) |

## Constants in `config` (change values there, never inline)

`SEED`, `DATA_START`, `DATA_END`, `FISCAL_YEARS`, `HSIC_CODE`, `GROCERY`, `ELECTRONICS`, `PRIME_RATES`, `CUTOFF_TRAIN` (2025-07-31), `CUTOFF_TEST` (2026-01-31), `CUTOFF_SCORE` (2026-07-31), `SILENT_ATTRITION_CUTOFFS`, `LOOKBACK_MONTHS`, `HORIZON_MONTHS`, `CARD_AGE_BINS/LABELS`, `YOUNG_CARD_YEARS`, `FREQ_TOP_QUANTILE`, `MIN_PURCHASES_PER_PERIOD`, `TICKET_BANDS/LABELS`, `GATE`, `BOOTSTRAP_N`, `SCENARIOS`, and the output paths `OUTPUTS`, `CHARTS`, `MODEL_EVAL`.

## Numbers contract

Each experiment module exposes functions that return a plain `dict` of named numbers, e.g.

```python
def f1_sow_trend() -> dict:
    return {"sow_fy25": 0.2891, "sow_fy26": 0.1948, ...}
```

`export.py` merges every dict into `outputs/key_numbers.md`. Keys are `snake_case`, prefixed with the finding ID (`f1_`, `x3_` …). Values are plain `float` / `int` / `str`, never numpy types.

**Run everything:** `python analysis/run_all.py` (about 3 minutes). Your module is picked up automatically once `analysis/experiments_f.py`, `analysis/experiments_h.py` or `analysis/economics.py` exists and has a `run()` function. If two modules produce the same key, the run stops.

**Labels** come from the key prefix:
- `o<N>_`, `mde_`, `econ_` → Simulated;
- `assumed_` → Assumed;
- `f15_net_margin*`, `f15_gross*` → Measured × Assumed;
- everything else → Measured.

**Verdicts:** every X test must also return `x<N>_verdict` (a short string), which feeds `outputs/experiment_log.csv`.

### Keys the reproduction checks read (`analysis/checks.py`)

Use exactly these names, or the check stays `pending`. Values are shares (0–1) unless the name ends in `_pp` (percentage points) or is a ₹ amount.

| Owner | Keys |
|---|---|
| Mayank: F1 | `f1_sow_fy25`, `f1_sow_fy26` |
| Mayank: F2 | `f2_leaver_pp`, `f2_stayer_pp`, `f2_joiner_pp` |
| Mayank: F3 | `f3_cash_upi_share_of_loss` (0.47) |
| Mayank: F8 | `f8_prime_ge_left_on_table` (₹) |
| Mayank: F11 | `f11_post_close_net` (₹) |
| Mayank: F14 | `f14_aug24_cards`, `f14_aug24_net_per_card`, `f14_aug24_hsic_per_card`, `f14_aug24_sow`, and the same four with `may26` |
| Mayank: X3 | `x3_excess_time_2025_01_31`, `x3_excess_time_2025_07_31`, `x3_excess_time_2026_01_31` (shares, e.g. 0.007); also `x3_excess_fixed_<cutoff>` |
| Shreyash: F12 | `f12_gap` (₹) |
| Shreyash: F15 | `f15_reward_rate_fy26`, and for the impact ledger: `f15_net_margin_lo_nocofund`, `f15_net_margin_hi_nocofund`, `f15_net_margin_lo_cofund`, `f15_net_margin_hi_cofund` (₹) |

Results land in `outputs/model_eval/checks.csv` (pass / FAIL / pending). A FAIL stops the run.

## Checked against the plan (smoke test, 23 Oct)

SoW 0.2891 / 0.1948 · FY payment-mix shares (all 8) · Aug 2024: 21,514 cards, ₹1,036.8 / ₹356.2 per card, SoW 0.344 · May 2026: 30,742 cards, ₹1,028.9 / ₹166.7, SoW 0.162 · open cards 26,749 / 29,198 · closers 1,281 / 1,799 · closure by card age at 2026-01-31: 14.7 / 9.0 / 6.3 / 4.0 / 3.0% · young cards at 2026-07-31: 6,313; top-tercile frequency share young 31.1% vs mature 30.9%.
