# Slides 8 and 9: content for the deck (Devansh)

Ready to paste into Shreyash's template. Every number below comes from `outputs/key_numbers.md` (key in brackets) or from a chart built by `analysis/charts_ml.py`. Charts are in `outputs/charts/`, 16:9 at 200 dpi, and restyle automatically once `analysis/style.py` exists (rerun `python analysis/run_all.py`).

**Wording rules for both slides** (plan §12 and the selection log):
- Say "4.8×" or "nearly 5×", never "5×": 14.73% ÷ 3.04% = 4.8.
- Say "no learned model beats card age alone", not "card age beats every model": the best model trails by only 0.003.
- Say "usage adds nothing **beyond card age**", not "usage doesn't predict closure": on its own it scores 0.567, because young cards have little usage history.
- Every "why" is labelled **Hypothesis**. Every number here is **Measured**.
- Never name earlier plans, and don't call the decision rules pre-registered.

---

## Slide 8: Closures

**Headline:** Closures have doubled, and they are a young-card problem

**Sub-headline:** A card's age predicts closure better than anything it does

### Layout
| Position | Content |
|---|---|
| Left, about 60% | `08_closure_by_card_age.png` (hero chart) |
| Right top | `08_closures_per_quarter.png` |
| Right bottom | Stat tile: **₹91.2M** spent at MetroMart after closing the card, by **6,227** customers |
| Footer strip | One line on the model result (below); the full model chart goes to the appendix |

`08_closure_model_auc.png` belongs in the appendix (closure-model table). Swap it in for the quarterly chart only if the slide needs the model result more than the trend.

### Body (3 bullets)
1. **Closures per open card doubled**, from 1.7% a quarter (Jul–Sep 2024) to 3.4% (Apr–Jun 2026). *(F9; chart `08_closures_per_quarter`)*
2. **Cards under 6 months old close at 14.7% within six months**, 4.8× the 3.0% rate of cards over 3 years old. *(F10; chart `08_closure_by_card_age`)*
3. **Closing the card doesn't mean leaving MetroMart:** 6,227 closed cardholders kept shopping and spent ₹91.2M there after closing. *(F11: `f11_post_close_net`; the plan's verified figure, until Mayank's key lands)*

### Footer line (model result)
No learned model beats card age alone: ROC-AUC 0.672 vs 0.669 for the best model *(`cm_b2_roc_auc`, `cm_lr_all_roc_auc`)*. Card-usage features add nothing beyond card age *(`x5_usage_increment_roc` ≈ 0)*, so we ship a simple rule: watch the youngest cards.

### Labels
- All numbers: **Measured**.
- If the slide says why young cards close, label it **Hypothesis** (for example: "the card never becomes a habit in the first months"). The data shows *who* closes, not *why*.

### Speaker notes (about 60 seconds)
> Closures are the visible half of the problem, and they're accelerating: the share of open cards closing each quarter doubled in two years, from 1.7% to 3.4%.
> The question is who closes. We trained logistic regression and gradient boosting on every profile and usage feature we have, and tested them on a later period. None of them beat one number: how old the card is. Cards under six months close at 14.7% over the next six months, nearly five times the rate of cards over three years old. The youngest tenth of cards catches a quarter of all closures.
> Usage looks predictive on its own, but only because new cards haven't had time to build a history. Within young cards, or within mature cards, usage adds nothing. So the early-warning system is a rule, not a model: protect cards in their first year.
> And closing the card doesn't mean the customer left. 6,227 people closed their card and still spent ₹91.2 million at MetroMart afterwards. That's spend HSIC used to be positioned to win, and it's our win-back segment on the next slide.

### If a judge asks
| Question | Answer (key) |
|---|---|
| How was the model tested? | Trained on cards open on 31 Jul 2025, tested once on cards open on 31 Jan 2026: 29,198 cards, 1,799 closures (`cm_test_cards`, `cm_test_closers`) |
| Is the gap between card age and the model real? | Yes but tiny: −0.003 ROC-AUC, 95% CI −0.005 to −0.001 (`cm_vs_b2_roc_diff`, `cm_vs_b2_ci_lo/hi`). The point is that the model adds nothing |
| How good is the card-age rule in practice? | The youngest 10% of cards (under about 0.48 years) catch 25.5% of closers and close at 15.7% vs 6.2% overall (`cm_b2_top_decile`, `cm_test_base_rate`, `closure_gain_by_decile.csv`) |
| Gradient boosting vs logistic regression? | Boosting is worse: −0.009, CI −0.014 to −0.004 (`x6_hgb_minus_lr`) |
| Does it hold at the earlier cutoff? | Card-age ROC-AUC 0.611 at 31 Jul 2025 (`base_card_age_auc_train`) |
| Is it fair by gender? | Similar: 0.667 for women, 0.674 for men (gender is never a model input) |

---

## Slide 9: Who to prioritise

**Headline:** Low SoW is the whole book, so we prioritise by risk and value

**Sub-headline:** The obvious method finds noise; card age and purchase frequency are what actually separate customers

### Layout
| Position | Content |
|---|---|
| Left, about 35% | `09_kmeans_control.png`, captioned "The obvious method: cluster on SoW" |
| Right, about 65% | `09_priority_matrix.png`: the answer |
| Footnote | Reconciles segment A with slide 8 (below) |

`09_box_outcomes.png` shows the same evidence as bars with confidence intervals. Put it in the appendix ("Segment validation"), or use it instead of the matrix if the template needs a chart rather than a diagram.

### Body (3 bullets)
1. **Clustering on SoW finds nothing that lasts:** 8 stable clusters that are 79 points apart in FY25 end up 2.3 points apart in FY26, and they explain 0.04% of next year's SoW. *(`seg_kmeans_fy25_sow_spread_pp`, `seg_kmeans_fy26_sow_spread_pp`, `seg_kmeans_eta2`; stability ARI 0.89, `seg_kmeans_ari`)*
2. **So SoW can't separate customers, and the boxes prove it:** SoW is within 1.7 points in every box, while young cards close 7.7 points more often and high-frequency customers spend ₹2,255 more off-card. *(`seg_sow_max_gap_pp`, `seg_age_closure_diff`, `seg_freq_nonhsic_diff`)*
3. **Protect first: young cards with high purchase frequency** (1,961 customers). They carry the same closure risk as other young cards (11.6% vs 12.1%) with 57% more off-card spend (₹6,235 vs ₹3,976). *(`seg_B_n_score`, `seg_B_closure_6m`, `seg_C_closure_6m`, `seg_B_nonhsic_per_cust`, `seg_C_nonhsic_per_cust`)*

### Box summary (if the template wants a table instead of the matrix)
| Box | Who | Customers now | 6-month closure | Off-card ₹ per customer | FY26 SoW | Lever |
|---|---|---|---|---|---|---|
| **B. Protect first** | young, high frequency | 1,961 | 11.6% | ₹6,235 | 16.1% | Onboarding protection (O7) + reward visibility (O3) |
| C. Activate | young, low/mid frequency | 4,352 | 12.1% | ₹3,976 | 17.7% | Activation milestone + Prime trial (O7) |
| D. Grow | mature, high frequency | 7,486 | 4.2% | ₹6,393 | 17.1% | Threshold bonus (O8) + reward visibility (O3) |
| E. Nudge | mature, low/mid frequency | 16,720 | 4.3% | ₹4,139 | 17.2% | Product fixes only (O1–O5) |
| A. Closed, still shopping | outside the grid | 5,903 | — | ₹92.3M in total after closing | 0% | Win-back (O6) |

Keys: `seg_<box>_n_score`, `seg_<box>_closure_6m`, `seg_<box>_nonhsic_per_cust`, `seg_<box>_sow`, `seg_A_post_close_net`. Non-cardholders (F, 6,836 customers, `seg_F_n_score`) are acquisition at checkout, a stretch item.

### Footnote (segment A vs slide 8)
"6,227 closed cardholders kept shopping (₹91.2M net after closing); the 5,903 with positive net spend after closing form segment A (₹92.3M)." The difference is 324 customers whose returns after closing equalled or exceeded their purchases (net spend ≤ 0); 89 of them only made returns.

### Labels
- All numbers: **Measured**. Customer counts are as of 31 Jul 2026; closure and off-card spend come from boxes built on 31 Jan 2026 and measured Feb–Jul 2026.
- Offers are named here only. Their economics live on slide 11 (some may not break even; don't promise payback on this slide).

### Speaker notes (about 75 seconds)
> The brief asks for segments that identify low-SoW customers. The obvious way is to cluster customers on their SoW, so we did that first. K-means finds eight clean, stable clusters, from almost zero to nearly 80% SoW. But follow the same customers into the next year and they all land between 20 and 22%. The clusters explain less than a tenth of a percent of next year's SoW. It's regression to the mean: last year's light users weren't light users, they were unlucky.
> So the honest answer is that low SoW is the whole book: every open card is drifting off HSIC at the same rate. What does separate customers is risk and value. Card age predicts closure, as we saw on the last slide. Purchase frequency at MetroMart predicts how much spend is at stake, and it carries over from year to year. And the two are independent, which gives a clean two-by-two.
> SoW is the same in all four boxes, within under two points. Closure risk and value are not. The top priority is young, high-frequency cards: the same risk as other young cards, but far more spend to lose. Mature high-frequency customers get a bonus only on spend above their own usual level, so we don't pay for spend we'd get anyway. The large low-frequency mature group gets the product fixes only, with no paid incentive.
> Outside the grid are 5,903 people who closed the card but still spend at MetroMart: HSIC's share of their spend is zero, so they're the most literal low-SoW customers there are, and the win-back target.

### If a judge asks
| Question | Answer (key) |
|---|---|
| Aren't these just tenure segments? | They're risk × value segments, chosen because they're the only customer traits that predict anything. SoW itself fails our heterogeneity gate (variance ratio 1.00, persistence r ≈ 0: `x1_*`) |
| Are the two axes really independent? | 31.1% of young cards vs 30.6% of mature cards are high-frequency (`seg_young_top_share`, `seg_mature_top_share`) |
| Do the youngest cards differ from 6–12 months? | Yes: within B and C, cards under 6 months close about 5.7 points more often (CI 4.2–7.3, `seg_young_split_diff`); `segments_young_split.csv` has the split |
| How sensitive is the frequency cut? | Moving the cut down 10% moves 12.3% of customers between boxes; moving it up 10% moves none, because purchase counts are whole numbers (`segments_boundary.csv`) |
| Why not rank by ₹ at stake? | With equal usage odds, ₹ at stake is just spend times a constant, so we call it what it is: value, measured by purchase frequency |
| Where's Prime in this? | Within every box, reward visibility (O3) goes to Prime members first: the ₹1.60M they left on the table is theirs (slide 10) |
