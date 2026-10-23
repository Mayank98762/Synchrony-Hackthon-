# Handoff: Shreyash (economics, offers, deck integration)

What you build, which inputs to use, what number to expect, and where each result ends up.
Your scope comes from [TEAM_SPLIT.md](TEAM_SPLIT.md); the rules come from [PROJECT_PLAN.md](PROJECT_PLAN.md) v5.3 §8 and [outputs/model_eval/selection_log.md](outputs/model_eval/selection_log.md) §8–§9.

## 0. Setup

1. `conda create -n synchrony python=3.12 nodejs=20 -y`, then `conda activate synchrony` and `pip install -r requirements.txt` (pinned: pandas 3.1, numpy 2.5).
2. Put the 4 case CSVs in **`data/`**, and check with `python -m analysis.prep` (expect SoW 0.2891 / 0.1948).
3. `economics.py` takes plain numbers, so you can start before any data module lands. Use the stub values below.

## 1. Hour 1: `analysis/style.py` (everyone waits on this)

Please expose exactly these names, so Devansh's and Mayank's chart code can call them without changes:

| Name | What |
|---|---|
| `apply()` | Sets matplotlib rcParams (fonts, grid, spines, background) |
| `COLORS` | dict: `ink`, `muted`, `grid`, `bg`, `hsic` (hero), `accent` |
| `METHOD_COLORS` | dict keyed by `payment_short`: `HSIC`, `Cash/UPI`, `Wallet`, `Debit`, `Other CC` |
| `BADGE_COLORS` | dict: `Measured`, `Simulated`, `Assumed`, `Hypothesis` |
| `save(fig, slide, name)` | Writes `outputs/charts/{slide:02d}_{name}.png`, 16:9, 200 dpi |

Use `config.CHARTS` for the folder.

## 2. `analysis/economics.py`

**Rules (selection_log §8: please read it):**
- **Net margin per ₹** = interchange + revolve income − reward rate × (1 − co-funding). Take the values from `config.SCENARIOS` (conservative / base / optimistic).
- **Reward rate** = the rate on *the spend being shifted*:
  - general spend: the pipeline-measured FY26 effective rate, **1.399%**. Compute it with `prep` (active FY26 HSIC rows: `reward.sum() / net.sum()`); never hard-code 1.39%.
  - Prime Grocery / Electronics: 5% / 3%.
- **`never`** is a valid output. If the incentive per incremental ₹ is ≥ the net margin (or the required shift is > 100%), return the string `"never"`.
- Also report each offer's **break-even revolve rate**: the revolve income (% of spend) at which it breaks even, with every other input at base.
- Every simulated ₹ is labelled Simulated; every input from `SCENARIOS` is labelled Assumed.

**Three issues from the 23 Oct review that your module has to handle honestly:**
1. **The hero offer (O3) is margin-negative on Prime Grocery in the conservative case.** It moves spend that earns 5%. Net margin per ₹ shifted:

   | Scenario | Prime Grocery (5%) | Prime Electronics (3%) |
   |---|---|---|
   | Conservative | −3.5% | −1.5% |
   | Base | +0.25% | +1.25% |
   | Optimistic | +1.5% | +2.5% |

   Say so. The ₹1.60M "left on the table" is the customer's gain and HSIC's cost. That turns "MetroMart co-funds Prime category rewards" into an ask on slide 12, and until it's agreed, O3 leads on 1% baskets.
2. **Retention value is small.** HSIC spend per open card is about ₹2,214 a year, so a retained card is worth roughly ₹2 (conservative) to ₹45 (base) a year in net margin. O6 and O7 will probably come out `never` without revolve income. Report it, lead with the break-even revolve rate, and don't claim retention "pays".
3. **50% co-funding is generous.** Moving a payment from UPI to card costs MetroMart a merchant fee. Put one line in the limitations.

**Inputs you need, with stub values to use until the real ones land:**

| Input | Stub | Real source (owner) | Key |
|---|---|---|---|
| FY26 effective reward rate | 0.01399 | `prep` (you) | `f15_reward_rate_fy26` |
| ₹ gap at constant SoW | ₹33.4M | F12 (you) | `f12_gap` |
| HSIC / total active net FY25, FY26 | ₹85.7M / ₹296.3M; ₹68.9M / ₹353.8M | F12 (you) | `f12_*` |
| Prime G+E spend on other methods FY26 | ₹47.4M | F8 (Mayank) | `f8_prime_ge_other_net` |
| Post-closure spend, closers still shopping | ₹91.2M, 6,227 | F11 (Mayank) | `f11_*` |
| Ticket-band mix (O4 ≥ ₹3k, O5 < ₹1k eligible spend) | see F5 in the plan | F5 (Mayank) | `f5_*` |
| Box sizes, closure rate, non-HSIC ₹ / customer, Prime share | B 2,226 · 11.6% · ₹6,235; C 4,942 · 12.1% · ₹3,976; D 6,744 · 4.2% · ₹6,393; E 15,286 · 4.3% · ₹4,139 (built at 2026-01-31) | `segments.py` (Devansh) | `seg_<B..E>_n`, `_closure_6m`, `_nonhsic_per_cust`, `_prime_share` |
| Segment A size and spend after close | **5,903 · ₹92.3M** at 2026-07-31 (pipeline). F11's 6,227 / ₹91.2M also counts return-only customers; use 5,903 on slides 9–11 | `segments.py` (Devansh) | `seg_A_n_score`, `seg_A_post_close_net` |
| Box sizes at production assignment (2026-07-31) | B 1,961 · C 4,352 · D 7,486 · E 16,720 · F 6,836 | `segments.py` (Devansh) | `seg_<X>_n_score` |
| HSIC row share p and purchases per customer per 3 months, per box (for the MDE) | p ≈ 0.16; n from segments | `segments.py` (Devansh) | `seg_<box>_p_hsic`, `seg_<box>_rows_3m` |

**Outputs:** `run() -> dict`, with keys like:
- `o3_breakeven_shift_base`;
- `o6_breakeven_revolve`;
- `o7_value_conservative` (a number or `"never"`);
- `f15_net_margin_lost_lo` / `_hi`;
- `mde_<box>`.

Charts: `11_net_margin_waterfall.png` (interchange → rewards → co-funding → net) and `11_breakeven.png` (by offer × scenario, with `never` shown as a marker, not a bar).

## 3. F12 and F15 (your own section in `experiments_f.py`)

Mayank owns the file. Keep your code in a separate section at the bottom, with no shared helpers, so merges stay clean.

| ID | Compute | Stub |
|---|---|---|
| F12 | HSIC and total active net by FY; FY26 HSIC at FY25 SoW; the gap | ₹85.7M → ₹68.9M; total ₹296.3M → ₹353.8M; gap ≈ ₹33M |
| F15 | Gross interchange on the gap (1.5–2%); rewards HSIC would have paid (1.399%); net lost margin at 0% and 50% co-funding; per 10,000 cardholders | gross ₹0.50–0.67M; rewards ₹0.47M; net ₹0.03–0.20M (no co-funding), ₹0.27–0.43M (50%) |

**Never quote gross interchange without the net-of-rewards figure beside it.**

## 4. Your slides and where each number comes from

| Slide | Message | Numbers (key → owner) |
|---|---|---|
| 1 Title | — | — |
| 2 Executive summary | Silent attrition is real and universal: 9.4pp, ₹33M of spend, the same for every customer type. Net of rewards the margin is thin, so the stake is retention and revolving balances. 3 findings, 3 actions (reward visibility first) | `f1_*`, `f14_*` (Mayank); `f12_gap`, `f15_*` (you); `x1_*` (Devansh) |
| 3 Data, rules, assumptions | Brief compliance; label legend (Measured / Simulated / Assumed / Hypothesis) | `selection_log.md` §1, PROJECT_PLAN §2 and §9 |
| 10 Offers | Three only: O3 reward visibility (₹1.60M; H-aware), O1 instant cashback (H-imm), O2 card on UPI. O4–O8 on one line each | `f8_*` (Mayank); `o*_` (you) |
| 11 Economics & pilot | Net margin after rewards; break-even by scenario incl. `never`; break-even revolve; holdout + MDE; O3 tests H-aware, O1 tests H-imm | `o*_`, `mde_*` (you); `seg_*` (Devansh) |
| 12 Roadmap & asks | Ask MetroMart to co-fund Prime category rewards; pilot; dashboard link + screenshots if built | — |
| Appendix | 17-hypothesis table, closure-model table, gate details, assumptions, limitations | `outputs/experiment_log.csv`, `cm_*`, `x1_*` (Devansh); `x*` (Mayank) |

## 5. Deck integration and submission

- **Hour 4:** you get the first `key_numbers` dict from Mayank and Devansh. Fill `[KN:key]` placeholders from it.
- **Hour 8:** Devansh sends the final `outputs/key_numbers.md`. Replace every `[KN:key]`; no number is typed by hand.
- **Final consistency pass:**
  - silent attrition is "universal", never "rejected";
  - every "why" carries a Hypothesis label;
  - no gross interchange without the net figure;
  - no v4, blueprint or "pre-registered".
- **Submit:** export the PDF and email it to **analyticshiring@syf.com** before **8:00 PM IST, 24 Oct**. The subject line is the roll number only. Attach the file; no Drive link.
