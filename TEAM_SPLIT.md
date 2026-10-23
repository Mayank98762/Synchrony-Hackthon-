# Team split v2: by strength (from PROJECT_PLAN.md v5.3)

- **Devansh** (coding, ML, web dashboard, most capable laptop): pipeline, models, dashboard
- **Mayank** (analytics): findings, hypothesis tests, the story slides
- **Shreyash** (economics): offers, break-even, the value story, deck integration

Each owner has their own files, slides and charts, so merge conflicts should be rare.

## How we stay independent

1. **Devansh ships the foundation first** (`config.py`, `prep.py`) and posts the interface (function and column names) within 30 minutes. Mayank starts on the raw CSVs with pandas and switches to `prep.py` when it lands. Shreyash needs no data to start.
2. **Numbers contract.** Every module returns a plain `dict` of named numbers; Devansh's `export.py` merges them into `key_numbers.md`. Until then, use the 23 Oct figures in the plan as stubs.
3. **Experiments are split by owner** (deviation from §10): `experiments_f.py` + `experiments_h.py` (Mayank), `experiments_ml.py` (Devansh).
4. **Charts:** each person exports charts for their own slides to `outputs/charts/<slide#>_*.png`, using Shreyash's style guide (`analysis/style.py`, hour 1).
5. **Branches:** one per person; merge to `main` at hours 4, 8 and the freeze.
6. **Heavy compute (bootstraps, HGB, K-means ARI×20) runs on Devansh's laptop.**

---

## Devansh: engineering, ML, dashboard

Status as of 23 Oct, night: everything Mayank and Shreyash need from Devansh is done, on the `devansh` branch. ☑ = done · ◐ = partly done · ☐ = not started.

| Task | Files | Status |
|---|---|---|
| Env (`synchrony` conda), `requirements.txt`, move CSVs to `data/` | repo root | ☑ versions pinned; CSVs copied, originals kept |
| `config.py` (paths, SEED, cutoffs, ASSUMPTIONS, gate thresholds, rule-9 definitions) | `analysis/config.py` | ☑ |
| `prep.py` (load, clean, enrich per §2) with validation asserts | `analysis/prep.py` | ☑ interface in `analysis/INTERFACE.md` |
| `selection_log.md` (decision rules fixed before the final run) | `outputs/model_eval/` | ☑ changes after the first run are in its change log |
| Handoff notes: what each teammate uses, from where, for which slide | `HANDOFF_MAYANK.md`, `HANDOFF_SHREYASH.md` | ☑ (added) |
| Heterogeneity gate (variance ratio, split-half, persistence) as a reusable function | `analysis/experiments_ml.py` | ☑ `gate()`; customer SoW fails it |
| X1, X2, X5, X6, X7, X15, X16: K-means on SoW, per-customer detector, usage-based closure prediction, HGB vs LR, onboarding cliff, sparsity and no-treatment-data audits | `analysis/experiments_ml.py` | ☑ X1, X2, X7, X15, X16 here; X5, X6 come from `closure_model.py`; the K-means control from `segments.py` |
| Closure model: B0, B1, B2 (card age), LR, HGB; out-of-time train and test; bootstrap CIs; ship-the-rule decision | `analysis/closure_model.py` | ☑ card-age rule ships (AUC 0.672) |
| Segmentation: K-means negative control (ARI, outcome separation), frequency × card-age 2×2, segments A–F, per-box table, boundary sensitivity | `analysis/segments.py` | ☑ |
| `export.py`, `run_all.py` (one command rebuilds everything, fails on any assert), `key_numbers.md`, `experiment_log.csv`, `impact_ledger.csv` | `analysis/` | ◐ built and run (18 pass, 0 fail, 21 pending); final run after Mayank's and Shreyash's modules land |
| **Dashboard** (§11): 4 pages, React + Vite + TS + Tailwind + ECharts, JSON contract. Built after charts exist; dropped if late | `dashboard/` | ☐ |
| **Slides 8 and 9** and their charts (closures; who to prioritise) | deck | ☐ next |

## Mayank: analytics and the story

| Task | Files |
|---|---|
| F1–F11, F13, F14: SoW trend, Bridge, payment-mix shift, DiD, ticket bands, ticket model, Wallet and capped tickets, reward paradox (₹1.60M), closures per card, closure-by-age table (F10), post-closure spend, persistence, per-card monthly view | `analysis/experiments_f.py` |
| X3, X4, X8–X14, X17: silent attrition vs both nulls at 3 cutoffs, pre-closure decay (raw vs adjusted), Prime, category, credit limit, festive, Wallet, never-activated, ticket and category persistence, returns | `analysis/experiments_h.py` |
| **§14 verification:** reproduction checks, exact EDA cross-checks, 3-customer spot checks | — |
| **Slides 4, 5, 6, 7** and their charts (the decline; where it went; universal attrition; the three hypotheses) | deck |
| Optional `notebooks/story.ipynb` (cut-order item 2) | `notebooks/` |

## Shreyash: economics, offers, integration

| Task | Files |
|---|---|
| Chart style guide (palette, fonts, 16:9 sizes), hour 1 | `analysis/style.py` |
| `economics.py`: net margin per ₹ after rewards, break-even shift rate, `never` output, three scenarios, retention value, MDE, offers O1–O8, the H-imm and H-aware pilot arms. Self-contained: inputs are plain numbers | `analysis/economics.py` |
| F12 and F15 (₹33M counterfactual gap, net-of-rewards lost margin): needs only the FY aggregates, so no `prep.py` wait | `analysis/experiments_f.py` (separate section) |
| Slide template, storyline, and **slides 1, 2, 3** (title, executive summary, data and assumptions with the Measured / Simulated / Assumed / Hypothesis labels) | deck |
| **Slides 10, 11, 12** and their charts (offers; economics and pilot; roadmap and asks) | deck |
| **Appendix:** 17-hypothesis table, closure-model table, gate details, assumptions, limitations | deck |
| **Deck integration:** `[KN]` placeholders replaced from `key_numbers.md`, consistency pass on labels and badges, PDF export | deck |
| **Submission:** email the PDF to analyticshiring@syf.com, subject = roll number only, attached (not Drive), before 8:00 PM IST on 24 Oct | — |

---

## Load check

| | Code | Slides | Other |
|---|---|---|---|
| Devansh | Foundation, ML, segmentation, pipeline, dashboard | 2 | Compute |
| Mayank | F and hypothesis tests (pandas) | 4 | Verification |
| Shreyash | Economics, F12/F15 | 6 + appendix | Style guide, integration, submission |

Devansh carries the most code, so the dashboard goes first on the cut list; if he is behind, it is dropped with no effect on the deck. Mayank and Shreyash own most of the slide work, which suits their strengths.

## Handoffs (the only dependencies)

| When | From → to | What | Status |
|---|---|---|---|
| Hour 0.5 | Devansh → Mayank | `prep.py` interface (function and column names) | ☑ `analysis/INTERFACE.md` |
| Hour 1 | Devansh → all | working `prep.py` and `config.py` | ☑ |
| Hour 1 | Shreyash → all | `style.py` and the slide template | ☐ |
| Hour 4 | Mayank, Devansh → Shreyash | first `key_numbers` dict for the `[KN]` placeholders | ◐ Devansh's part in `outputs/key_numbers.md`; Mayank's keys pending |
| Hour 8 | Mayank → Devansh | `experiments_f.py` and `experiments_h.py` ready for `run_all.py` | ☐ use the key names in `INTERFACE.md` |
| Hour 8 | Devansh → Shreyash | final `key_numbers.md` | ☐ after Mayank's modules |
