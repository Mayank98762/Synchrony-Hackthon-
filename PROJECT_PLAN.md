# MetroMart–HSIC Silent Attrition & Share of Wallet: Project Plan (v5.3, final)

> Synchrony Analytics Hackathon 2026. **Required deliverable:** slides as a PDF, emailed to analyticshiring@syf.com by **8:00 PM IST, 24 Oct 2026**. The subject line is the roll number only. Attach the file; do not use Google Drive.
> v5 replaces v4 and `synchrony_hackathon_strategy_blueprint.md`. Both earlier plans were tested against the data on 23 Oct, and most of their core ideas failed. §4 records what failed and why. Internally we track which plan each idea came from; **in the deck they are "common hypotheses we tested"** and our earlier plans are never named.
> **v5.1 (23 Oct):** a teammate's independent EDA reproduced the core numbers exactly (§2). It also:
> - strengthened the first-year closure finding (F10);
> - added two clearer views: per-card spend (F14) and the SoW-band movement table (X1);
> - led us to fix shared definitions so that every output agrees (§3, rule 9).
>
> **v5.2 (23 Oct), after an external review:**
> - silent attrition is reframed as *real and universal*, not "rejected";
> - the brief's segmentation question gets a literal answer (a 2×2 of frequency × closure risk, §7);
> - reward visibility is the hero offer;
> - the "why" explanations are labelled hypotheses;
> - the loss is stated in interchange terms;
> - the pre-registration claim is dropped;
> - the dashboard is cut to 4 pages and built after the deck charts.
>
> **v5.3 (23 Oct), final planning change; implementation starts from this version:**
> - **Economics are net of rewards.** HSIC already pays an effective 1.39% in rewards against an assumed 1.5–2% interchange, so the gross interchange figure overstated the loss. The value of a shifted ₹ is now interchange + revolve income − the reward share HSIC funds (F15, §8). Offers that can't pay back are reported as "never breaks even".
> - **O6 win-back is cut from 5% to 3%** and co-funded by MetroMart, because 5% on everything loses money on every recovered ₹.
> - **Purchase frequency counts all MetroMart purchases**, not only those made while the card was open. The old definition put only 8.7% of young cards in the top tercile vs 30.9% of mature cards, so the "Protect first" box was nearly empty by construction. With the new definition the figures are 31.1% vs 30.9% (checked on the data at 2026-07-31).
> - **The 2×2 slide shows that SoW doesn't separate the boxes** while closure risk and non-HSIC ₹ do.
> - **Slide 10 shows three offers** (O3, O1, O2); the rest go on one line and in the appendix.
> - **The brief's "no fees" detail is used:** it explains why customers keep the card and stop using it rather than close it.

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

HSIC's Share of Wallet at MetroMart fell from **28.9% in FY25 to 19.5% in FY26**. Customers aren't shopping less: MetroMart spend per card was flat (₹1,036.8 in Aug 2024 vs ₹1,028.9 in May 2026), while HSIC spend per card halved (₹356.2 → ₹166.7). **This is silent attrition, and it is universal.** Nearly every open card is quietly losing share, at the same rate for every kind of customer: Prime and Non-Prime, every age, credit limit, APR band, card vintage and category. Statistically, customers don't differ in how often they reach for the card. Usage varies between them no more than coin flips would, and a customer's share this year predicts nothing about next year. So silent attrition is **not concentrated in a group that could be found and targeted: the whole book is low-SoW**. HSIC has a **product problem, not a targeting problem.** The card is losing ground mainly to **Cash/UPI**, which took 47% of the lost share, across every ticket size.

Our recommendation has three layers:
1. **Fix the product for everyone, starting with reward visibility.** No rival card matches HSIC's Grocery and Electronics rates, yet Prime members use the card exactly like Non-Prime members and left ₹1.60M of cashback on the table in FY26. Showing the reward at the till costs almost nothing. Next come instant cashback at the till and the card on UPI.
2. **Trigger offers at the moment of purchase**, using the one real behavioural signal: ticket size.
3. **Prioritise with a 2×2 built from traits that persist or predict:** purchase frequency at MetroMart × closure risk (card age). SoW is the same in every box; value and risk are not. The closed-but-still-shopping group sits outside the grid: ₹91.2M of spend after closure. Young cards matter most: cards under 6 months old close at 14.7% within six months, about 5× the rate of cards over 3 years old.

The interchange on MetroMart spend is thin once rewards are paid (F15), so the bank's stake is **retention and revolving interest**, and every paid offer must clear a net-of-rewards break-even.

Every claim is backed by a test (§4–§5), and every test has a baseline or a null model. The reasons *behind* the shift are labelled hypotheses that the pilot will test (§5): immediacy for Cash/UPI, awareness for the reward paradox.

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
- **Independent cross-check:** a second EDA, written separately by a teammate, matches ours exactly on:
  - pooled SoW (0.289 / 0.195);
  - all eight FY payment-mix shares;
  - the Aug 2024 and May 2026 per-card figures;
  - open cards at both cutoffs (26,749 / 29,198);
  - closers at 2026-01-31 (1,799);
  - card-age AUC (0.611 / 0.672).

  The remaining differences come from definitions, not errors, and are resolved by §3 rule 9.

---

## 3. Evaluation protocol

These rules apply to every experiment, whether it was already run (§4) or is still to come.

1. **Decision rules are fixed before the final run.** The 23 Oct experiments were exploratory. The thresholds and selection rules for the final pipeline are written into `outputs/model_eval/selection_log.md` before `run_all.py` produces the reported numbers, and are not changed afterwards. This is *not* pre-registration, and the deck won't call it that.
2. **Every effect is compared with a null.** Nulls are calendar-matched, so a portfolio-wide trend can't pose as a customer-level effect. This one rule overturned four common hypotheses (§4).
3. **Heterogeneity gate.** Before any customer-level score or segment is used, it must show:
   - **variance ratio** (observed spread of per-customer HSIC share ÷ spread expected from chance alone) clearly above 1;
   - **split-half reliability** (odd vs even transactions in the same year) clearly above 0;
   - **year-over-year persistence** of r ≥ 0.2.

   A variable that fails the gate is not used for targeting. Card age passes for a different reason: it doesn't need to persist, because it *predicts* closure out of time.
4. **Out-of-time validation for prediction.** Train on the 2025-07-31 snapshot, test once on the 2026-01-31 snapshot, and score at 2026-07-31. Features come from the 12 months up to the cutoff; labels from the 6 months after it.
5. **Baselines are mandatory.** Every model is compared against a simple rule and against random. It must beat the rule with a bootstrap CI that excludes 0, or we ship the rule.
6. **Uncertainty is reported.** 95% CIs (bootstrap or normal approximation) on every headline comparison.
7. **Every ₹ figure is labelled** Measured, Simulated or Assumed, in the deck and on the dashboard. Causal explanations the data can't test are labelled **Hypothesis**.
8. **Gender is never a model feature.** It is used only for the fairness slice check.
9. **Shared definitions.** These are fixed in `selection_log.md` before coding, and every script, chart and slide uses them. The two EDAs differed only where these weren't yet fixed (e.g. 1,281 vs 1,257 closers at 2025-07-31, from calendar months vs a fixed number of days).

   | Term | Definition |
   |---|---|
   | 6-month window | (cutoff, cutoff + 6 calendar months], end date inclusive. 2025-07-31 → 2026-01-31; 2026-01-31 → 2026-07-31 |
   | Card age | Days from open date to cutoff ÷ 365.25. Bins: < 6m, 6–12m, 1–2y, 2–3y, 3y+ |
   | Closure-model universe | **All** cards open at the cutoff (open ≤ cutoff, not closed on or before it), including cards under 6 months old. Card age is a feature |
   | "Purchase" | An active-window Sale row |
   | Purchase frequency | **All** MetroMart Sale rows (any payment method, before or after the card opened) in the 12 months up to the cutoff. It measures the customer's value to MetroMart, so it must not depend on card age. Counting only active-window rows caps a young card's count at its age (8.7% of young cards vs 30.9% of mature cards in the top tercile); counting all rows gives 31.1% vs 30.9%. Tercile cut points are fixed in `selection_log.md` |
   | Customer-level SoW filter | ≥ 3 purchases in each period compared |
   | SoW bands | Zero = 0; Low / Mid / High = terciles of the non-zero FY25 SoW values, with the same cut points applied in FY26 |
   | Silent-attrition universe | Card open from the lookback start (cutoff − 12 months) to the horizon end; ≥ 1 HSIC row in the lookback; ≥ 1 active row in the horizon |
   | Net margin per ₹ of HSIC spend | interchange % + revolve income % − reward rate × (1 − MetroMart co-funding share). Reward rate = the measured FY26 effective rate on HSIC spend (1.39%) unless an offer changes it. All three inputs except the reward rate are Assumed (§9) |

---

## 4. Experiment log: what we expected vs what we found

Ideas came from three sources: **v4** (the previous project plan), **BP** (the strategy blueprint) and **R** (our own review). Every row was tested on the full data on 23 Oct 2026, and the final pipeline must reproduce each number (§14).

**In the deck:**
- these appear as *common hypotheses we tested*, with no source column;
- the main slide shows **three**: X3 (silent attrition vs the trend), X4 (the decay curve that disappears) and X1 (K-means on noise);
- the full table goes in the appendix.

| # | Source | What we expected | Test | What we found | Verdict |
|---|---|---|---|---|---|
| X1 | v4 C3, BP Model 2 | Clustering customers on SoW would reveal low-SoW segments | Heterogeneity gate on per-customer HSIC share | Variance ratio **1.001** (FY25) and **0.996** (FY26): exactly the spread chance produces. Split-half r = **−0.007** (n = 22,320). FY25 → FY26 r = **0.00** (second EDA: 0.002, 95% range −0.018 to 0.020). SoW-band movement: whichever FY25 band a customer starts in, 39–43% land in "Zero" in FY26 | **Rejected.** SoW clusters would be clusters of noise |
| X2 | v4 C2 | A detector could flag individual customers whose SoW is declining | Same gate | Every customer's usage falls at the portfolio rate; nothing customer-specific remains to detect | **Rejected.** Dropped |
| X3 | v4 #21 | Silent attrition is concentrated: some cardholders go quiet faster than chance and the trend predict | Zero-HSIC rate in the next 6 months vs two nulls, at 3 cutoffs | Fixed-share null: excess **+21.6 / +17.5 / +21.5pp**. Time-aware null: excess **+0.7 / +0.1 / +0.0pp** (CI ±1pp). Second EDA, different universe: excess +0.1 / +0.2pp | **Reframed.** Silent attrition is real and universal. The portfolio-wide trend explains all of it; no group goes quiet faster than everyone else. The usual count would label about 21pp of cardholders "silent attriters" who are behaving exactly like everyone else |
| X4 | v4 #4 | HSIC use decays in the months before a card closes | Closers' HSIC share by months before closure, raw vs calendar-adjusted | Raw: 27.0% at −12 months → 20.5% at closure, which *looks* like decay. Calendar-adjusted excess: between −1.4 and +2.3pp with no trend | **Rejected.** Closures cluster late in the window, when everyone's SoW is lower |
| X5 | v4 C1-B1, BP Model 1 | Recent card usage predicts closure | Out-of-time test on cards with ≥ 6 months' tenure (25,468 cards, 1,246 closures); second EDA on all open cards, one feature at a time | Recency rule ROC-AUC **0.519**. Usage features only: **0.523** (≈ random). Profile features: **0.619**. Second EDA: every feature except card age scores 0.50–0.55 | **Rejected.** Usage carries no closure signal |
| X6 | v4 C1-M2 | Gradient boosting beats logistic regression | Same test | HGB 0.606 vs LR 0.620 ROC-AUC; top-decile capture 18.4% vs 18.5% | **Rejected.** Ship LR |
| X7 | v4 #12 | New cards show an onboarding usage cliff | Calendar-adjusted HSIC share by months since opening | Within ±1.5pp for months 0–18, no trend | **Rejected for usage.** But closure *is* card-age-driven (F10) |
| X8 | BP H2 | Non-Prime members drop off because 1% is too little | SoW by membership by quarter; logistic model of HSIC use | Non-Prime 32.8 → 15.5%, Prime 32.7 → 15.6%. Prime coefficient **0.000** | **Rejected.** Also confirms the reward paradox (F8) |
| X9 | BP H4 | Customers keep Grocery on HSIC and move other categories away | SoW by category | 23–24% in all 10 categories; each falls ≈ 32 → 15% | **Rejected** |
| X10 | BP H3 | Credit limits bind during sale events | Monthly MetroMart spend ÷ card limit | Median **1.2%**, maximum 26.5%. Zero customer-months reach 50% | **Rejected** |
| X11 | BP H3 | Festive peaks (Diwali) drive switching | Monthly sales index | 92–108 (mean = 100), no festive spike | **Rejected** |
| X12 | R | MetroMart's own Wallet is cannibalising the card | Stayers' method shift; non-cardholders' method shift | Wallet took only **14%** of HSIC's loss, and Wallet share is *falling* for non-cardholders (48.8 → 44.8%) | **Rejected.** Cash/UPI is the winner |
| X13 | v4 S1 | A "never-activated" segment exists | Share of active cardholders with zero HSIC rows vs chance | 26.9% observed vs 25.7% expected by chance | **Rejected.** Mostly chance |
| X14 | R | Ticket-size or category mix would make good segments (big-ticket shopper, grocery shopper) | FY25 → FY26 persistence | Big-ticket share r = **0.008**; Grocery + Electronics share r = **0.000** | **Rejected as segments.** Ticket size works at the *transaction* level instead (F6) |
| X15 | BP | Predict "SoW drops > 20% in the next 60 days" | Rows available per window | 0.82 rows per customer per 60 days, so SoW is undefined for most customers | **Infeasible** |
| X16 | BP Model 3 | Uplift model for offer response | Data audit | No historical offers, so no treated or control group | **Infeasible.** Replaced by a pilot design (§8) |
| X17 | v4 | Returns behave differently by payment method | Return rate by method | 10.1% for every method | **No signal** |

**What testing these hypotheses taught us (deck slide 7, with X3, X4, X1)**
1. **Calendar-adjust everything.** When the whole portfolio drifts, a customer-level metric that ignores the drift mistakes *universal* silent attrition for a group of individual "silent attriters", "decayers" and "decliners" (X3, X4).
2. **Test whether customers differ before segmenting them.** K-means on SoW is the common first move. The heterogeneity gate takes minutes, and it showed that approach would produce confident-looking noise (X1, X2, X14).
3. **When the drift is portfolio-wide, the fix is portfolio-wide.** Targeting money spent on "low-SoW customers" would land on customers chosen at random.

---

## 5. What the data does support

| # | Finding | Evidence | Label |
|---|---|---|---|
| F1 | **SoW fell 28.9% → 19.5% (FY25 → FY26)** in a straight line: 32.7% in Q1 FY25 to 15.6% in Q4 FY26, about −2.4pp per quarter | Active-window, net, ratio of sums | Measured |
| F2 | **The whole decline comes from customers who stayed.** Of −9.4pp: card closures +0.26pp, change among continuously open cards −9.54pp, new cards −0.15pp | SoW Bridge on 18,111 cards open throughout both FYs (29.2% → 19.6%) | Measured |
| F3 | **Cash/UPI is the main winner**, taking 47% of HSIC's lost share; Debit took 21%, Other Bank CC 19%, Wallet 14% | Stayers' payment-mix shift | Measured |
| F4 | **The shift to Cash/UPI is partly market-wide but much stronger for cardholders:** +4.5pp for stayers vs +1.8pp for non-cardholders | Difference in differences | Measured |
| F5 | **HSIC loses about a third of its share in every ticket band**, and Cash/UPI gains 3.5–4.4pp in every band. Shares in FY25 → FY26: | | Measured |
| | &nbsp;&nbsp;• under ₹1k: 23.3 → 15.0% | | |
| | &nbsp;&nbsp;• ₹1–3k: 27.9 → 18.3% | | |
| | &nbsp;&nbsp;• ₹3–10k: 28.8 → 19.3% | | |
| | &nbsp;&nbsp;• capped ₹9,999.99: 30.1 → 21.7% | | |
| F6 | **Ticket size is the only behavioural signal.** Within the same category and quarter, HSIC is used on 17.1% of low tickets vs 25.5% of high tickets. A model of HSIC use goes from AUC 0.592 (month only) to 0.604 (everything); every customer attribute adds ≈ 0 | Within-stratum terciles; logistic model | Measured |
| F7 | **MetroMart Wallet carries about half of all capped (₹9,999.99) purchases** (48.5 → 51.1%), even though HSIC is the product with financing | Ticket-band mix | Measured |
| F8 | **Reward paradox.** No rival card matches HSIC's Grocery/Electronics rates (brief), yet Prime members use HSIC exactly like Non-Prime members. In FY26, Prime cardholders put ₹47.4M of Grocery + Electronics spend on other methods and **left ₹1.60M of cashback on the table**, i.e. cashback they would have earned by paying with HSIC. *Context only:* across all cardholders and categories, the figure is ₹3.98M, against ₹0.96M actually earned on HSIC | Derived rewards | Measured |
| F9 | **Closures per open card doubled** from 1.7% a quarter (Jul–Sep 2024) to 3.4% (Apr–Jun 2026) | Closures ÷ cards open at quarter start | Measured |
| F10 | **Closure is a young-card problem.** 6-month closure rate by card age, all open cards: | Rule 9 definitions; both EDAs | Measured |
| | &nbsp;&nbsp;• 2025-07-31 cutoff: 8.3% (< 6m), 6.6% (6–12m), 4.6% (1–2y), 3.8% (2–3y), 2.8% (3y+) | | |
| | &nbsp;&nbsp;• 2026-01-31 cutoff: **14.7%**, 9.0%, 6.3%, 4.0%, **3.0%**, i.e. about 5× from youngest to oldest | | |
| | Card age alone scores ROC-AUC 0.611 / 0.672 at the two cutoffs. On the ≥ 6-month universe, tenure was the dominant LR coefficient (−0.29 standardised), and the model captured 18.5% of closers in its top decile (1.85× random). The final pipeline re-runs the model on the rule-9 universe | | |
| F11 | **Closed cards keep shopping.** 6,227 of 7,664 closers still shop at MetroMart, spending **₹91.2M** net after closure. Their mix after closure (Wallet 46%, Cash/UPI 28%, Debit 13%, Other CC 13%) matches non-cardholders, so HSIC's share is simply redistributed | Post-close transactions | Measured |
| F12 | **HSIC spend shrank while MetroMart spend grew.** HSIC net spend fell from ₹85.7M to ₹68.9M while active cardholder spend rose from ₹296.3M to ₹353.8M. At FY25's SoW, FY26 HSIC spend would have been about ₹102M, so the gap is **about ₹33M** | Counterfactual at constant SoW | Measured (gap is derived) |
| F13 | **Only frequency and spend persist** year to year (r = 0.44 for purchase count, 0.22 for net spend). These are the only behaviour variables allowed into segments | Persistence test | Measured |
| F14 | **Customers kept shopping and changed how they pay.** Cards active in the month went from 21,514 (Aug 2024) to 30,742 (May 2026). MetroMart net spend per card stayed flat (₹1,036.8 → ₹1,028.9). HSIC spend per card more than halved (₹356.2 → ₹166.7), taking monthly SoW from 34.4% to 16.2% | Per-card monthly view; both EDAs | Measured |
| F15 | **The loss in the bank's terms, net of rewards.** Gross interchange on the ₹33M gap at 1.5–2% (Assumed) is ₹0.50–0.67M, but HSIC would also have paid 1.39% in rewards on that spend (measured FY26 effective rate), i.e. ₹0.46M. Net lost margin (rule 9 definition, no revolve income): | F12 × rule-9 net margin | Measured × Assumed |
| | &nbsp;&nbsp;• HSIC funds all rewards: **₹0.04–0.20M** | | |
| | &nbsp;&nbsp;• MetroMart co-funds 50% of rewards: **₹0.27–0.43M** | | |
| | So the interchange on MetroMart spend is thin; the bank's real stake is **retention** (closures doubled, F9) and **revolving interest** (APR 28–35%, but there is no balance data, so revolve income is an Assumed scenario: 0 / 1 / 2% of spend). The deck leads the value story with those two, never with gross interchange. Every figure is also reported per 10,000 cardholders, because the dataset is a 45k-customer sample | | |

**A clue from the brief: no fees.** The card has no joining or annual fee, so keeping an unused card costs the customer nothing. That fits what the data shows: the main loss is cards kept open and used less (F2: −9.54pp from stayers vs +0.26pp from closures), not cards closed. It also means closure isn't driven by cost, which is consistent with usage not predicting closure (X5). Labelled Hypothesis on slide 6.

**Why, not just what: hypotheses for the pilot**

The data shows *what* moved, not *why*. These two explanations are labelled **Hypothesis** everywhere they appear, in the deck and in the UI:

| Hypothesis | Consistent with | Not shown by the data | Pilot test that confirms or refutes it |
|---|---|---|---|
| **H-imm:** customers choose Cash/UPI for immediacy (instant settlement and payoff vs a statement credit next month) | Cash/UPI took 47% of the loss, in every ticket band (F3, F5) | The data has no reason codes, and immediacy isn't observed | O1 instant cashback vs holdout: HSIC share lift on treated cards |
| **H-aware:** Prime members don't know, or don't feel, their 5%/3% rates | Prime and Non-Prime usage identical (F8, X8) | Awareness isn't observed; rewards may simply not drive this behaviour | O3 reward visibility vs holdout: lift in Prime Grocery + Electronics HSIC share |

---

## 6. USPs

Each USP exists because of a finding; none were added for show.

| # | USP | Why it's different | Built on |
|---|---|---|---|
| U1 | **The heterogeneity gate.** A three-test check (variance ratio, split-half, persistence) run before any segmentation | Most teams will cluster noise and present it confidently. We prove whether the clusters would be real, and the gate is reusable on any future data | X1, X2, X14 |
| U2 | **Silent attrition, measured against the trend** | Shows silent attrition is real but universal. The usual count would send retention money to about 21pp of "silent attriters" who behave exactly like everyone else | X3 |
| U3 | **Raw vs calendar-adjusted decay curve** (toggle on the dashboard) | The same chart tells two opposite stories, and the adjustment decides which is true | X4 |
| U4 | **SoW Bridge.** An exact split of the −9.4pp into closures, stayers and new cards, broken down by destination method | Answers "is it mix or behaviour?" in one picture: it's behaviour | F2, F3 |
| U5 | **"Target moments, not people."** Offers fire on the purchase (ticket size, basket), not on a customer label | Follows directly from the data: ticket size is the only behavioural signal, and customer traits don't persist | F6, X14 |
| U6 | **Common hypotheses we tested.** Three on the main slide, 17 in the appendix, each with its test and number | Shows judgement, not just output | §4 |
| U7 | **Reward visibility as the hero offer**, followed by instant cashback | No rival card matches HSIC's Grocery/Electronics rates, yet Prime members left ₹1.60M on the table. Showing the reward at the till costs almost nothing; crediting it at the till instead of next month is the second lever. Both rest on hypotheses the pilot tests | F8, H-aware, H-imm |
| U8 | **Break-even-first economics, net of rewards.** Every offer shows the shift rate it needs to pay for itself after the rewards HSIC funds, and says "never breaks even" when it can't | Most teams will count gross interchange or gross spend as "value". We show the margin is thin and price offers accordingly | §8, F15 |

Deliberately left out: GenAI/RAG assistants, AI-written marketing copy, uplift models (no treatment data), real-time streaming and deep-learning CLV. None has supporting data, and they would look like filler to judges hiring analysts.

---

## 7. Segmentation (brief item 3)

The brief asks for "segments using a model or method to identify low-SoW customers". One slide answers it literally: **"Low-SoW = the whole book. Here's who to prioritise and why."**

**Step 1 (setup, not the answer): show the obvious method finds noise.** Run K-means on SoW features as a negative control. Report:
- bootstrap stability (ARI) across 20 resamples;
- outcome separation: does the FY25 segment predict FY26 HSIC share?
- the heterogeneity gate.

If K-means *does* separate outcomes, the gate has failed and we switch to a customer-level design. That rule goes into `selection_log.md` before the final run.

**Step 2: who is low-SoW?** Every open card's expected SoW is the portfolio's current level (15.6% in Q4 FY26), so SoW can't separate customers. Two things can, because the data shows they're real:
- **Value = purchase frequency at MetroMart** (all payment methods, rule 9, so it doesn't depend on card age). It is the most persistent behaviour (FY25 → FY26 r = 0.44); net spend (r = 0.22) is the tiebreak. We don't dress this up as "₹ at stake": with equal usage odds that would be spend × a constant, so we call it what it is.
- **Closure risk = card age.** It predicts out of time: 14.7% six-month closure under 6 months vs 3.0% at 3y+; AUC 0.611 / 0.672.

| | **Mature card** (card age ≥ 12 months) | **Young card** (card age < 12 months) |
|---|---|---|
| **High frequency** (top tercile) | **D. Grow:** threshold bonus (O8) + reward visibility (O3) | **B. Protect first** (highest priority): onboarding protection (O7) + reward visibility (O3) |
| **Low / mid frequency** | **E. Nudge:** product fixes only (O1–O5), no paid incentive | **C. Activate:** activation milestone + Prime trial (O7) |

**Outside the grid:**
- **A. Closed, still shopping:** 6,227 customers who spent ₹91.2M after closure. HSIC gets none of their MetroMart spend, which makes them the most literal low-SoW group. → Win-back (O6).
- **F. Non-cardholders:** 6,836 customers. → Acquisition at checkout (stretch).

**Step 3: final segment list** (first match wins):

| Segment | Rule | Size | Lever |
|---|---|---|---|
| A. Closed, still shopping | Card closed and MetroMart spend after closure | 6,227 | O6 |
| B. Protect first | Open, card age < 12m, top-tercile frequency | From the pipeline | O7 + O3 |
| C. Activate | Open, card age < 12m, other frequency | From the pipeline | O7 |
| D. Grow | Open, card age ≥ 12m, top-tercile frequency | From the pipeline | O8 + O3 |
| E. Nudge | Open, card age ≥ 12m, other frequency | From the pipeline | O1–O5 only |
| F. Non-cardholders | No card | 6,836 | Stretch |

- B + C = 6,297 young cards at 2026-07-31, out of 30,519 open cards (the 23 Oct check counted 6,313 with card age < 1 year, so the pipeline fixes the exact count under rule 9). About a third of them fall in B. If the < 6m and 6–12m groups differ with a CI, they are reported separately within B and C.
- Within every box, reward-visibility messaging (O3) goes to Prime members first. Prime is a fixed attribute, and the ₹1.60M left on the table is theirs.

**How the slide shows it.** One table, one row per box (A–E), three columns:
- **FY26 SoW:** expected to be about the same in every box. This *is* the answer to "identify low-SoW customers": SoW can't separate them;
- **6-month closure rate** and **non-HSIC ₹ per customer:** expected to differ clearly between boxes. That is why we prioritise on value and risk.

If SoW *does* differ between boxes with a CI, we report it and the slide says so.

**Segment checks:**
- sizes add up to the universe;
- the axes are independent: the share of young cards in the top frequency tercile is within ±3pp of the share of mature cards (31.1% vs 30.9% on 23 Oct);
- each box's 6-month closure rate and non-HSIC ₹ differ with a CI; FY26 SoW per box is reported with its CI either way;
- boundary sensitivity: share of customers who change box when the tercile or the 12-month cut moves by ±10%.

---

## 8. Offers & economics (brief item 4)

Ordered by priority. O3 is the hero offer. **Slide 10 shows only O3, O1 and O2**; O4–O8 get one line each there, with full detail in the appendix.

| # | Offer | Layer | Who / trigger | Addresses | Cost model |
|---|---|---|---|---|---|
| **O3** | **Reward visibility (hero):** POS and receipt line "Pay with HSIC: earn ₹X on this basket"; monthly "₹ you left on the table" | Product | Every basket; Prime Grocery + Electronics first | Reward paradox, ₹1.60M (F8); tests H-aware | ≈ 0 incentive cost |
| O1 | **Instant cashback at the till:** reward applied at checkout, not on next month's statement | Product | All HSIC purchases | Cash/UPI shift (F3, F4); tests H-imm | Same reward amount; cost = 1 month's time value + ops (Assumed) |
| O2 | **HSIC card on UPI** (credit card linked to UPI) | Product (strategic) | All | Cash/UPI took 47% of the loss | Partnership and network cost (qualitative) |
| O4 | **No-cost EMI on baskets ≥ ₹3,000** at MetroMart | Moment | Basket ≥ ₹3k | Wallet holds ~half of capped tickets (F7); ticket-size signal (F6) | Subvention %, co-funded by MetroMart (Assumed) |
| O5 | **Small-basket streak:** 5 HSIC purchases under ₹1,000 in a month earn a ₹50 bonus | Moment | Baskets < ₹1k | Lowest HSIC share (17.1%) | Bonus paid only above the threshold |
| O6 | **Win-back:** instant re-approval and 3% on everything for 90 days (capped per customer), then the normal rates | Segment A | 6,227 closers | ₹91.2M post-closure spend | Boost cost on recovered spend, co-funded by MetroMart (Assumed share). Value includes the card's ongoing net margin after the 90 days. Was 5%; cut because 5% exceeds any assumed per-₹ margin |
| O7 | **Young-card protection:** activation milestone (3 swipes in 60 days) plus a 3-month Prime trial for Non-Prime | Segments B, C | 6,297 young cards | Up to 5× closure risk (F10) | Trial cost co-funded by MetroMart (Assumed) |
| O8 | **Threshold bonus:** extra 1% only on HSIC spend above the customer's own trailing 3-month average | Segment D | High-frequency mature cards | Avoids paying for spend that would happen anyway | Bonus on the increment only |

**Economics (per offer, in the pipeline and the dashboard simulator)**
- **Value per ₹ shifted to HSIC** = the rule-9 **net margin**: interchange % + revolve income % − reward rate × (1 − MetroMart co-funding share). The base reward rate is the measured 1.39%; for Prime Grocery + Electronics baskets it is the 5% / 3% the customer would earn.
- **Retention value** (O6, O7) = the expected net margin over the card's next 12 months × the change in closure probability (Simulated). This, not interchange on one month's spend, is where young-card offers earn their keep.
- **Cost** is split into incentive on *incremental* spend vs incentive on spend that would have happened anyway (cannibalisation), net of MetroMart's co-funded share.
- **Break-even shift rate** = the share of eligible non-HSIC ₹ that must move for net value ≥ 0. This is the headline number.
- **"Never breaks even"** is a valid output. If an offer's incentive per incremental ₹ is at or above the net margin per ₹ in a scenario (or the required shift rate is above 100%), `economics.py` returns `never` for that scenario and the slide says so. It is never hidden or forced positive.
- **Scenarios** (all Assumed inputs, results labelled **Simulated**):

  | Input | Conservative | Base | Optimistic |
  |---|---|---|---|
  | Interchange | 1.5% | 1.75% | 2.0% |
  | Revolve income (% of spend) | 0% | 1% | 2% |
  | MetroMart co-funding of rewards and boosts | 0% | 50% | 50% |

  Expected: in the conservative scenario, reward-heavy offers don't break even on Grocery + Electronics. That is reported honestly, and it is why O3 (no extra cost) leads.
- **Headline wording:** "₹33M of HSIC spend lost (measured). Net of the rewards HSIC pays, that is ₹0.04–0.43M of margin (assumed rates), so the bank's real stake is retention and revolving balances. Offer X pays back if Y% of eligible spend moves (break-even). Base case ₹Z (simulated)." Never "we will recover ₹Z", and never gross interchange on its own.

**Pilot design (turns simulated numbers into measured ones, and tests the hypotheses)**
- A randomised 10% holdout per offer and segment.
- **O3 vs holdout tests H-aware; O1 vs holdout tests H-imm.** A null result is reported as a refuted hypothesis, not hidden.
- Because HSIC use behaves like a coin flip per purchase, the MDE has a closed form: MDE = 2.8·√(2p(1−p)/n) for n purchases per arm, at 80% power and α = 0.05. The pipeline computes it per segment.
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
- Interchange 1.5–2%, revolve income 0–2% of spend, MetroMart co-funding of rewards and boosts 0–50%, cost of funds, EMI subvention %, response scenarios (scenario table in §8).
- The measured 1.39% FY26 effective reward rate is a *derived* figure (Measured), not an assumption.

**Hypotheses (labelled Hypothesis)**
- H-imm and H-aware (§5). Neither is claimed as a finding.

**Limitations**
- The ₹9,999.99 cap understates big-ticket spend. We disclose it and don't correct it.
- There is no offer, response or redemption history, so all response figures are simulated until the pilot runs.
- There is no balance data, so revolving interest can't be valued.
- **Synthetic-data caveat:** the data behaves as if payment method is drawn per purchase from a probability that depends only on date and ticket size. Real portfolios usually have customer-level differences. This is why the heterogeneity gate is a *gate*, not a one-off finding: on real data, if the gate passes, customer-level targeting switches on automatically.

---

## 10. Architecture

```
Synchrony-Hackthon-/
├── README.md, PROJECT_PLAN.md, TASKS.md, requirements.txt
├── data/                      # the 4 case CSVs, moved here from the repo root in A01; never committed (.gitignore blocks *.csv)
├── analysis/
│   ├── config.py              # paths, SEED=42, cutoffs, ASSUMPTIONS, gate thresholds, rule-9 definitions
│   ├── prep.py                # load, clean, enrich (§2 rules) + validation asserts
│   ├── experiments.py         # X1–X17 and F1–F15, each a function returning a dict
│   ├── closure_model.py       # out-of-time closure model (B0, B1, B2 card age, LR, HGB)
│   ├── segments.py            # K-means negative control, frequency × card-age 2×2, segments A–F
│   ├── economics.py           # offer economics, net margin after rewards, break-even (or `never`), scenarios, MDE
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

**The deck decides this hackathon.** Judges may never open a link in a PDF, so the deck carries every chart and the dashboard is a bonus.
- **Scope:** cut to 4 pages.
- **Who builds it:** Claude, *after* the deck charts are exported. No teammate time comes out of the deck.
- **If it isn't ready by the freeze:** it is dropped without affecting the submission.

**Stack:** React 18.3 + Vite 5.4 + TypeScript + Tailwind 3.4 + ECharts 5.5 (`echarts-for-react`).
- Static build with no backend. Every page reads precomputed JSON.
- Light and dark themes; works at phone width.
- Hosted as a private claude.ai Artifact or on GitHub Pages; the owner decides whether to share.

| # | Page | Content | Interaction |
|---|---|---|---|
| 1 | **Story** | The answer (§1); 5 KPI tiles: SoW 28.9 → 19.5%; HSIC spend per card ₹356 → ₹167 while MetroMart spend per card stays flat; ₹33M gap (₹0.04–0.43M net margin after rewards, Assumed rates); ₹91.2M post-closure spend; closure rate 1.7 → 3.4%. Then 3 recommendations, reward visibility first | — |
| 2 | **Is it a segment problem?** | Quarterly SoW lines for any slice (membership, age, limit, APR, vintage, category, gender, future closers); heterogeneity-gate numbers; SoW-band movement table | Slice dropdown |
| 3 | **Silent attrition & closures** | Fixed vs time-aware silent-attrition null; pre-closure curve; closure rate by card age (both cutoffs) | **Raw / calendar-adjusted toggle** (U3) |
| 4 | **Who to prioritise & offers** | The frequency × card-age 2×2 + closed-but-shopping group, with sizes and outcomes; offer library (O3 first); break-even per offer | Shift-rate slider per offer; every output carries a **Simulated** badge; hypotheses carry a **Hypothesis** badge |

**JSON contract** (`dashboard/public/data/`): `kpis.json` · `slices.json` · `gate.json` · `attrition.json` · `segments.json` · `offers.json` (library, defaults, assumptions). Total size < 2MB.

---

## 12. Deck

About 12 slides plus an appendix. Built from `outputs/` only; every number comes from `key_numbers.md`. **Never name v4 or the blueprint, and never claim pre-registration.**

| # | Slide | Message |
|---|---|---|
| 1 | Title | — |
| 2 | Executive summary | Silent attrition is real and universal: HSIC lost 9.4pp of SoW (₹33M of spend), evenly across every customer type. Net of rewards the margin on that spend is thin, so the stake is retention and revolving balances. 3 findings, 3 actions with reward visibility first, measured loss + break-even |
| 3 | Data, rules, assumptions | Brief compliance at a glance; Measured / Simulated / Assumed / Hypothesis labels explained |
| 4 | The decline | 28.9 → 19.5%; spend per card flat while HSIC spend per card halves (F14); the Bridge shows that 100% of it comes from stayers |
| 5 | Where it went | Cash/UPI 47%; every ticket band; Wallet owns big tickets. "Why Cash/UPI?" shown as hypothesis H-imm |
| 6 | Silent attrition is universal | Same decline in every slice + the heterogeneity gate + the SoW-band movement table. One line: with no fees, keeping an unused card costs nothing, so customers stop using it rather than close it (Hypothesis) |
| 7 | Common hypotheses we tested | Three: silent attrition vs the trend (+21pp → 0), the decay curve that disappears, K-means on noise. Plus 3 lessons |
| 8 | Closures | Closures per open card doubling; cards under 6 months close at 14.7%, about 5× the 3y+ rate; usage doesn't predict closure; ₹91.2M after closure |
| 9 | Who to prioritise | "Low-SoW = the whole book." K-means control as setup → frequency × card-age 2×2 + closed-but-shopping group. Table per box: size, FY26 SoW (same everywhere), closure rate and non-HSIC ₹ (different) |
| 10 | Offers | Three offers only: hero reward visibility (₹1.60M left on the table; H-aware), instant cashback (H-imm), card on UPI. O4–O8 on one line each |
| 11 | Economics & pilot | Net margin per ₹ after rewards; break-even per offer by scenario, including any "never breaks even"; retention value; holdout + MDE; which hypothesis each arm tests |
| 12 | Roadmap & asks | What HSIC and MetroMart decide; dashboard link + screenshots (if built) |
| App. | — | Full table of 17 hypotheses tested, closure-model table, gate details, assumptions, limitations |

---

## 13. Schedule, tracks & cut order

Hours are counted from the start of implementation.
- **Track A:** analysis.
- **Track B:** charts and slide polish (teammates).
- **Track C:** deck.
- **The dashboard:** built by Claude after A08, outside the team's tracks.

| Hours | Track A: Analysis | Track B: Charts & polish | Track C: Deck |
|---|---|---|---|
| 0–1 | Env, `config.py` (incl. rule-9 definitions), `prep.py` + asserts, `selection_log.md` | Chart style guide (palette, fonts, 16:9 sizes); slide-ready chart templates | Slide template, storyline, assumptions slide |
| 1–4 | Reproduce F1–F15 and X1–X17 in `experiments.py` | Draft charts for slides 4–8 from the 23 Oct numbers | Slides 1–6 with `[KN]` placeholders |
| 4–6 | Closure model; segments (K-means control, 2×2, A–F) | Draft charts for slides 9–11 | Slides 7–9 |
| 6–8 | Economics (net margin, retention value, break-even incl. `never`), MDE, `export.py`, final charts, `key_numbers.md` | Swap draft charts for pipeline charts; visual QA | Slides 10–12 + appendix |
| 8–10 | Verification (§14), spot checks | Slide polish; consistency pass on labels and badges | Insert real numbers; full read-through |
| **Freeze ~5 PM IST, 24 Oct** | — | — | **Export the PDF; email by 7 PM** |

**Dashboard (Claude, after A08):** pages 1–4, then publish and take screenshots for slide 12. It is dropped if it isn't ready by the freeze.

**Cut order if behind:**
1. The dashboard.
2. The notebook (`story.ipynb`).
3. The appendix detail beyond the 17-hypothesis table.

**Never cut:** brief rules, F1–F15, the three-hypothesis slide, the 2×2 segment slide, offers with break-even, assumptions, the deck.

---

## 14. Verification

- `python analysis/run_all.py` passes every assert:
  - row counts and data checks from §2;
  - the Bridge reconciles to the reported FY SoW;
  - segment sizes add up to the universe;
  - no `impact_ledger.csv` row is missing a Measured / Simulated / Assumed tag;
  - snapshot dates: max feature date ≤ cutoff < min label date.
- **Decision rules** in `selection_log.md` were fixed before the final `run_all.py` and not changed afterwards.
- **Reproduction checks** against the 23 Oct exploratory numbers. Tolerance ±0.2pp unless stated otherwise:
  - SoW: 28.9 / 19.5%;
  - Bridge: +0.26 / −9.54 / −0.15pp;
  - Cash/UPI share of the loss: 47%;
  - variance ratio: 1.00 ± 0.02;
  - time-aware null excess: |x| < 1.5pp;
  - post-closure spend: ₹91.2M;
  - Prime Grocery + Electronics left on the table: ₹1.60M;
  - FY26 effective reward rate on HSIC spend: 1.39%;
  - net lost margin (F15, no revolve income): ₹0.04–0.20M with no co-funding, ₹0.27–0.43M with 50% co-funding (±₹0.02M);
  - young vs mature share in the top frequency tercile: 31.1% / 30.9% (±1pp).
- **Exact cross-checks** against both EDAs. Counts must be identical and rates must match to 3 decimals:
  - pooled SoW 0.289 / 0.195 and the eight FY payment-mix shares;
  - Aug 2024: 21,514 cards, ₹1,036.8 / ₹356.2 per card, SoW 0.344;
  - May 2026: 30,742 cards, ₹1,028.9 / ₹166.7 per card, SoW 0.162;
  - open cards at the two cutoffs: 26,749 / 29,198;
  - closers: 1,281 / 1,799 under rule 9 (the second EDA's 1,257 used a fixed-day window);
  - card-age AUC: 0.611 / 0.672.
- **Closure model:** on the rule-9 universe, the chosen model must beat card age alone (0.611 / 0.672) with a bootstrap CI that excludes 0. Otherwise we ship the card-age rule and say so.
- **Sanity checks:**
  - random baseline PR-AUC ≈ the base rate;
  - the simulator at 0% shift reproduces the baseline;
  - break-even and the net-margin line worked out by hand for one offer;
  - a deliberately loss-making test offer (incentive above the net margin) returns `never`, not a number;
  - no slide or tile quotes gross interchange without the net-of-rewards figure beside it.
- **Spot checks:** 3 customers (closed-and-shopping, young card, high-frequency mature card) traced through raw rows → segment → offer.
- **Labels:** every causal "why" in the deck and the UI carries a Hypothesis label; no slide names v4 or the blueprint, or claims pre-registration.
- **Deck:** every number appears in `key_numbers.md`, and every slide maps to one step of the storyline.
- **Dashboard (if built):** the 4 pages render from real JSON, with no console errors, at phone width and in both themes.
