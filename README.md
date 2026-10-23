# MetroMart–HSIC: Silent Attrition & Share of Wallet

Our entry for the **Synchrony Analytics Hackathon 2026** case study. HSIC Bank and MetroMart issue a co-branded credit card, and cardholders are paying for more of their MetroMart shopping with other methods. We measure the loss in **Share of Wallet (SoW)**, test where it comes from, decide who to prioritise and design offers to win the spend back.

> **Status:** plan v5.3 is final, and implementation is under way. Two independent EDAs agree on every core number. The pipeline, ML experiments, closure model and segmentation are done and merged to `main`. The findings, hypothesis tests and slides 4–7 are done on the `mayank` branch, waiting to merge. See [Progress](#progress) below and [TASKS.md](TASKS.md).
> **Deliverable:** slides as a PDF, emailed to analyticshiring@syf.com by **8:00 PM IST, 24 Oct 2026**. The subject line is the roll number only.
> **Full plan:** [PROJECT_PLAN.md](PROJECT_PLAN.md) · **Task board:** [TASKS.md](TASKS.md)

## The answer
SoW fell from **28.9% (FY25) to 19.5% (FY26)**. Customers didn't shop less: MetroMart spend per card stayed flat while HSIC spend per card halved (₹356 → ₹167).

**This is silent attrition, and it is universal.** Nearly every open card is quietly losing share at the same rate, whatever the customer type. Customers don't differ in how often they use the card: the spread between them is what coin flips would produce, and this year's share doesn't predict next year's. So the whole book is low-SoW, and HSIC has a **product problem, not a targeting problem**. The card is losing mainly to **Cash/UPI**, which took 47% of the lost share. HSIC lost ₹33M of spend. Net of the 1.399% in rewards HSIC pays, the margin on that spend is thin (₹0.03–0.43M at assumed rates), so the bank's real stake is retention and revolving balances.

Our recommendation:
1. **Fix the product for everyone, starting with reward visibility.** No rival card matches HSIC's Grocery and Electronics rates, yet Prime members use the card like everyone else and left ₹1.60M of cashback on the table. Showing the reward at the till costs almost nothing. Next come instant cashback at the till and the card on UPI.
2. **Trigger offers on the purchase itself:** no-cost EMI on big baskets, a streak bonus on small ones.
3. **Prioritise with a 2×2 of purchase frequency at MetroMart × closure risk (card age).** SoW is the same in every box; value and risk are not. Add the 6,227 closed cardholders who still shop (₹91.2M of spend after closure). Young cards matter most: cards under 6 months old close at 14.7% within six months, about 5× the rate of cards over 3 years old.

Why customers moved to Cash/UPI (immediacy?) and why Prime members ignore their rates (awareness?) are **hypotheses**. The pilot's holdout groups are designed to test them.

## What makes this entry different
- **We test before we segment.** A three-part heterogeneity gate (variance ratio 1.00, split-half r ≈ 0, year-over-year r = 0.00) shows that clustering customers on SoW would produce confident-looking noise.
- **We measure silent attrition against the trend.** The usual count labels about 21pp of cardholders "silent attriters" who are behaving exactly like everyone else. Once the portfolio-wide trend is accounted for, the decline is universal, not concentrated.
- **We show the common hypotheses we tested and what the data said:**
  - the pre-closure "decay curve" disappears after calendar adjustment;
  - card usage adds nothing to closure prediction beyond card age, and card age alone (AUC 0.672) beats every learned model;
  - MetroMart's own Wallet isn't what is eating the card.
- **We target moments, not people.** Ticket size is the only behavioural signal in the data, so offers fire at checkout.
- **Break-even-first economics, net of rewards.** Every offer shows the shift rate it needs to pay for itself after the rewards HSIC funds, or says it never breaks even. Every ₹ figure is labelled Measured, Simulated or Assumed, and every "why" is labelled Hypothesis.

## Progress
As of 24 Oct. Owners and task IDs are in [TEAM_SPLIT.md](TEAM_SPLIT.md) and [TASKS.md](TASKS.md).

**Done (Devansh)**

| Piece | File | Result |
|---|---|---|
| Environment | `requirements.txt` | `synchrony` conda env, versions pinned (pandas 3.1, scikit-learn 1.9) |
| Foundation | `analysis/config.py`, `analysis/prep.py` | Loads and validates the 4 CSVs and applies the brief's rules; shared helpers for SoW, the 6-month window, card age and purchase frequency. Interface: `analysis/INTERFACE.md` |
| Decision rules | `outputs/model_eval/selection_log.md` | Every threshold fixed before the final run; later changes are listed in its change log |
| Heterogeneity gate | `analysis/experiments_ml.py` | Customer SoW fails all three tests (variance ratio 1.00, split-half r −0.005, persistence r 0.004). X2, X7, X15 and X16 also done |
| Closure model | `analysis/closure_model.py` | Card age alone (ROC-AUC 0.672) beats every learned model, so the card-age rule ships. Its top 10% riskiest cards close at 15.7% vs 6.2% overall. Usage adds nothing beyond card age |
| Segmentation | `analysis/segments.py` | K-means looks stable (ARI 0.89) but explains 0.04% of next year's SoW. 2×2 boxes: SoW within 1.7pp; young cards close 7.7pp more often; high-frequency customers spend ₹2,255 more off-card |
| Pipeline | `analysis/run_all.py`, `export.py`, `checks.py` | One command, about 3 minutes, deterministic. 39 reproduction checks: 18 pass, 0 fail, 21 pending on teammates' modules |
| Handoffs | `HANDOFF_MAYANK.md`, `HANDOFF_SHREYASH.md` | What each teammate uses, from which file, for which slide |

**Done (Mayank, on the `mayank` branch, not merged yet)**

| Piece | File | Result |
|---|---|---|
| Findings F1–F11, F13, F14 | `analysis/experiments_f.py` | Built on `prep.py`; 205 keys (with X tests) in `key_numbers.md`. All 19 of Mayank's reproduction checks in `checks.py` pass, so `run_all.py` now reports 37 pass, 0 fail, 2 pending (Shreyash's F12, F15) |
| Hypothesis tests X3, X4, X8–X14, X17 | `analysis/experiments_h.py` | Each returns a verdict from `config.VERDICT`. Silent attrition is universal (time-aware excess +0.4 / 0.0 / −0.3pp vs +21pp by the usual count); no pre-closure decay after calendar adjustment (slope +0.08pp a month, CI −0.09 to +0.25) |
| Verification (§14) | `analysis/verify.py`, `analysis/verify_second.py` | 0 blocking failures. Every 23 Oct stub checked; 4 misses have a found cause, and 7 can't be reproduced (what was tried is listed, the message is unchanged). 3 customers traced from raw rows to segment and offer. Independent rebuild from the raw CSVs, including Devansh's X1 band table: 91/91 |
| Slides 4–7 and charts | `deck/slides_04-07.md`, `analysis/charts_story.py` | Drop-in slide content with a key for every number; 12 charts at 16:9 (`outputs/charts/04_*`–`07_*`), including the gate, band table and K-means control from Devansh's outputs |
| Notebook | `notebooks/story.ipynb` | Walk-through of slides 4–7 that imports `analysis/`; runs without errors |

**In progress / next**
- **Mayank:** merge the `mayank` branch; swap the charts to Shreyash's `style.py` when it lands; tell Devansh F9 is 1.8% → 4.0% for slide 8.
- **Shreyash:** `style.py`, `economics.py` (with the 3 review fixes in his handoff), F12 and F15, slides 1–3 and 10–12, deck integration and submission.
- **Devansh:** charts and content for slides 8–9; the final `run_all.py` once the teammates' modules land; the 4-page dashboard (optional, cut first).

## Repository structure
```
├── README.md, PROJECT_PLAN.md, TASKS.md, TEAM_SPLIT.md, requirements.txt
├── HANDOFF_MAYANK.md, HANDOFF_SHREYASH.md   # what each teammate uses and where
├── data/            # the 4 case CSVs (gitignored; see "Data handling")
├── analysis/        # Python pipeline; run_all.py rebuilds every output; INTERFACE.md lists helpers and key names
├── notebooks/       # story.ipynb: narrative walk-through, imports analysis/
├── outputs/         # key_numbers.md/.json, impact_ledger.csv, experiment_log.csv, tables/, model_eval/, charts/
└── dashboard/       # optional 4-page React + Vite + ECharts app; reads dashboard/public/data/*.json
```
`synchrony_hackathon_strategy_blueprint.md` is an earlier brainstorm, kept for reference. Plan v5.3 supersedes it.

## Getting started
1. **Create the conda env** (Miniconda). Nothing is installed globally:
   ```bash
   conda create -n synchrony python=3.12 nodejs=20 -y
   conda activate synchrony
   pip install -r requirements.txt
   ```
2. **Add the data:** put `Customer Data.csv`, `Transactions Data.csv`, `Category Code.csv` and `Payment Code.csv` in `data/`, keeping the original file names.
3. **Run the analysis:** `python analysis/run_all.py` from the repo root, inside the `synchrony` env (about 3 minutes). It fails on any failed check; checks whose module doesn't exist yet show as pending. Outputs go to `outputs/`; the deck takes every number from `outputs/key_numbers.md`.
4. **(Optional) run the dashboard:**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
   For a static build, run `npm run build`; the output goes to `dashboard/dist/`.

## Team workflow
- **Pick a task** from [TASKS.md](TASKS.md), put your name in the Owner column and respect its dependencies. There are three tracks: Analysis, Charts & polish, and Deck. **The deck comes first.**
- **One branch per task** (e.g. `task/A05-closure-model`). Keep PRs small; one teammate reviews each.
- **No hand-typed numbers.** Every figure in the deck comes from `outputs/key_numbers.md`.
- **Decision rules are fixed before the final run.** Write them into `outputs/model_eval/selection_log.md` before the final `run_all.py`, and don't change them afterwards. Don't call this pre-registration in the deck.
- **In the deck:**
  - call rejected ideas "common hypotheses we tested", and never name our earlier plans;
  - label every simulation Simulated or Assumed, and every unproven "why" Hypothesis.
- **Changing scope** means updating PROJECT_PLAN.md in the same PR, with a one-line reason.
- **Deadline:** the deck freezes at about 5 PM IST on 24 Oct and is emailed by 7 PM.

## Data handling
- Don't commit secrets, tokens, credentials or local tool settings (`.claude/`).
- The case data is hackathon material. Check the organisers' rules before pushing it to a public repo.
- **Only aggregate files go in `outputs/`.** No file with one row per customer: `run_all.py` fails if a new one appears, and `.gitignore` blocks `outputs/**/*customer*.csv`. The older `outputs/eda/customer_sow_segments.csv` is customer-level and should be removed.
