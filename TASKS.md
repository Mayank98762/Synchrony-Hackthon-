# Task Board (plan v5)

Tasks come from [PROJECT_PLAN.md](PROJECT_PLAN.md) §13. Claim a task by putting your name in **Owner**, and tick it when it's merged.

- **Tracks:** A = Analysis · B = Dashboard · C = Deck. They run in parallel; B and C start on mock data and placeholders.
- **Priority:** P0 = must ship · P1 = build if on schedule · P2 = stretch.
- **Est.** is in hours. **§** points to PROJECT_PLAN.md.

**Deadline:** the deck freezes at about **5 PM IST, 24 Oct 2026** and is emailed by **7 PM**. Submission closes at 8 PM.

## Already done (23 Oct)
| ID | Task | Result |
|---|---|---|
| D01 | Profile the data and check the brief's rules | §2 data facts |
| D02 | Test the ideas from plan v4 and the blueprint | 17 experiments, X1–X17 (§4) |
| D03 | Find what the data does support | F1–F13 (§5) |
| D04 | Rewrite the plan, README and task board | v5 |
| D05 | Cross-check against a teammate's independent EDA | Core numbers match exactly; F10 strengthened, F14 and the SoW-band table added, shared definitions fixed (v5.1) |

## Track A: Analysis
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| A01 | Conda env `synchrony` + `requirements.txt`; `analysis/config.py` (paths, `SEED=42`, cutoffs, `ASSUMPTIONS`, gate thresholds); write `outputs/model_eval/selection_log.md` with every decision rule from §3, §7 and §8 **and the shared definitions in §3 rule 9** (6-month window, card-age bins, purchase, SoW filter, SoW bands, silent-attrition universe) | P0 | — | 0.5 | _TBD_ | ☐ |
| A02 | `prep.py`: load, clean, enrich with the §2 rules (signed net, `n_txn = 0` for Returns, FY / fiscal quarter, active window, `is_hsic`, reward rate, credit month) + validation asserts | P0 | A01 | 0.5 | _TBD_ | ☐ |
| A03 | `experiments.py` part 1: F1 trend, F2 Bridge (reconciliation assert), F3–F5 method and ticket-band shifts, F7, F8 missed cashback, F11 post-closure, F12 ₹ gap, F14 per-card monthly spend (MetroMart vs HSIC) | P0 | A02 | 1.5 | _TBD_ | ☐ |
| A04 | `experiments.py` part 2: heterogeneity gate (X1, X2, X14, F13) + SoW-band movement table (FY25 → FY26), slice table (X8, X9), time-aware silent-attrition null (X3), calendar-adjusted decay (X4) and onboarding (X7), X10–X13, X17, F6 ticket-size model | P0 | A02 | 1.5 | _TBD_ | ☐ |
| A05 | `closure_model.py` on the rule-9 universe (**all** open cards, including those under 6 months): snapshots with leakage asserts; B0 random, B1 recency rule, **B2 card age alone**, LR profile / transactions / all, HGB; ROC-AUC, PR-AUC, top-decile capture, 1,000-sample paired bootstrap vs B1 and B2; coefficients; closure rate by card-age bin at both cutoffs (F9, F10, X5, X6); gender slice check | P0 | A02 | 1.5 | _TBD_ | ☐ |
| A06 | `segments.py`: K-means negative control (ARI stability, FY25 → FY26 outcome separation); ₹-at-stake ranking with out-of-time check; rule segments A–F (split B into < 6m and 6–12m if their outcomes differ with a CI); size, closure rate and ₹ at stake per segment; boundary sensitivity | P0 | A04, A05 | 1.5 | _TBD_ | ☐ |
| A07 | `economics.py`: offers O1–O8 (incremental vs cannibalised cost, net value, break-even shift rate, 3 scenarios); closed-form MDE + holdout sizing per segment | P0 | A06 | 1 | _TBD_ | ☐ |
| A08 | `export.py`: `key_numbers.md`, `impact_ledger.csv` (every row tagged), `experiment_log.csv`, PNG charts for the deck (200 dpi, 16:9), all dashboard JSON from §11 (< 12MB), customer shards | P0 | A03–A07 | 1 | _TBD_ | ☐ |
| A09 | `run_all.py` + reproduction checks against the 23 Oct numbers and the exact cross-checks against both EDAs (§14) | P0 | A08 | 0.5 | _TBD_ | ☐ |
| A10 | `notebooks/story.ipynb`: narrative walk-through that imports `analysis/` | P1 | A09 | 0.5 | _TBD_ | ☐ |

## Track B: Dashboard
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| B01 | Scaffold: Vite + React 18.3 + TS + Tailwind 3.4 + ECharts 5.5 (Node from the conda env); app shell, navigation, light/dark tokens, mobile layout; Measured / Simulated / Assumed badge component | P0 | — | 1 | _TBD_ | ☐ |
| B02 | Mock JSON matching the §11 contract, so every page can be built before Track A finishes | P0 | B01 | 0.5 | _TBD_ | ☐ |
| B03 | Page 1 Story (5 KPI tiles), page 2 The decline (trend, per-card MetroMart vs HSIC spend, Bridge waterfall, method shift) | P0 | B02 | 1 | _TBD_ | ☐ |
| B04 | Page 3 "Is it a segment problem?" (slice dropdown) + page 4 Noise check (real vs simulated, re-simulate button, SoW-band movement table) | P0 | B02 | 1.5 | _TBD_ | ☐ |
| B05 | Page 5 Attrition (raw / calendar-adjusted toggle, tenure hazard, nulls) + page 6 Where the wallet went (ticket bands, Sankey) | P0 | B02 | 1.5 | _TBD_ | ☐ |
| B06 | Page 7 Expected vs found (experiment cards with verdict filter, closure-model table) | P0 | B02 | 1 | _TBD_ | ☐ |
| B07 | Page 8 Segments & offers + page 9 Offer simulator (sliders, break-even line, MDE planner, Simulated badges) | P1 | B02 | 2 | _TBD_ | ☐ |
| B08 | Page 10 Customer lookup (sharded lazy load) + page 11 Methods & assumptions | P1 | B02 | 1.5 | _TBD_ | ☐ |
| B09 | Swap mocks for real JSON; QA at phone width, both themes, zero console errors; build; publish; screenshots for the deck | P0 | A08, B03–B06 | 1 | _TBD_ | ☐ |

## Track C: Deck (required)
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| C01 | Slide template + storyline for the 12 slides in §12, with placeholder numbers marked `[KN]` | P0 | — | 1 | _TBD_ | ☐ |
| C02 | Slides 1–6 drafted from the §5 findings (data, decline, where it went, the twist) | P0 | C01 | 1 | _TBD_ | ☐ |
| C03 | Slides 7–12 (expected vs found, attrition, segments, offers, economics and pilot, roadmap and asks) + appendix | P0 | C01 | 1.5 | _TBD_ | ☐ |
| C04 | Replace every `[KN]` with values from `key_numbers.md`; insert charts from `outputs/charts/` and dashboard screenshots | P0 | A08, B09 | 1 | _TBD_ | ☐ |
| C05 | Review: brief compliance (all 4 objectives + assumptions), every number traceable, hypothesis verdicts shown; export the PDF | P0 | C04 | 0.5 | _TBD_ | ☐ |
| C06 | Email the PDF to analyticshiring@syf.com (subject = roll number only; attach the file, no Drive link) | P0 | C05 | 0.1 | _TBD_ | ☐ |

## Stretch (P2)
| ID | Task | Depends on | Est. |
|---|---|---|---|
| S01 | Non-cardholder acquisition at checkout (6,836 customers; payment-mix benchmark) | A06 | 0.5 |
| S02 | Fairness slice report (closure-model error rates by gender and age band) as an appendix slide | A05 | 0.5 |
| S03 | Prime trial economics (O7): extra cashback a Non-Prime customer would earn as Prime | A07 | 0.5 |

## Verification checklist (before the deck freezes)
- [ ] `python analysis/run_all.py` passes every assert: data checks, Bridge reconciles, segment sizes add up, ledger fully tagged, snapshot dates leak-free.
- [ ] Reproduction checks pass (PROJECT_PLAN §14 tolerances), and the exact cross-checks against both EDAs match.
- [ ] Every script, chart and slide uses the §3 rule-9 definitions.
- [ ] `selection_log.md` was committed before the results files.
- [ ] Simulator at 0% shift = baseline; break-even checked by hand for one offer.
- [ ] 3 customers traced from raw rows → segment → offer → dashboard lookup.
- [ ] Every number in the deck is in `key_numbers.md`.
- [ ] Dashboard: all pages on real data, phone width, both themes, no console errors.

## Cut order if behind schedule
B08 → the live simulation in B04 (keep static charts) → B07 simulator (keep a static table) → the whole dashboard (PNG charts only).
**Never cut:** A01–A09, C01–C06.
