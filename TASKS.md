# Task Board (plan v5.3, final)

Tasks come from [PROJECT_PLAN.md](PROJECT_PLAN.md) §13. Claim a task by putting your name in **Owner**, and tick it when it's merged.

- **Tracks** (A and C start immediately; B starts from the 23 Oct numbers):
  - **A** = Analysis;
  - **B** = Charts & slide polish;
  - **C** = Deck.
- **The dashboard** (W-tasks) is built by Claude after A08 and is dropped if it isn't ready by the freeze.
- **Priority:** P0 = must ship · P1 = build if on schedule · P2 = stretch.
- **Est.** is in hours. **§** points to PROJECT_PLAN.md.
- **Done:** ☑ = done · ◐ = partly done (the note says what's left) · ☐ = not started. Owners follow [TEAM_SPLIT.md](TEAM_SPLIT.md).

**Status (23 Oct, night):** Devansh's pipeline foundation, ML experiments, closure model, segmentation and `run_all.py` are done on the `devansh` branch. `python analysis/run_all.py`: 18 checks pass, 0 fail, 21 pending on Mayank's and Shreyash's keys (names in `analysis/INTERFACE.md`). Handoff notes: `HANDOFF_MAYANK.md`, `HANDOFF_SHREYASH.md`.

**Status (24 Oct, Mayank):** `experiments_f.py`, `experiments_h.py`, the slide 4–7 charts and content, the notebook and the §14 verification are done and merged to `main`. With them, `run_all.py` reports 37 checks pass, 0 fail, 2 pending (Shreyash's `f12_gap`, `f15_reward_rate_fy26`). `python -m analysis.verify` reports 0 blocking failures.

**Deadline:** the deck freezes at about **5 PM IST, 24 Oct 2026** and is emailed by **7 PM**. Submission closes at 8 PM. **The deck decides this hackathon.**

## Already done (23 Oct)
| ID | Task | Result |
|---|---|---|
| D01 | Profile the data and check the brief's rules | §2 data facts |
| D02 | Test the ideas from plan v4 and the blueprint | 17 experiments, X1–X17 (§4) |
| D03 | Find what the data does support | F1–F14 (§5) |
| D04 | Rewrite the plan, README and task board | v5 |
| D05 | Cross-check against a teammate's independent EDA | Core numbers match exactly; F10 strengthened, F14 and the SoW-band table added, shared definitions fixed (v5.1) |
| D06 | Apply the external review | v5.2: see the PROJECT_PLAN header for the full list. Silent attrition reframed as universal; literal 2×2 segment answer; reward visibility as the hero offer; hypotheses labelled; interchange view (F15); pre-registration claim dropped; dashboard cut to 4 pages |
| D07 | Final planning fixes | v5.3: economics net of rewards (F15, §8) with "never breaks even" allowed; O6 cut to 3%, co-funded; purchase frequency counts all MetroMart purchases so young cards can reach the top tercile; 2×2 slide shows SoW is flat across boxes; slide 10 shows 3 offers; "no fees" clue used |

## Track A: Analysis
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| A01 | Conda env `synchrony` + `requirements.txt`; move the 4 case CSVs from the repo root into `data/`; `analysis/config.py` (paths, `SEED=42`, cutoffs, `ASSUMPTIONS` with the §8 scenario table: interchange 1.5 / 1.75 / 2%, revolve income 0 / 1 / 2%, MetroMart co-funding 0 / 50 / 50%; gate thresholds); write `outputs/model_eval/selection_log.md` with every decision rule from §3, §7 and §8 **and the shared definitions in §3 rule 9** (6-month window, card-age bins, purchase, purchase frequency **over all MetroMart purchases**, SoW filter, SoW bands, silent-attrition universe, net margin per ₹) | P0 | — | 0.5 | Devansh | ☑ versions pinned; CSVs copied (originals kept in `Synchrony_files/`) |
| A02 | `prep.py`: load, clean, enrich with the §2 rules (signed net, `n_txn = 0` for Returns, FY / fiscal quarter, active window, `is_hsic`, reward rate, credit month) + validation asserts | P0 | A01 | 0.5 | Devansh | ☑ interface in `analysis/INTERFACE.md` |
| A03 | `experiments.py` part 1: F1 trend, F2 Bridge (reconciliation assert), F3–F5 method and ticket-band shifts, F7, F8 (Prime G+E left on the table + context total), F11 post-closure, F12 ₹ gap, F14 per-card monthly spend, F15 loss in the bank's terms (gross interchange, rewards HSIC would have paid at 1.39%, net margin at 0% and 50% co-funding, per 10,000 cardholders) | P0 | A02 | 1.5 | Mayank (F1–F14); Shreyash (F12, F15) | ☑ Mayank's F1–F11, F13, F14 (merged); Shreyash's F12, F15 done on `shreyash`: gap ₹33.4M, FY26 reward rate 1.399% from the pipeline, both checks pass |
| A04 | `experiments.py` part 2: heterogeneity gate (X1, X2, X14, F13) + SoW-band movement table, slice table (X8, X9), time-aware silent-attrition null (X3), calendar-adjusted decay (X4) and onboarding (X7), X10–X13, X17, F6 ticket-size model | P0 | A02 | 1.5 | Devansh (gate, X1, X2, X7, X15, X16); Mayank (rest) | ☑ Devansh's part in `experiments_ml.py`; Mayank's X3, X4, X8–X14, X17, F6 and F13 in `experiments_h.py` / `experiments_f.py` (merged) |
| A05 | `closure_model.py` on the rule-9 universe (**all** open cards, including those under 6 months): snapshots with leakage asserts; B0 random, B1 recency rule, **B2 card age alone**, LR profile / transactions / all, HGB; ROC-AUC, PR-AUC, top-decile capture, 1,000-sample paired bootstrap vs B1 and B2; coefficients; closure rate by card-age bin at both cutoffs (F9, F10, X5, X6); gender slice check | P0 | A02 | 1.5 | Devansh | ☑ card-age rule ships (AUC 0.672); X5 verdict: usage adds nothing beyond card age |
| A06 | `segments.py`: K-means negative control (ARI stability, FY25 → FY26 outcome separation); **frequency × card-age 2×2** + segments A–F (§7), frequency over all MetroMart purchases; independence assert (young vs mature top-tercile share within ±3pp); per box: size, FY26 SoW, 6-month closure rate, non-HSIC ₹, Prime share, with CIs; < 6m vs 6–12m split if outcomes differ; boundary sensitivity at ±10% | P0 | A04, A05 | 1.5 | Devansh | ☑ segment A = 5,903 (net spend after close > 0) vs F11's 6,227 |
| A07 | `economics.py`: offers O1–O8 with O3 first, O6 at 3% (net margin per ₹ after rewards and co-funding, retention value for O6/O7, incremental vs cannibalised cost, break-even shift rate per scenario, returning `never` when an offer can't pay back); closed-form MDE + holdout sizing per segment; map each pilot arm to the hypothesis it tests (O3 → H-aware, O1 → H-imm) | P0 | A06 | 1 | Shreyash | ☑ on `shreyash`: O1–O8 by scenario incl. `never`, break-even revolve with and without co-funding, O7 retention value, MDE per box, self-checks; charts `11_net_margin_waterfall.png`, `11_breakeven.png` |
| A08 | `export.py`: `key_numbers.md`, `impact_ledger.csv` (every row tagged), `experiment_log.csv`, PNG charts for the deck (200 dpi, 16:9), dashboard JSON for the 4 pages (< 2MB) | P0 | A03–A07 | 1 | Devansh | ◐ `key_numbers.md`/`.json`, `impact_ledger.csv`, `experiment_log.csv` done; slide 8–9 PNGs and the dashboard JSON (`dashboard/public/data/`, 35 kB, `analysis/dashboard_data.py`) built by `run_all.py` |
| A09 | `run_all.py` + reproduction checks against the 23 Oct numbers and the exact cross-checks against both EDAs (§14) | P0 | A08 | 0.5 | Devansh | ◐ built and run: 18 pass, 0 fail, 21 pending; final run once Mayank's and Shreyash's modules land |
| A10 | `notebooks/story.ipynb`: narrative walk-through that imports `analysis/` | P2 | A09 | 0.5 | Mayank | ☑ executed without errors (merged) |

## Track B: Charts & slide polish
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| B01 | Chart style guide: palette (HSIC as the hero colour), fonts, 16:9 sizes, badge style for Measured / Simulated / Assumed / Hypothesis | P0 | — | 0.5 | Shreyash | ☑ `analysis/style.py` on `shreyash`: the validated reference palette (same as the fallback), an ordinal scenario ramp, badge colours |
| B02 | Draft charts for slides 4–8 from the 23 Oct numbers: SoW trend, per-card spend, Bridge waterfall, method shift by ticket band, slice lines, gate + band table, silent-attrition null, raw vs adjusted decay, closure by card age | P0 | B01 | 2 | Mayank (slides 4–7); Devansh (slide 8) | ◐ slides 4–7 done (Mayank, `analysis/charts_story.py`, 12 charts); slide 8 done (Devansh, `analysis/charts_ml.py`: closure by card age, closures per quarter, model AUC) |
| B03 | Draft charts for slides 9–11: K-means control, the 2×2 with sizes and outcomes, offer slide with 3 offers (O3, O1, O2), net-margin waterfall (interchange → rewards → co-funding), break-even by scenario incl. `never`, pilot design | P0 | B01 | 1.5 | Devansh (slide 9); Shreyash (slides 10–11) | ☑ slide 9 (Devansh); slides 10–11 charts on `shreyash` (Shreyash) |
| B04 | Swap the drafts for pipeline charts from `outputs/charts/`; visual QA | P0 | A08, B02, B03 | 1 | Each owner, own slides | ◐ slides 4–7: pipeline charts, visually checked; restyle with `style.py` when it lands |
| B05 | Slide polish and consistency pass: labels, badges, units, number formatting | P0 | B04, C03 | 1 | Shreyash | ☐ |

## Track C: Deck (required)
| ID | Task | P | Depends on | Est. | Owner | Done |
|---|---|---|---|---|---|---|
| C01 | Slide template + storyline for the 12 slides in §12, with placeholder numbers marked `[KN]` | P0 | — | 1 | Shreyash | ◐ storyline condensed to 6 slides + an optional appendix (organizers' 5–6 slide limit, to confirm); `deck/build_deck.js` builds the .pptx from `key_numbers.json` |
| C02 | Slides 1–6: executive summary leading with *universal* silent attrition, data and rules, the decline, where it went (H-imm labelled), silent attrition is universal | P0 | C01 | 1 | Shreyash (1–3); Mayank (4–6) | ◐ slides 1–3 content in `deck/slides_01-03_10-12.md` (Shreyash); slides 4–6 in `deck/slides_04-07.md` (Mayank) |
| C03 | Slides 7–12 + appendix: three common hypotheses tested, closures, who to prioritise (2×2), offers with reward visibility as the hero, economics and pilot, roadmap and asks; full 17-row table in the appendix | P0 | C01 | 1.5 | Mayank (7); Devansh (8–9); Shreyash (10–12, appendix) | ◐ slide 7 in `deck/slides_04-07.md` (Mayank); 8–9 in `deck/slides_08_09.md` (Devansh); 10–12 + appendix in `deck/slides_01-03_10-12.md` (Shreyash) |
| C04 | Replace every `[KN]` with values from `key_numbers.md`; insert the final charts and (if built) dashboard screenshots | P0 | A08, B04 | 1 | Shreyash | ☐ |
| C05 | Review against the brief and the plan:<br>• all 4 objectives covered, assumptions stated, every number traceable;<br>• silent attrition framed as universal (never "rejected");<br>• every "why" labelled Hypothesis;<br>• no mention of v4, the blueprint or pre-registration.<br>Then export the PDF | P0 | C04, B05 | 0.5 | Shreyash | ☐ |
| C06 | Email the PDF to analyticshiring@syf.com (subject = roll number only; attach the file, no Drive link) | P0 | C05 | 0.1 | Shreyash | ☐ |

## Dashboard (Devansh with Claude, optional)
Live in `dashboard/`; see README → Getting started, step 4.
| ID | Task | P | Depends on | Est. | Done |
|---|---|---|---|---|---|
| W01 | Scaffold Vite + React 18.3 + TS + Tailwind 3.4 + ECharts 5.5 (Node from the conda env); shell, navigation, light/dark tokens, badges | P1 | A08 | 0.5 | ☑ Vite 5.4 + React 18.3 + TS + ECharts 5.5 (plain CSS on the taste-skill app base instead of Tailwind) |
| W02 | Page 1 Story + page 2 "Is it a segment problem?" | P1 | W01 | 1 | ☑ |
| W03 | Page 3 Silent attrition & closures (raw / adjusted toggle) + page 4 Who to prioritise & offers (2×2, break-even sliders) | P1 | W01 | 1.5 | ☑ break-even sliders replaced by a measured shift simulator until `economics.py` lands |
| W04 | QA (phone width, both themes, no console errors); publish; screenshots for slide 12 | P1 | W02, W03 | 0.5 | ◐ QA done: taste-skill lint 0 fail, inspector 0 fail / 0 warn at 1440, 768, 390 on all 4 pages; publish and slide-12 screenshots left |

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
- [ ] Decision rules in `selection_log.md` were fixed before the final run and not changed afterwards.
- [ ] Simulator at 0% shift = baseline; break-even and the net-margin line checked by hand for one offer; a loss-making test offer returns `never`.
- [x] Young vs mature top-tercile frequency share within ±3pp (2×2 axes independent): 31.1% vs 30.6%, asserted in `segments.py`.
- [x] 3 customers traced from raw rows → segment → offer: one closed-and-shopping (A), one young card (B), one high-frequency mature card (D), all matching `segments.assign` (`outputs/verification/verification_report.md`).
- [ ] Every number in the deck is in `key_numbers.md`.
- [ ] Deck wording:
  - [ ] silent attrition is "universal", never "rejected";
  - [ ] every "why" is labelled Hypothesis;
  - [ ] gross interchange never appears without the net-of-rewards figure;
  - [ ] no v4, blueprint or pre-registration mentions.

## Cut order if behind schedule
1. The dashboard (W01–W04).
2. A10, the notebook.
3. Appendix detail beyond the 17-row table.

**Never cut:** A01–A09, B01–B05, C01–C06.
