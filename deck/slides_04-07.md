# Slides 4–7: the story (owner: Mayank)

Drop-in content for Shreyash's template. Every number shows its key in `outputs/key_numbers.md`, so swapping in `[KN:key]` is mechanical.
Charts: `outputs/charts/`, 16:9 at 200 dpi, rebuilt by `python -m analysis.charts_story` after `python analysis/run_all.py`.
Badges: **M** = Measured · **H** = Hypothesis. No slide names earlier plans or claims pre-registration.

---

## Slide 4: The decline

**Headline:** HSIC's share of MetroMart spend fell from 28.9% to 19.5% in one year, and all of it came from cards that stayed open

**Charts:** `04_sow_trend.png` (main) · `04_per_card.png` · `04_bridge.png`

**Points**
- SoW **28.9% → 19.5%** FY25 → FY26 (`f1_sow_fy25`, `f1_sow_fy26`) **M**, falling in a straight line: **32.7%** in Q1 FY25 to **15.6%** in Q4 FY26, about **−2.4pp a quarter** (`f1_sow_fy25_q1`, `f1_sow_fy26_q4`, `f1_slope_pp_per_quarter`) **M**
- Customers didn't shop less. MetroMart spend per card was flat, **₹1,037 → ₹1,029**, while HSIC spend per card more than halved, **₹356 → ₹167** (Aug 2024 → May 2026; `f14_aug24_net_per_card`, `f14_may26_net_per_card`, `f14_aug24_hsic_per_card`, `f14_may26_hsic_per_card`) **M**
- **Bridge, −9.4pp:** card closures **+0.26pp**, continuously open cards **−9.54pp**, new cards **−0.15pp** (`f2_leaver_pp`, `f2_stayer_pp`, `f2_joiner_pp`) **M**. On the **18,111** cards open throughout, SoW went 29.2% → 19.6% (`f2_stayers_n`, `f2_stayer_sow_fy25`, `f2_stayer_sow_fy26`)

**Speaker notes:** SoW is always a ratio of sums, counted only while the card is active and net of returns (brief rules). The Bridge reconciles exactly to the reported FY figures. This is a behaviour change by existing cardholders, not a mix effect from closures or new cards.

---

## Slide 5: Where it went

**Headline:** Cash/UPI took almost half of HSIC's lost share, at every ticket size

**Charts:** `05_mix_shift.png` (main) · `05_ticket_bands.png` · `05_capped_mix.png` (Wallet owns big tickets)

**Points**
- Of HSIC's lost share on continuously open cards: **Cash/UPI 47%**, Debit 21%, Other bank CC 19%, MetroMart Wallet 14% (`f3_cash_upi_share_of_loss`, `f3_debit_share_of_loss`, `f3_other_cc_share_of_loss`, `f3_wallet_share_of_loss`) **M**
- Partly market-wide, but much stronger for cardholders: Cash/UPI **+4.5pp** for cardholders vs **+1.8pp** for non-cardholders (`f4_cash_upi_change_pp_stayers`, `f4_cash_upi_change_pp_noncardholders`) **M**
- HSIC loses about a third of its share in **every** ticket band (under ₹1k 23.3 → 15.0%; ₹1–3k 27.9 → 18.3%; ₹3–10k 28.8 → 19.3%; capped 30.1 → 21.7%), and Cash/UPI gains **+3.5 to +4.5pp** in every band (`f5_hsic_share_fy25_*`, `f5_hsic_share_fy26_*`, `f5_cash_upi_gain_pp_*`) **M**
- Ticket size is the only behavioural signal: within the same category and quarter, HSIC is used on **17.1%** of low tickets vs **25.6%** of high tickets (`f6_hsic_row_share_t1`, `f6_hsic_row_share_t3`) **M**
- MetroMart Wallet carries about half of capped ₹9,999.99 purchases (**48.5% → 51.1%**; `f7_wallet_share_capped_fy25`, `f7_wallet_share_capped_fy26`), even though HSIC is the product with financing **M**
- **Why Cash/UPI? Immediacy:** settled and paid off at once, vs a statement credit next month (H-imm) **H**. The data has no reason codes; the O1 instant-cashback pilot arm tests it.

**Speaker notes:** Wallet is *not* eating the card: it took only 14% of the loss, and its share is falling among non-cardholders (X12). The ticket-size signal is why offers fire on the purchase, not on a customer label.

---

## Slide 6: Silent attrition is universal

**Headline:** Every kind of customer is quietly using the card less, at the same rate, so the whole book is low-SoW

**Charts:** `06_slices.png` (main) · `06_gate.png` · `06_band_movement.png`

**Points**
- Every slice fell **7–11pp**: membership, age, credit limit, APR, card vintage, all 10 categories and future closers (`experiments_h.slice_table`) **M**
  - Prime **32.7% → 15.6%** vs Non-Prime **32.8% → 15.5%**, Q1 FY25 → Q4 FY26 (`x8_sow_fy25_q1_prime`, `x8_sow_fy26_q4_prime`, `x8_sow_fy25_q1_non_prime`, `x8_sow_fy26_q4_non_prime`); Prime coefficient in a calendar-controlled model of HSIC use is **−0.007** (95% CI −0.026 to +0.012; `x8_prime_logit_coef`) **M**
  - Category SoW **23–24%** in all 10 categories (`x9_sow_pooled_min`, `x9_sow_pooled_max`) **M**
- **Heterogeneity gate: customers don't differ in how often they use the card** (Devansh's X1) **M**
  - Variance ratio **1.00** in both years (`x1_variance_ratio_fy25`, `x1_variance_ratio_fy26`): the spread chance alone produces
  - Split-half r = **−0.005**; FY25 → FY26 r = **+0.004** (`x1_split_half_r`, `x1_persistence_r`)
- **SoW-band movement:** whichever FY25 band a customer starts in, **35–37%** land in "Zero" in FY26 and about **16%** in "High": the rows are identical (`x1_band_to_zero_min`, `x1_band_to_zero_max`; 12,327 cardholders with ≥ 3 purchases in each FY, `x1_sow_filter_n`; table `outputs/tables/x1_sow_band_movement.csv`) **M**
- "Never-activated" cards are chance: **26.9%** of active cardholders have no HSIC rows, against **26.9%** expected if everyone used HSIC at the portfolio's monthly rate (`x13_zero_hsic_observed`, `x13_zero_hsic_expected`) **M**
- **Why keep a card you don't use? No fees:** with no joining or annual fee, keeping an unused card costs nothing, so customers stop using it rather than close it **H**

**Speaker notes:** This is the literal answer to "identify low-SoW customers": SoW can't separate them, because every open card's expected SoW is the portfolio's current level. That is why slide 9 prioritises on value (purchase frequency) and risk (card age) instead.

---

## Slide 7: Common hypotheses we tested

**Headline:** Three common analyses would have told a confident and wrong story; calendar-matching and a gate overturned them

**Charts:** `07_silent_null.png` · `07_decay_raw_vs_adj.png` · `07_kmeans.png`

**Points**
1. **"Some cardholders are silent attriters."** Against their own past usage, **+21.6 / +17.5 / +21.5pp** more cardholders go zero-HSIC than expected (6 months after 2025-01-31 / 2025-07-31 / 2026-01-31; `x3_excess_fixed_2025_01_31`, `x3_excess_fixed_2025_07_31`, `x3_excess_fixed_2026_01_31`). Against the portfolio trend: **+0.4 / 0.0 / −0.3pp**, each inside its 95% CI of ±0.8–1.1pp (`x3_excess_time_2025_01_31`, `x3_excess_time_2025_07_31`, `x3_excess_time_2026_01_31`, `x3_excess_time_lo_*`, `x3_excess_time_hi_*`) **M**. Silent attrition is real but **universal** (`x3_verdict`); the usual count would send retention money to ~21pp of cardholders who behave exactly like everyone else.
2. **"Usage decays before a card closes."** Raw: **27.0%** at −12 months → **20.5%** at closure (`x4_raw_m12`, `x4_raw_m0`), which looks like decay. Calendar-adjusted: **−1.4 to +2.3pp**, slope **+0.08pp a month** (95% CI −0.09 to +0.25) (`x4_excess_min_pp`, `x4_excess_max_pp`, `x4_slope_pp_per_month`) **M**. Closures cluster late in the window, when everyone's SoW is lower.
3. **"Cluster customers on SoW to find low-SoW segments."** K-means finds **8** stable clusters (ARI **0.89**) whose FY25 SoW spans **79pp**; a year later the same customers sit **2.3pp** apart, and the clusters explain **0.04%** of next year's SoW (`seg_kmeans_k`, `seg_kmeans_ari`, `seg_kmeans_fy25_sow_spread_pp`, `seg_kmeans_fy26_sow_spread_pp`, `seg_kmeans_eta2`) **M**

**Lessons (bottom band)**
1. **Calendar-adjust everything.** A portfolio-wide drift poses as individual "attriters" and "decayers".
2. **Test whether customers differ before segmenting them.** The gate takes minutes.
3. **A portfolio-wide drift needs a portfolio-wide fix.** Targeting "low-SoW customers" would pick them at random.

**Speaker notes:**
- **Closures (Devansh's X5):** usage adds no closure signal beyond card age. Don't say usage carries no signal: on its own it scores ROC-AUC 0.567, but only as a stand-in for card age (`x5_usage_roc_auc`).
- **The appendix table (X1–X17)** holds the other tests. Mine are:
  - X8 Prime;
  - X9 category;
  - X10: credit limit never binds (median **1.2%** of the limit; no customer-month at ≥ 50%);
  - X11: no festive spike (monthly index **91–109**);
  - X12: Wallet isn't the winner;
  - X13: no never-activated segment;
  - X14: ticket and category mix don't persist (r ≈ **0.00**);
  - X17: returns are **10.1%** for every method.

---

## Numbers that differ from the 23 Oct stubs (from `outputs/verification/verification_report.md`)
Use the pipeline value in the deck. Only F9 changes a sentence:
- **F9 (slide 8, Devansh):** closures per open card are **1.8% (Jul–Sep 2024) → 4.0% (Apr–Jun 2026)** by calendar quarter (`f9_rate_first`, `f9_rate_last`), not 1.7% → 3.4%. Say "more than doubled".
- **F6:** HSIC is used on 25.6% of high tickets (the stub said 25.5%). The 23 Oct terciles put capped category-7 rows in the middle tercile.
- **X13:** the chance level is 26.9%, not 25.7%. The stub used one pooled HSIC rate for all 24 months, which makes the result even closer to chance.
- **X3:** the time-aware excess is +0.4 / 0.0 / −0.3pp (stub +0.7 / +0.1 / +0.0).
- **X11:** the index runs 91–109 on net sales; the stub's 92–108 used gross.
- **F13:** r = 0.43 / 0.23 (stub 0.44 / 0.22).
- **X14:** r ≈ 0.00 either way.

The message is unchanged in every case.
