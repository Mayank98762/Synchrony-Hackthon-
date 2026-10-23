# Handoff: Mayank (analytics and the story)

What you build, which inputs to use, what number to expect, and where each result ends up.
Your scope comes from [TEAM_SPLIT.md](TEAM_SPLIT.md); the rules come from [PROJECT_PLAN.md](PROJECT_PLAN.md) v5.3 and [outputs/model_eval/selection_log.md](outputs/model_eval/selection_log.md).

## 0. Setup (15 minutes, do this first)

1. `conda create -n synchrony python=3.12 nodejs=20 -y`, then `conda activate synchrony` and `pip install -r requirements.txt`.
   - The versions are pinned: **pandas 3.1**, numpy 2.5, scikit-learn 1.9.
   - Don't run the pipeline from your Anaconda base env. pandas 2.x behaves differently.
2. Put the 4 case CSVs in **`data/`** (not the repo root), with the original file names. `.gitignore` keeps them out of git.
3. Check the setup with `python -m analysis.prep` from the repo root. It should print SoW FY25 0.2891 and FY26 0.1948, and finish in about 8 seconds.
4. Read [analysis/INTERFACE.md](analysis/INTERFACE.md). It lists every column and helper you'll use.

`config.py` and `prep.py` live on Devansh's `devansh` branch, which isn't pushed yet. Until it is, use the stub numbers in the tables below; they are the verified 23 Oct figures.

## 1. Rules for your code

- **Files:** `analysis/experiments_f.py` (F-findings) and `analysis/experiments_h.py` (hypothesis tests).
- **One function per finding**, returning a plain `dict`:
  - keys in `snake_case`, prefixed with the ID: `f1_sow_fy25`, `x3_excess_time_2026_01_31`;
  - values are Python `float` / `int` / `str`, never numpy types (wrap with `float()`).
- **Add `run() -> dict`** to each file, merging all its finding dicts. Devansh's `run_all.py` calls `experiments_f.run()` and `experiments_h.run()`.
- **Inputs:** always `d = prep.load()`. SoW uses `prep.active(d.txn)` and `prep.sow(...)` (ratio of sums, net). Use `prep.months_after`, `prep.in_window`, `prep.horizon` and `prep.lookback` for every date window: calendar months, (start, end] (rule 9).
- **Thresholds and dates:** take them from `config` (`C.VERDICT`, `C.SILENT_ATTRITION_CUTOFFS`, `C.CUTOFF_TEST` …). Never type them inline.
- **Charts:** save to `outputs/charts/<slide#>_<name>.png` (e.g. `04_sow_trend.png`) with Shreyash's `analysis/style.py`. Until it lands, plain matplotlib at 16:9 is fine.
- **The repo is public.** Never write a customer-level table (one row per customer) into `outputs/`. Aggregates only.
- **Verdicts:** follow `selection_log.md`. Silent attrition is "universal", never "rejected". Any "why" is labelled Hypothesis.

## 2. `experiments_f.py`: findings (slides 4, 5, 6, 8)

| ID | Compute | Inputs | Stub (23 Oct) | Goes to |
|---|---|---|---|---|
| F1 | SoW by FY and fiscal quarter | `active`, `fy`, `fq_label`, `sow()` | FY 0.2891 / 0.1948; quarters 32.7% → 15.6% | Slide 4 trend chart, slide 2 |
| F2 | SoW Bridge: all FY25 → stayers FY25 → stayers FY26 → all FY26. Stayers = card open on 2024-08-01 and not closed before 2026-07-31. **Assert it reconciles** | `d.cust` dates, `active` | leaver +0.26pp, stayers −9.54pp (29.2 → 19.6%, n = 18,111), joiner −0.15pp | Slide 4 waterfall |
| F3 | Stayers' payment-mix shift FY25 → FY26, and each method's share of HSIC's loss | `payment_short`, stayers | Cash/UPI 47%, Debit 21%, Other CC 19%, Wallet 14% | Slide 5 |
| F4 | Cash/UPI share change: stayers vs non-cardholders (`~has_card`) | `has_card` | +4.5pp vs +1.8pp | Slide 5 |
| F5 | Method mix by `ticket_band` × FY (active Sale rows) | `ticket_band` | HSIC <1k 23.3 → 15.0 … capped 30.1 → 21.7% | Slide 5 chart |
| F6 | HSIC row share by ticket tercile within category × quarter; logistic AUC month-only vs everything | `amount`, `category_code`, `fq_label` | 17.1% / 24.2% / 25.5%; AUC 0.592 → 0.604 | Slide 5 one-liner, appendix |
| F7 | Wallet share of capped tickets by FY | `is_capped` | 48.5 → 51.1% | Slide 5 |
| F8 | Prime G+E spend on other methods in FY26, and the cashback left on the table at 5% / 3%; context total for all cardholders | `is_prime`, `category_code`, `reward_rate` | ₹47.4M → **₹1.60M**; context ₹3.98M vs ₹0.96M earned | **Slide 10 hero offer**, slide 2 |
| F9 | Closures ÷ cards open at quarter start, by calendar quarter | `d.cust` | 1.7% (Jul–Sep 2024) → 3.4% (Apr–Jun 2026) | Slide 8 |
| F10 | 6-month closure rate by `card_age_bin` at both cutoffs | `prep.snapshot_universe(cutoff)` | 2025-07-31: 8.3 / 6.6 / 4.6 / 3.8 / 2.8%; 2026-01-31: 14.7 / 9.0 / 6.3 / 4.0 / 3.0% | **Slide 8** (Devansh's slide; send him the dict) |
| F11 | Closers with spend after close; post-close net ₹; post-close mix | `close_date`, `date` | 6,227 of 7,664; ₹91.2M; Wallet 46 / Cash 28 / Debit 13 / Other CC 13% | Slide 8, segment A |
| F13 | FY25 → FY26 persistence of purchase count and net spend per customer | `customer_id`, `fy` | r = 0.44 / 0.22 | Slide 9 footnote (why frequency is the value axis) |
| F14 | Per-card monthly: cards active in the month, net / card, HSIC / card, SoW, for Aug 2024 and May 2026 (and every month for the chart) | `month`, card dates | 21,514 · ₹1,036.8 · ₹356.2 · 0.344 → 30,742 · ₹1,028.9 · ₹166.7 · 0.162 | **Slide 4 headline**, slide 2, dashboard KPI |

F12 and F15 belong to Shreyash: put them in a **separate section** of the same file, with no shared helper functions, so merges stay clean.

## 3. `experiments_h.py`: hypothesis tests (slides 6, 7, appendix)

The verdict thresholds are in `C.VERDICT` and `selection_log.md` §3, §4 and §7.

| ID | Test | Stub (23 Oct) | Verdict | Goes to |
|---|---|---|---|---|
| X3 | Zero-HSIC rate in the 6-month horizon vs the fixed-share and time-aware nulls, at the 3 `SILENT_ATTRITION_CUTOFFS`; excess + 95% CI | Fixed +21.6 / +17.5 / +21.5pp; time-aware +0.7 / +0.1 / +0.0pp (±1pp) | **Universal** | **Slide 7** (1 of 3), slide 6, dashboard page 3 |
| X4 | Closers' HSIC share by months before closure, raw and minus the same-month portfolio share; slope + CI | Raw 27.0 → 20.5%; adjusted −1.4 to +2.3pp, no trend | No decay | **Slide 7** (2 of 3), dashboard toggle |
| X8 | SoW Prime vs Non-Prime by quarter | 32.7 → 15.6 vs 32.8 → 15.5% | Rejected | Slide 6 slice chart |
| X9 | SoW by category by FY | 23–24% everywhere | Rejected | Slide 6, appendix |
| X10 | Monthly MetroMart spend ÷ credit limit | median 1.2%, max 26.5%, 0 months ≥ 50% | Rejected | Appendix |
| X11 | Monthly sales index | 92–108 | Rejected | Appendix |
| X12 | Wallet share of stayers' HSIC loss; Wallet share for non-cardholders | 14%; 48.8 → 44.8% | Rejected | Slide 5 one-liner, appendix |
| X13 | Zero-HSIC cardholders, observed vs chance | 26.9% vs 25.7% | Rejected | Appendix |
| X14 | FY25 → FY26 persistence of big-ticket share and G+E share | r = 0.008 / 0.000 | Rejected as segments | Slide 9 footnote, appendix |
| X17 | Return-row share by payment method | 10.1% for all | No signal | Appendix |

## 4. What you get from Devansh (and when)

| Hour | What | Where | You use it for |
|---|---|---|---|
| now | `config.py`, `prep.py`, `INTERFACE.md` | `analysis/` (devansh branch) | Everything |
| ~4 | `experiments_ml.gate(...)` and the X1 result: variance ratio FY25 / FY26, split-half r, persistence r, SoW-band movement table | `analysis/experiments_ml.py`; keys `x1_*` | **Slide 6** (the gate + band table) and **slide 7** (3 of 3: K-means on noise) |
| ~4 | X5 / X6: usage features don't predict closure | keys `x5_*`, `x6_*` | Slide 7 lessons, appendix |
| 8 | `key_numbers.md` with every key | `outputs/key_numbers.md` | Final numbers on your slides |

Planned keys from Devansh (stub values in brackets):
- `x1_variance_ratio_fy25` [1.001], `x1_variance_ratio_fy26` [0.996];
- `x1_split_half_r` [−0.007], `x1_persistence_r` [0.00];
- `x1_band_to_zero_min` / `x1_band_to_zero_max` [0.35 / 0.37 from the pipeline; the second EDA's 39–43% used a different customer filter, and the conclusion is the same: every FY25 band ends up "Zero" equally often];
- `x1_gate_pass` [False].

## 5. Your slides (4–7)

| Slide | Message | Charts | Numbers |
|---|---|---|---|
| 4 The decline | Spend per card flat, HSIC per card halves; the Bridge shows 100% of the decline comes from stayers | `04_sow_trend.png`, `04_per_card.png`, `04_bridge.png` | F1, F2, F14 |
| 5 Where it went | Cash/UPI 47%, in every ticket band; Wallet owns big tickets. "Why Cash/UPI?" = **Hypothesis H-imm** | `05_mix_shift.png`, `05_ticket_bands.png` | F3–F7, X12 |
| 6 Silent attrition is universal | Same decline in every slice + the gate + the band table. One line: no fees, so customers stop using the card rather than close it (**Hypothesis**) | `06_slices.png`, `06_gate.png` (Devansh's numbers) | X8, X9, x1_* |
| 7 Common hypotheses we tested | Three only: silent attrition vs the trend (+21pp → 0), the decay curve that disappears, K-means on noise. Plus 3 lessons | `07_silent_null.png`, `07_decay_raw_vs_adj.png`, `07_kmeans.png` | X3, X4, x1_* |

**Never** name v4 or the blueprint on a slide, and never say "pre-registered".

## 6. Verification (PROJECT_PLAN §14), before the hour-8 handoff

- **Reproduction:** every stub above within ±0.2pp. Bridge +0.26 / −9.54 / −0.15. Cash/UPI 47%. Time-aware excess |x| < 1.5pp. ₹91.2M. ₹1.60M.
- **Exact EDA cross-checks:** counts identical and rates to 3 decimals. Pooled SoW and all 8 mix shares; the Aug 2024 and May 2026 per-card rows; open cards 26,749 / 29,198; closers 1,281 / 1,799.
- **Spot checks:** trace 3 customers (one closed-and-shopping, one young card, one high-frequency mature card) from raw rows to segment to offer. Pick the IDs from Devansh's segment output.

A failed check stops the run: find the cause, don't widen the tolerance.
