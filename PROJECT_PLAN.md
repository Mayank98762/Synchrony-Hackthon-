# MetroMart–HSIC Silent Attrition & Share of Wallet: Project Plan (v5)

> Synchrony Analytics Hackathon 2026. **Required deliverable:** slides as a PDF, emailed to analyticshiring@syf.com by **8:00 PM IST, 24 Oct 2026**. The subject line is the roll number only. Attach the file; do not use Google Drive.
> v5 replaces v4 and `synchrony_hackathon_strategy_blueprint.md`. Both earlier plans were tested against the data on 23 Oct, and most of their core ideas failed. §4 records what failed and why. That record is now part of the pitch.

## Contents
1. [The answer in one paragraph](#1-the-answer-in-one-paragraph)
2. [Brief rules & definitions](#2-brief-rules--definitions)
3. [Evaluation protocol](#3-evaluation-protocol)
4. [Experiment log: what we expected vs what we found](#4-experiment-log-what-we-expected-vs-what-we-found)
5. [What the data does support](#5-what-the-data-does-support)
6. [USPs](#6-usps)
7. [Segmentation (brief item 3)](#7-segmentation-brief-item-3)
8. [Offers & economics (brief item 4)](#8-offers--economics-brief-item-4)
9. [Assumptions & limitations](#9-assumptions--limitations)
10. [Architecture](#10-architecture)
11. [Dashboard (UI)](#11-dashboard-ui)
12. [Deck](#12-deck)
13. [Schedule, tracks & cut order](#13-schedule-tracks--cut-order)
14. [Verification](#14-verification)

---

## 1. The answer in one paragraph

HSIC's Share of Wallet at MetroMart fell from **28.9% in FY25 to 19.5% in FY26**, and it fell at the same rate for **every** kind of customer: Prime and Non-Prime, every age, credit limit, APR band, card vintage and category. Statistically, individual customers don't differ in how often they reach for the card. Usage varies between customers no more than coin flips would, and a customer's share this year predicts nothing about next year. So there is no hidden group of "low-SoW customers" to find. **HSIC has a product problem, not a targeting problem.** The card is losing ground mainly to **Cash/UPI**, which took 47% of the lost share, across every ticket size. Our recommendation therefore has three layers:
1. **Fix the product for everyone:** instant cashback at the till, reward visibility at checkout, and the card on UPI.
2. **Trigger offers at the moment of purchase**, using the one real behavioural signal: ticket size.
3. **Target only groups defined by traits that actually persist:** closed cards whose owners still shop (₹91.2M of spend after closure) and first-year cardholders, whose closure rate is 3× that of mature cards.

Every claim is backed by a test in §4–§5, and every test has a baseline or a null model.

---

## 2. Brief rules & definitions

| Rule (from the brief) | How we implement it |
|---|---|
| SoW = HSIC spend at MetroMart ÷ total spend at MetroMart | Always a **ratio of sums** in ₹, never an average of per-customer ratios |
| Net, not gross | `net = +amount` for a Sale, `−amount` for a Return |
| Returns count as 0 transactions | `n_txn = 0` for Return rows (they are null in the raw data) |
| Only while the card is active | `open_date ≤ txn_date ≤ close_date`, inclusive at both ends; a null close date means the card is still open |
| Fiscal year Aug–Jul | FY25 = Aug 2024–Jul 2025, FY26 = Aug 2025–Jul 2026. Fiscal quarters: Q1 = Aug–Oct |
| Category / payment lookups | Joined on `Category_Code` / `Payment_Code`. HSIC = code 3 |
| Rewards credited the following month | Derived reward = HSIC net × rate (Prime: 5% Grocery, 3% Electronics, 1% other; Non-Prime: 1%), booked in month + 1 |

**Data facts (all verified on 23 Oct 2026)**
- **Customers:** 45,000. 6,836 have never held a card; 7,664 cards are closed. 126 cards open after the data ends, and some close dates run to 2026-08-05. Both are handled by the active-window rule.
- **Transactions:** 444,118 rows from 2024-08-01 to 2026-07-31. 44,814 are Returns, all with null `Number_of_Transactions`. 21,235 rows sit at exactly ₹9,999.99 (a cap).
- **Integrity:** no duplicate IDs and no orphan rows. No HSIC transaction falls outside an active card window.
- **Sparsity:** about 9.9 rows per customer over two years, i.e. 0.82 rows per 60 days.

---

## 3. Evaluation protocol

These rules apply to every experiment, whether it was already run (§4) or is still planned.

1. **The decision rule comes before the result.** Each hypothesis states in advance what counts as supported. Rules live in `outputs/model_eval/selection_log.md`, which is committed before the notebook produces results.
2. **Every effect is compared with a null.** Nulls are calendar-matched, so a portfolio-wide trend cannot pose as a customer-level effect. This one rule overturned four of our earlier ideas (§4).
3. **Heterogeneity gate.** Before any customer-level score or segment is used, it must show:
   - **variance ratio** (observed spread of per-customer HSIC share ÷ spread expected from chance alone) clearly above 1;
   - **split-half reliability** (odd vs even transactions in the same year) clearly above 0;
   - **year-over-year persistence** of r ≥ 0.2.

   A variable that fails the gate is not used for targeting.
4. **Out-of-time validation for prediction.** Train on the 2025-07-31 snapshot, test once on the 2026-01-31 snapshot, and score at 2026-07-31. Features come from the 12 months up to the cutoff; labels from the 6 months after it.
5. **Baselines are mandatory.** Every model is compared against a simple rule and against random. A model must beat the rule with a bootstrap CI that excludes 0, or we ship the rule.
6. **Uncertainty is reported.** 95% CIs (bootstrap or normal approximation) on every headline comparison.
7. **Every ₹ figure is labelled** Measured, Simulated or Assumed, in the deck and on the dashboard.
8. **Gender is never a model feature.** It is used only for the fairness slice check.

---

## 4. Experiment log: what we expected vs what we found

Ideas came from three sources: **v4** (the previous project plan), **BP** (the strategy blueprint) and **R** (our own review). Every row below was tested on the full data on 23 Oct 2026. The notebook must reproduce each number (see §14).

| # | Source | What we expected | Test | What we found | Verdict |
|---|---|---|---|---|---|
| X1 | v4 C3, BP Model 2 | Clustering customers on SoW would reveal low-SoW segments | Heterogeneity gate on per-customer HSIC share | Variance ratio **1.001** (FY25) and **0.996** (FY26): exactly the spread chance produces. Split-half r = **−0.007** (n = 22,320). FY25 → FY26 r = **0.00** | **Rejected.** SoW clusters would be clusters of noise |
| X2 | v4 C2 | A detector could flag individual customers whose SoW is declining | Same gate | Every customer's usage falls at the portfolio rate; nothing customer-specific remains to detect | **Rejected.** Dropped |
| X3 | v4 #21 | Silent attrition is real: more cardholders go quiet than chance predicts | Zero-HSIC rate in the next 6 months vs two nulls, at 3 cutoffs | Fixed-share null: excess **+21.6 / +17.5 / +21.5pp**. Time-aware null: excess **+0.7 / +0.1 / +0.0pp** (CI ±1pp) | **Rejected.** The "excess" is the portfolio trend. Customer-level silent attrition beyond the trend is zero |
| X4 | v4 #4 | HSIC use decays in the months before a card closes | Closers' HSIC share by months before closure, raw vs calendar-adjusted | Raw: 27.0% at −12 months → 20.5% at closure, which *looks* like decay. Calendar-adjusted excess: between −1.4 and +2.3pp with no trend | **Rejected.** Closures cluster late in the window, when everyone's SoW is lower |
| X5 | v4 C1-B1, BP Model 1 | Recent card usage predicts closure | Out-of-time test, 25,468 cards, 1,246 closures | Recency rule ROC-AUC **0.519**. Usage features only: **0.523** (≈ random). Profile features: **0.619** | **Rejected.** Usage carries no closure signal |
| X6 | v4 C1-M2 | Gradient boosting beats logistic regression | Same test | HGB 0.606 vs LR 0.620 ROC-AUC; top-decile capture 18.4% vs 18.5% | **Rejected.** Ship LR |
| X7 | v4 #12 | New cards show an onboarding usage cliff | Calendar-adjusted HSIC share by months since opening | Within ±1.5pp for months 0–18, no trend | **Rejected for usage.** But closure *is* tenure-driven (§5) |
| X8 | BP H2 | Non-Prime members drop off because 1% is too little | SoW by membership by quarter; logistic model of HSIC use | Non-Prime 32.8 → 15.5%, Prime 32.7 → 15.6%. Prime coefficient **0.000** | **Rejected.** Also confirms the reward paradox (§5) |
| X9 | BP H4 | Customers keep Grocery on HSIC and move other categories away | SoW by category | 23–24% in all 10 categories; each falls ≈ 32 → 15% | **Rejected** |
| X10 | BP H3 | Credit limits bind during sale events | Monthly MetroMart spend ÷ card limit | Median **1.2%**, maximum 26.5%. Zero customer-months reach 50% | **Rejected** |
| X11 | BP H3 | Festive peaks (Diwali) drive switching | Monthly sales index | 92–108 (mean = 100), no festive spike | **Rejected** |
| X12 | R | MetroMart's own Wallet is cannibalising the card | Stayers' method shift; non-cardholders' method shift | Wallet took only **14%** of HSIC's loss, and Wallet share is *falling* for non-cardholders (48.8 → 44.8%) | **Rejected.** Cash/UPI is the winner |
| X13 | v4 S1 | A "never-activated" segment exists | Share of active cardholders with zero HSIC rows vs chance | 26.9% observed vs 25.7% expected by chance | **Rejected.** Mostly chance |
| X14 | R | Ticket-size or category mix would make good segments (big-ticket shopper, grocery shopper) | FY25 → FY26 persistence | Big-ticket share r = **0.008**; Grocery + Electronics share r = **0.000** | **Rejected as segments.** Ticket size works at the *transaction* level instead (§5) |
| X15 | BP | Predict "SoW drops > 20% in the next 60 days" | Rows available per window | 0.82 rows per customer per 60 days, so SoW is undefined for most customers | **Infeasible** |
| X16 | BP Model 3 | Uplift model for offer response | Data audit | No historical offers, so no treated or control group | **Infeasible.** Replaced by a pilot design (§8) |
| X17 | v4 | Returns behave differently by payment method | Return rate by method | 10.1% for every method | **No signal** |

**What the failures taught us (this is slide 7 of the deck)**
1. **Calendar-adjust everything.** When the whole portfolio drifts, any customer-level metric that ignores the drift will "find" attrition, decay and decliners that aren't there (X3, X4).
2. **Test whether customers differ before segmenting them.** Two plans, and most competing teams, start with K-means on SoW. The heterogeneity gate takes minutes and showed that approach would have produced confident-looking noise (X1, X2, X14).
3. **When the drift is portfolio-wide, the fix is portfolio-wide.** Targeting money spent on "low-SoW customers" would land on customers chosen at random.

---

## 5. What the data does support

| # | Finding | Evidence | Label |
|---|---|---|---|
| F1 | **SoW fell 28.9% → 19.5% (FY25 → FY26)** in a straight line: 32.7% in Q1 FY25 to 15.6% in Q4 FY26, about −2.4pp per quarter | Active-window, net, ratio of sums | Measured |
| F2 | **The whole decline comes from customers who stayed.** Of −9.4pp: card closures +0.26pp, change among continuously open cards −9.54pp, new cards −0.15pp | SoW Bridge on 18,111 cards open throughout both FYs (29.2% → 19.6%) | Measured |
| F3 | **Cash/UPI is the main winner**, taking 47% of HSIC's lost share; Debit took 21%, Other Bank CC 19%, Wallet 14% | Stayers' payment-mix shift | Measured |
| F4 | **The shift to Cash/UPI is partly market-wide but much stronger for cardholders**: +4.5pp for stayers vs +1.8pp for non-cardholders | Difference in differences | Measured |
| F5 | **HSIC loses about a third of its share in every ticket band**, and Cash/UPI gains 3.5–4.4pp in every band. Shares in FY25 → FY26: | | Measured |
| | &nbsp;&nbsp;• under ₹1k: 23.3 → 15.0% | | |
| | &nbsp;&nbsp;• ₹1–3k: 27.9 → 18.3% | | |
| | &nbsp;&nbsp;• ₹3–10k: 28.8 → 19.3% | | |
| | &nbsp;&nbsp;• capped ₹9,999.99: 30.1 → 21.7% | | |
| F6 | **Ticket size is the only behavioural signal.** Within the same category and quarter, HSIC is used on 17.1% of low tickets vs 25.5% of high tickets. A model of HSIC use goes from AUC 0.592 (month only) to 0.604 (everything); every customer attribute adds ≈ 0 | Within-stratum terciles; logistic model | Measured |
| F7 | **MetroMart Wallet carries about half of all capped (₹9,999.99) purchases** (48.5 → 51.1%), even though HSIC is the product with financing | Ticket-band mix | Measured |
| F8 | **Reward paradox.** Prime members earn 5%/3% but use HSIC exactly like Non-Prime members. In FY26, Prime cardholders spent ₹47.4M on Grocery + Electronics with other methods, missing **₹1.60M** of cashback. Across all cardholders, missed cashback was **₹3.98M**, against ₹0.96M actually paid | Derived rewards | Measured |
| F9 | **Closures per open card doubled** from 1.7% a quarter (Jul–Sep 2024) to 3.4% (Apr–Jun 2026) | Closures ÷ cards open at quarter start | Measured |
| F10 | **Closure is a first-year problem.** 6-month closure rate by tenure: 8.7% (≤ 12 months), 6.4% (12–24), 4.1% (24–36), 3.1% (36–48), 2.9% (48+). Tenure is the dominant model coefficient (−0.29 standardised). The LR model captures 18.5% of closers in its top decile, 1.85× random | Out-of-time test | Measured |
| F11 | **Closed cards keep shopping.** 6,227 of 7,664 closers still shop at MetroMart, spending **₹91.2M** net after closure. Their mix after closure (Wallet 46%, Cash/UPI 28%, Debit 13%, Other CC 13%) matches non-cardholders, so HSIC's share is simply redistributed | Post-close transactions | Measured |
| F12 | **HSIC spend shrank while MetroMart spend grew.** HSIC net spend fell from ₹85.7M to ₹68.9M while active cardholder spend rose from ₹296.3M to ₹353.8M. At FY25's SoW, FY26 HSIC spend would have been about ₹102M, so the gap is **about ₹33M** | Counterfactual at constant SoW | Measured (gap is derived) |
| F13 | **Only frequency and spend persist** year to year (r = 0.44 for transaction count, 0.22 for net spend). These are the only behaviour variables allowed into segments | Persistence test | Measured |

---

## 6. USPs

Each USP exists because of a finding; none were added for show.

| # | USP | Why it's different | Built on |
|---|---|---|---|
| U1 | **The heterogeneity gate.** A three-test check (variance ratio, split-half, persistence) run before any segmentation | Most teams will cluster noise and present it confidently. We prove whether the clusters would be real, and the gate is reusable on any future data | X1, X2, X14 |
| U2 | **Time-aware silent-attrition test.** Corrects a +21pp overstatement down to 0 | Shows why silent-attrition counts mislead during a portfolio-wide decline | X3 |
| U3 | **Raw vs calendar-adjusted decay curve** (toggle on the dashboard) | The same chart tells two opposite stories, and the adjustment decides which is true | X4 |
| U4 | **SoW Bridge.** An exact split of the −9.4pp into closures, stayers and new cards, broken down by destination method | Answers "is it mix or behaviour?" in one picture: it's behaviour | F2, F3 |
| U5 | **"Target moments, not people."** Offers fire on the purchase (ticket size, basket), not on a customer label | Follows directly from the data: ticket size is the only behavioural signal, and customer traits don't persist | F6, X14 |
| U6 | **Expected-vs-found log**, with 17 rejected ideas, each with its test and number | Shows judgement, not just output. No other team will put their failed hypotheses on a slide | §4 |
| U7 | **Instant cashback at the till.** The same reward, credited at checkout instead of next month | Takes on UPI's immediacy at almost no extra cost. The brief's "credited next month" detail is the hint | F3, F4, F8 |
| U8 | **Break-even-first economics.** Every offer shows the shift rate it needs to pay for itself, which needs no response assumption | No invented response rates in the headline | §8 |

Deliberately left out: GenAI/RAG assistants, AI-written marketing copy, uplift models (no treatment data), real-time streaming and deep-learning CLV. None has supporting data, and they would look like filler to judges hiring analysts.

---

## 7. Segmentation (brief item 3)

The brief asks for "segments using a model or method to identify low-SoW customers". We answer it in three steps on one slide.

**Step 1: show the obvious method fails.** Run K-means on SoW features as a pre-registered negative control. Report:
- bootstrap stability (ARI) across 20 resamples;
- outcome separation: does the FY25 segment predict FY26 HSIC share?
- the heterogeneity gate.

Expected result: little or no separation. If it *does* separate, the gate has failed and we switch to a customer-level design. That rule goes into `selection_log.md` first.

**Step 2: answer "who is low-SoW?" honestly.** Every cardholder's expected SoW is the portfolio's current level (15.6% in Q4 FY26). So the **whole book** is low-SoW, and the useful question becomes *where the most ₹ sits on other payment methods*. We rank customers by **₹ at stake** = expected MetroMart spend × (1 − current portfolio SoW). Expected spend is predictable because spend and frequency persist (F13). The notebook validates this out of time (FY25 rank → FY26 non-HSIC ₹, top-decile capture).

**Step 3: segments built only from persistent traits** (rules applied in order; first match wins):

| Segment | Rule | Size | Why it's real | Lever |
|---|---|---|---|---|
| A. Closed, still shopping | Card closed and MetroMart spend after closure | 6,227 | ₹91.2M of post-closure spend (F11) | Win-back (O6) |
| B. First-year cardholders | Open card with tenure < 12 months | 6,297 of 30,519 open cards at 2026-07-31 | 3× the closure rate of mature cards (F10) | Onboarding protection (O7) |
| C. High-frequency established | Tenure ≥ 12 months and top tercile of transaction count | Notebook | Frequency persists (r = 0.44); largest ₹ at stake | Threshold bonus (O8) |
| D. Prime established | Tenure ≥ 12 months, Prime, not in C | Notebook | Prime status is a fixed attribute; ₹1.60M missed (F8) | Reward visibility (O3) |
| E. Everyone else open | — | Notebook | — | Product fixes only (O1–O5), no paid targeting |
| F. Non-cardholders | No card | 6,836 | — | Acquisition at checkout (stretch) |

**Segment checks:** sizes add up to the universe; each segment's FY26 outcome (closure rate, ₹ at stake) differs from the others with a CI; customers move between segments at ±10% threshold changes (boundary sensitivity).

---

## 8. Offers & economics (brief item 4)

| # | Offer | Layer | Who / trigger | Addresses | Cost model |
|---|---|---|---|---|---|
| O1 | **Instant cashback at the till**: reward applied at checkout, not on next month's statement | Product | All HSIC purchases | Immediacy vs UPI (F3, F4) | Same reward amount; cost = 1 month's time value + ops (Assumed) |
| O2 | **HSIC card on UPI** (credit card linked to UPI) | Product (strategic) | All | Cash/UPI took 47% of the loss | Partnership and network cost (qualitative) |
| O3 | **Reward visibility**: POS and receipt line "Pay with HSIC: earn ₹X on this basket"; monthly "₹ you left on the table" | Product | Prime G+E baskets first | Reward paradox (F8) | ≈ 0 incentive cost |
| O4 | **No-cost EMI on baskets ≥ ₹3,000** at MetroMart | Moment | Basket ≥ ₹3k | Wallet holds ~half of capped tickets (F7); ticket-size signal (F6) | Subvention %, co-funded by MetroMart (Assumed) |
| O5 | **Small-basket streak**: 5 HSIC purchases under ₹1,000 in a month earns a ₹50 bonus | Moment | Baskets < ₹1k | Lowest HSIC share (17.1%) | Bonus paid only above the threshold |
| O6 | **Win-back**: instant re-approval and 5% on everything for 90 days (capped) | Segment A | 6,227 closers | ₹91.2M post-closure spend | Boost cost on recovered spend |
| O7 | **First-year protection**: activation milestone (3 swipes in 60 days) plus a 3-month Prime trial for Non-Prime | Segment B | 6,297 new cards | 3× closure risk (F10) | Trial cost co-funded by MetroMart (Assumed) |
| O8 | **Threshold bonus**: extra 1% only on HSIC spend above the customer's own trailing 3-month average | Segment C | High-frequency | Avoids paying for spend that would happen anyway | Bonus on the increment only |

**Economics (per offer, in the notebook and the dashboard simulator)**
- **Value per ₹ shifted to HSIC** = interchange % + other income % (Assumed, three scenarios).
- **Cost** is split into incentive on *incremental* spend vs incentive on spend that would have happened anyway (cannibalisation).
- **Break-even shift rate** = the share of eligible non-HSIC ₹ that must move for net value ≥ 0. This is assumption-light and is the headline number.
- **Scenario range** (conservative / base / optimistic) is labelled **Simulated**.
- **Headline wording:** "₹33M of HSIC spend lost (measured). Offer X pays back if Y% of eligible spend moves (break-even). Base case ₹Z (simulated)." Never "we will recover ₹Z".

**Pilot design (turns simulated numbers into measured ones)**
- A randomised 10% holdout per offer and segment.
- Because HSIC use behaves like a coin flip per purchase, the MDE has a closed form: MDE = 2.8·√(2p(1−p)/n) for n purchases per arm, at 80% power and α = 0.05. The notebook computes it per segment.
- Read out after 3 months on SoW, active rate, closure rate and net value.
- **Scale only if** the CI of the lift excludes 0 and net value > 0.

---

## 9. Assumptions & limitations

**Data**
- Amounts are in ₹.
- Prime status is a static snapshot.
- Travel and Bill Payments earn the "other eligible" 1%.
- A Return reduces the payment method on its own row. Returns are not linked to the original sale.
- `Number_of_Transactions` counts purchases within a row and is used only for frequency.
- Cards are active on both their open and close dates.
- Non-cardholders are excluded from SoW and used only as a benchmark.

**Modelling**
- 12-month lookback, 6-month horizon.
- Customers can appear in several snapshots.
- Calendar adjustment uses the portfolio's monthly HSIC row share.

**Business (labelled Assumed)**
- Interchange %, MetroMart co-funding %, cost of funds, EMI subvention %, response scenarios.

**Limitations**
- The ₹9,999.99 cap understates big-ticket spend. We disclose it and don't correct it.
- There is no offer, response or redemption history, so all response figures are simulated until the pilot runs.
- **Synthetic-data caveat:** the data behaves as if payment method is drawn per purchase from a probability that depends only on date and ticket size. Real portfolios usually have customer-level differences. This is why the heterogeneity gate is a *gate*, not a one-off finding: on real data, if the gate passes, customer-level targeting switches on automatically.

---

## 10. Architecture

```
Synchrony-Hackthon-/
├── README.md, PROJECT_PLAN.md, TASKS.md, requirements.txt
├── data/                      # the 4 case CSVs (not committed unless the owner decides)
├── analysis/
│   ├── config.py              # paths, SEED=42, cutoffs, ASSUMPTIONS, gate thresholds
│   ├── prep.py                # load, clean, enrich (§2 rules) + validation asserts
│   ├── experiments.py         # X1–X17 and F1–F13, each a function returning a dict
│   ├── closure_model.py       # out-of-time closure model (B0, B1, LR, HGB)
│   ├── segments.py            # K-means negative control, ₹-at-stake ranking, rule segments
│   ├── economics.py           # offer economics, break-even, scenarios, MDE
│   ├── export.py              # outputs/*.csv, charts/*.png, key_numbers.md, dashboard JSON
│   └── run_all.py             # one command rebuilds everything; fails loudly on any assert
├── notebooks/story.ipynb      # narrative walk-through that imports analysis/ (no logic of its own)
├── outputs/                   # key_numbers.md, impact_ledger.csv, experiment_log.csv, charts/, model_eval/
└── dashboard/                 # React app (§11); reads dashboard/public/data/*.json
```

- **Environment:** a dedicated conda env, `synchrony` (Python 3.12 + Node.js 20). Python packages are listed in `requirements.txt`; nothing is installed globally.
- **No database.** The data is about 22MB of CSV.
- **Single source of numbers.** `run_all.py` writes `key_numbers.md` and the dashboard JSON from the same objects, so the deck and the UI can't disagree.

---

## 11. Dashboard (UI)

**Stack:** React 18.3 + Vite 5.4 + TypeScript + Tailwind 3.4 + ECharts 5.5 (`echarts-for-react`).
- Static build with no backend. Every page reads precomputed JSON.
- Light and dark themes; works at phone width.
- Hosted as a private claude.ai Artifact or on GitHub Pages; the owner decides whether to share.
- The deck carries the link and screenshots. **The PDF must stand on its own.**

| # | Page | Content | Interaction |
|---|---|---|---|
| 1 | **Story** | The answer (§1), 4 KPI tiles (SoW 28.9 → 19.5%, ₹33M gap, ₹91.2M post-closure spend, closure rate 1.7 → 3.4%), 3 recommendations | Each tile links to its evidence page |
| 2 | **The decline** | Monthly SoW with FY bands; Bridge waterfall; stayers' method shift | Toggle ₹ / pp |
| 3 | **Is it a segment problem?** | Quarterly SoW lines for any slice: membership, age, limit, APR, vintage, category, gender, future closers | Dropdown: every slice gives the same overlapping lines |
| 4 | **Noise check** | Real customers vs simulated customers who all share the same probability: dispersion, split-half scatter, FY25 vs FY26 scatter, variance ratio | Re-simulate button; slider for rows per customer |
| 5 | **Attrition** | Closures per open card by quarter; closure rate by tenure; pre-closure curve; fixed vs time-aware silent-attrition null | **Raw / calendar-adjusted toggle** (U3) |
| 6 | **Where the wallet went** | Method mix by ticket band and FY; Sankey of stayers' share shift; cardholders vs non-cardholders | Band filter |
| 7 | **Expected vs found** | The 17 experiments as cards: belief → test → number → verdict chip; closure-model comparison table | Filter by source / verdict |
| 8 | **Segments & offers** | Segment cards (size, ₹ at stake, closure rate, offer); offer library; K-means negative-control result | Click a segment to see its offer economics |
| 9 | **Offer simulator** | Per offer: shift-rate slider → incremental ₹, cost (incremental vs cannibalised), net value, break-even line; MDE / holdout planner | Every output carries a **Simulated** badge; assumptions are editable |
| 10 | **Customer lookup** | Search an ID: profile, segment, monthly spend by method, derived rewards (earned vs credited), offer | Lazy-loads a sharded JSON |
| 11 | **Methods & assumptions** | Brief rules, assumptions, data checks, evaluation protocol, limitations | — |

**JSON contract** (`dashboard/public/data/`). The analysis track exports these files. The UI track builds against mock files with the same shape from hour 1.
- `kpis.json`
- `sow_monthly.json` · `bridge.json` · `mix_shift.json` · `ticket_mix.json`
- `slices.json` · `noise.json` (summary stats, 2k-point scatter samples, monthly p and the rows-per-customer distribution for live simulation)
- `attrition.json` · `experiments.json` · `closure_model.json`
- `segments.json` · `offers.json` (library, defaults, assumptions)
- `customers/shard_XX.json` (50 shards keyed by `Customer_ID % 50`)
- `assumptions.json`

Total budget: < 12MB.

---

## 12. Deck

About 12 slides plus an appendix. Built from `outputs/` only; every number comes from `key_numbers.md`.

| # | Slide | Message |
|---|---|---|
| 1 | Title | — |
| 2 | Executive summary | The 9.4pp drop is real; "at-risk customers" are not. 3 findings, 3 actions, measured loss + break-even |
| 3 | Data, rules, assumptions | Brief compliance at a glance |
| 4 | The decline | 28.9 → 19.5%; the Bridge shows that 100% of it comes from stayers |
| 5 | Where it went | Cash/UPI 47%; every ticket band; Wallet owns big tickets |
| 6 | The twist | Same decline in every slice + the heterogeneity gate |
| 7 | Expected vs found | 8 strongest rejected ideas with their numbers + 3 lessons |
| 8 | Attrition, corrected | Silent attrition is the trend (time-aware null); closures doubling and tenure-driven; ₹91.2M after closure |
| 9 | Segments | K-means control fails → ₹-at-stake ranking → 6 persistent segments |
| 10 | Offers | Product fixes + moment triggers + segment offers |
| 11 | Economics & pilot | Break-even per offer, simulated range, holdout + MDE |
| 12 | Roadmap & asks | What HSIC and MetroMart decide; dashboard link + screenshots |
| App. | — | Full experiment log, closure-model table, gate details, assumptions, limitations |

---

## 13. Schedule, tracks & cut order

Three tracks run in parallel. Hours are counted from the start of implementation.

| Hours | Track A: Analysis | Track B: Dashboard | Track C: Deck |
|---|---|---|---|
| 0–1 | Env, `config.py`, `prep.py` + asserts, `selection_log.md` | Vite scaffold, theme, layout, mock JSON from §11 | Slide template, storyline, assumptions slide |
| 1–4 | Reproduce F1–F13 and X1–X17 in `experiments.py` | Pages 1–3 on mock data | Slides 1–6 with placeholders |
| 4–6 | Closure model; segments (K-means control, ₹ at stake, rules) | Pages 4–7 | Slides 7–9 |
| 6–8 | Economics, MDE, `export.py`, charts, `key_numbers.md` | Pages 8–9, swap mocks for real JSON | Slides 10–12 |
| 8–10 | Verification (§14), spot checks | Pages 10–11, mobile and dark-mode pass, publish | Insert real numbers and charts, appendix |
| **Freeze ~5 PM IST, 24 Oct** | — | Screenshots for the deck | **Export the PDF; email by 7 PM** |

**Cut order if behind:** page 10 (Customer lookup) → page 4's live simulation (keep static charts) → page 9 simulator (keep a static economics table) → the whole dashboard (screenshots of PNG charts only).

**Never cut:** brief rules, F1–F13, the experiment log, segments, offers with break-even, assumptions, the deck.

---

## 14. Verification

- `python analysis/run_all.py` passes every assert:
  - row counts and data checks from §2;
  - the Bridge reconciles to the reported FY SoW;
  - segment sizes add up to the universe;
  - no `impact_ledger.csv` row is missing a Measured / Simulated / Assumed tag;
  - snapshot dates: max feature date ≤ cutoff < min label date.
- **Reproduction checks** against the 23 Oct exploratory numbers. Tolerance ±0.2pp unless stated otherwise:
  - SoW: 28.9 / 19.5%;
  - Bridge: +0.26 / −9.54 / −0.15pp;
  - Cash/UPI share of the loss: 47%;
  - variance ratio: 1.00 ± 0.02;
  - time-aware null excess: |x| < 1.5pp;
  - closure LR test ROC-AUC: 0.62 ± 0.01;
  - post-closure spend: ₹91.2M;
  - missed cashback: ₹3.98M.
- **Sanity checks:**
  - random baseline PR-AUC ≈ the base rate;
  - the simulator at 0% shift reproduces the baseline;
  - break-even worked out by hand for one offer.
- **Spot checks:** 3 customers (closed-and-shopping, first-year, high-frequency) traced through raw rows → segment → offer → dashboard lookup.
- **Dashboard:** every page renders from real JSON, with no console errors, at phone width and in both themes.
- **Deck:** every number appears in `key_numbers.md`, and every slide maps to one step of the storyline.
