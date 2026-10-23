# Task Board

Tasks are taken from [PROJECT_PLAN.md](PROJECT_PLAN.md) §13. To claim a task, put your name in the **Owner** column, then tick it off when it's merged.

- **Priority:** P0 = must ship · P1 = build if on schedule · P2 = stretch.
- **Est.** is in hours.
- **§** points to the notebook section listed in PROJECT_PLAN.md §5.

**Deadline:** the deck is frozen at about **5 PM IST, 24 Oct 2026**, and emailed by **7 PM**. The submission closes at 8 PM.

## Phase 1: Core analysis (H1–H4) — Step 1, about 4h
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T01 | §0 Config: paths, `SEED=42`, cutoffs (2025-07-31 / 2026-01-31 / 2026-07-31), `ASSUMPTIONS` dict; write `selection_log.md` with every rule fixed in advance for C1–C4 | P0 | — | 0.5 | _TBD_ | ☐ |
| T02 | §1 Load, clean, enrich: signed `net_amt`, `n_txn`=0 for Returns, FY/month/half, `active` window, `is_hsic`, `reward_rate`, `reward_credit_month`, joins to the lookup tables | P0 | T01 | 0.5 | _TBD_ | ☐ |
| T03 | §2 Validation asserts (unique IDs, codes mapped, Returns have null n_txn, close ≥ open, HSIC only in the active window, gross − returns = net) + threshold sensitivity table (#20) | P0 | T02 | 0.5 | _TBD_ | ☐ |
| T04 | §3 Portfolio SoW: by month/FY, category × membership heatmap, cohort/age/limit/APR bands (M1) | P0 | T03 | 0.5 | _TBD_ | ☐ |
| T05 | §4 SoW Bridge: exact additive breakdown (leavers / stayers by method / joiners), with a reconciliation assert (#1, H1) | P0 | T04 | 1 | _TBD_ | ☐ |
| T06 | §5 Switching: dominant method by FY, transition matrix for the Sankey, switch timing (#5, H2) | P0 | T05 | 0.5 | _TBD_ | ☐ |
| T07 | §6 Reward paradox + missed cashback per customer (#2, H3) | P0 | T04 | 0.5 | _TBD_ | ☐ |
| T08 | §7 Null model for zero-HSIC at 3 cutoffs, with CI (#21); pre-closure decay curve (#4); vintage curves (#12) (H4) | P0 | T03 | 1 | _TBD_ | ☐ |

## Phase 2: Experiments — Steps 2–4, about 8h
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T09 | §8 `build_snapshot(cutoff, lookback=12m, horizon=6m)` with leakage asserts (max feature date ≤ cutoff < min label date) | P0 | T03 | 1 | _TBD_ | ☐ |
| T10 | §9 **C2** decline detection: D0–D3, semi-synthetic recovery (k = 25/50/75/100), placebo test, predictive validity; pick the winner using the pre-set rule | P0 | T09 | 1 | _TBD_ | ☐ |
| T11 | §9 C2 failure analysis: recall by activity level, profile of placebo false positives, ₹ vs row-count mismatch → **minimum-evidence rule** | P0 | T10 | 0.5 | _TBD_ | ☐ |
| T12 | §10 Attrition classes (Explicit → Silent [null-model confident] → Decliner [C2 winner] → Never-activated → Stable/Grower → Insufficient evidence) | P0 | T10, T11 | 0.5 | _TBD_ | ☐ |
| T13 | §11 **C1** models B0, B1, M1 (LR), M2 (HGB): CV tuning, test once, PR-AUC / top-decile capture / Brier / calibration, 1,000-sample bootstrap with paired differences vs B1, selection rule | P0 | T09, T10 | 2 | _TBD_ | ☐ |
| T14 | §11 C1 explanations (odds ratios with CI, permutation importance, partial dependence, reason codes) + failure analysis (FN-sudden/sparse/new, FP-silent/noise, slice metrics, gender fairness check, PSI drift, 3 examples per type) | P0 | T13 | 1 | _TBD_ | ☐ |
| T15 | §11 C1 extra models M3 (Random Forest), M4 (Cox PHReg + Schoenfeld check) | P1 | T13 | 1 | _TBD_ | ☐ |
| T16 | §12 **C3** segmentation S0–S3 + explainer trees: gates (ARI ≥ 0.7, size 3–50%, fidelity ≥ 85%), outcome separation with CI, targeting efficiency, actionability, internal indices; selection rule / hybrid | P0 | T10, T12 | 1.5 | _TBD_ | ☐ |
| T17 | §12 C3 failure analysis: contradictions, boundary sensitivity at ±5pp, purity, check that clusters aren't just spend levels | P0 | T16 | 0.5 | _TBD_ | ☐ |
| T18 | §13 Next-Best-Offer engine: offer library, best expected net value per customer, 10% holdout per segment, evidence flag → `customer_scores.csv` | P0 | T13, T16 | 0.5 | _TBD_ | ☐ |

## Phase 3: Economics, impact & exports — Step 5, about 2.5h
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T19 | §14 **C4** offer economics O0–O4 (simulated): incremental vs cannibalised cost, net value, ROI, break-even shift rate, tornado sensitivity | P0 | T18 | 1 | _TBD_ | ☐ |
| T20 | §15 Big-ticket financing gap (#13), seasonality calendar (#14), MDE baselines per segment (#10) | P1 | T16 | 0.5 | _TBD_ | ☐ |
| T21 | §16 Impact Ledger: every number tagged Measured / Simulated / Assumed; scenarios; break-even; pilot design | P0 | T13, T19 | 0.5 | _TBD_ | ☐ |
| T22 | §17 `iteration_log.md` (only real triggers: fired or not fired) + `failure_atlas.csv` | P0 | T11, T14, T17, T19 | 0.5 | _TBD_ | ☐ |
| T23 | §18 PNG charts (PROJECT_PLAN §11 list), `key_numbers.md`, dashboard JSON (size budget < 12MB) | P0 | T05–T22 | 1 | _TBD_ | ☐ |

## Phase 4: Deck (required) — Step 6, about 3h
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T24 | Build the about-18-slide deck following the storyline (PROJECT_PLAN §11). Every number comes from `key_numbers.md` / `impact_ledger.csv` | P0 | T23 | 2 | _TBD_ | ☐ |
| T25 | Review: each hypothesis marked supported / rejected / partly; assumptions slide; appendix; export the PDF | P0 | T24 | 0.5 | _TBD_ | ☐ |
| T26 | Email the PDF to the organisers (subject = roll number only; no Google Drive) | P0 | T25 | 0.1 | _TBD_ | ☐ |

## Phase 5: Dashboard (optional) — Steps 7–8, about 8h
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T27 | Dashboard shell (vanilla JS + ECharts 5.5.0 pinned, light/dark, mobile) + tabs 1 Story, 2 Why SoW fell, 3 Attrition | P1 | T23 | 1.5 | _TBD_ | ☐ |
| T28 | Tabs 4 Early warning, 5 Segments & offers, 6 Model Lab (model toggle, Failure Atlas, iteration log) | P1 | T27 | 1.5 | _TBD_ | ☐ |
| T29 | Tabs 9 Impact & Operations, 10 Methods & trust | P1 | T27 | 1 | _TBD_ | ☐ |
| T30 | Tab 7 Customer 360 (lazy-load `txns.json`) | P1 | T28 | 1.5 | _TBD_ | ☐ |
| T31 | Tab 8 Simulators: SoW, reward what-if, campaign planner — every output carries a "Simulated" badge | P1 | T28 | 1.5 | _TBD_ | ☐ |
| T32 | Publish as a private Artifact; add screenshots and the link to the deck | P1 | T27–T31 | 0.5 | _TBD_ | ☐ |

## Phase 6: Stretch (P2)
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| T33 | Prime + card bundle economics (#16) | P2 | T07 | 0.5 | _TBD_ | ☐ |
| T34 | Non-cardholder acquisition lookalikes (#17) | P2 | T07 | 0.5 | _TBD_ | ☐ |
| T35 | Reward-credit timing study (#19) | P2 | T04 | 1.5 | _TBD_ | ☐ |

## Verification checklist (before the deck freezes)
- [ ] Restart & Run All passes every assert: the Bridge reconciles, leakage dates are correct, segment counts add up to the universe, and no Impact Ledger row is untagged.
- [ ] `selection_log.md` is older than every results file, and the chosen methods match its rules.
- [ ] Sanity checks:
  - [ ] B0 PR-AUC ≈ the base rate.
  - [ ] D0's placebo false-positive rate is above D1's and D2's.
  - [ ] Simulators at 0% shift reproduce the baseline.
  - [ ] Break-even worked out by hand for one segment.
- [ ] Cross-checks: SoW is 28.9% (FY25) and 19.5% (FY26); #21 is 62.7% vs 43.5% at 2026-01-31.
- [ ] 3 customers spot-checked against their raw rows.
- [ ] Every number in the deck can be traced to `key_numbers.md` or `impact_ledger.csv`.

## Cut order if behind schedule
P2 → T15 (M3/M4) → T30–T31 → the whole dashboard → C4 cut down to O0/O1/O3.
**Never cut:** T01–T14, T16–T19, T21–T26.
