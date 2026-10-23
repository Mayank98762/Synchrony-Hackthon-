# MetroMart–HSIC: Silent Attrition & Share of Wallet

Our entry for the **Synchrony Analytics Hackathon 2026** case study. HSIC Bank and MetroMart issue a co-branded credit card, and cardholders are paying for more of their MetroMart shopping with other methods. We measure the loss in **Share of Wallet (SoW)**, test where it comes from, decide who to prioritise and design offers to win the spend back.

> **Status:** plan v5.3 is final, and implementation is starting. Two independent EDAs agree on every core number.
> **Deliverable:** slides as a PDF, emailed to analyticshiring@syf.com by **8:00 PM IST, 24 Oct 2026**. The subject line is the roll number only.
> **Full plan:** [PROJECT_PLAN.md](PROJECT_PLAN.md) · **Task board:** [TASKS.md](TASKS.md)

## The answer
SoW fell from **28.9% (FY25) to 19.5% (FY26)**. Customers didn't shop less: MetroMart spend per card stayed flat while HSIC spend per card halved (₹356 → ₹167).

**This is silent attrition, and it is universal.** Nearly every open card is quietly losing share at the same rate, whatever the customer type. Customers don't differ in how often they use the card: the spread between them is what coin flips would produce, and this year's share doesn't predict next year's. So the whole book is low-SoW, and HSIC has a **product problem, not a targeting problem**. The card is losing mainly to **Cash/UPI**, which took 47% of the lost share. HSIC lost ₹33M of spend. Net of the 1.39% in rewards HSIC pays, the margin on that spend is thin (₹0.04–0.43M at assumed rates), so the bank's real stake is retention and revolving balances.

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
  - card usage doesn't predict closure (AUC 0.52);
  - MetroMart's own Wallet isn't what is eating the card.
- **We target moments, not people.** Ticket size is the only behavioural signal in the data, so offers fire at checkout.
- **Break-even-first economics, net of rewards.** Every offer shows the shift rate it needs to pay for itself after the rewards HSIC funds, or says it never breaks even. Every ₹ figure is labelled Measured, Simulated or Assumed, and every "why" is labelled Hypothesis.

## Repository structure
```
├── README.md, PROJECT_PLAN.md, TASKS.md, requirements.txt
├── data/            # the 4 case CSVs (see "Data handling")
├── analysis/        # Python pipeline; run_all.py rebuilds every output
├── notebooks/       # story.ipynb: narrative walk-through, imports analysis/
├── outputs/         # key_numbers.md, impact_ledger.csv, experiment_log.csv, charts/, model_eval/
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
3. **Run the analysis:** `python analysis/run_all.py`. Every assert must pass. Outputs go to `outputs/` and `dashboard/public/data/`.
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
