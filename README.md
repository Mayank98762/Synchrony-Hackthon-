# MetroMart–HSIC: Silent Attrition & Share of Wallet

Our entry for the **Synchrony Analytics Hackathon 2026** case study. HSIC Bank and MetroMart issue a co-branded credit card, and cardholders are paying for more of their MetroMart shopping with other methods. We measure the loss in **Share of Wallet (SoW)**, test where it comes from, segment customers and design offers to win the spend back.

> **Status:** plan v5 is final, and implementation is starting.
> **Deliverable:** slides as a PDF, emailed to analyticshiring@syf.com by **8:00 PM IST, 24 Oct 2026**. The subject line is the roll number only.
> **Full plan:** [PROJECT_PLAN.md](PROJECT_PLAN.md) · **Task board:** [TASKS.md](TASKS.md)

## The answer
SoW fell from **28.9% (FY25) to 19.5% (FY26)**, and it fell at the **same rate for every kind of customer**. The data shows customers don't differ in how often they use the card: the spread between them is what coin flips would produce, and this year's share doesn't predict next year's. So HSIC has a **product problem, not a targeting problem**. The card is losing mainly to **Cash/UPI**, which took 47% of the lost share.

Our recommendation:
1. **Fix the product for everyone:** instant cashback at the till, reward visibility at checkout, and the card on UPI.
2. **Trigger offers on the purchase itself:** no-cost EMI on big baskets, a streak bonus on small ones.
3. **Target only groups that are real:** 6,227 closed cardholders who still shop (₹91.2M of spend after closure), and first-year cardholders, whose closure rate is 3× that of mature cards.

## What makes this entry different
- **We test before we segment.** A three-part heterogeneity gate (variance ratio 1.00, split-half r ≈ 0, year-over-year r = 0.00) shows that clustering customers on SoW would produce confident-looking noise.
- **We publish what failed.** 17 ideas from our earlier plans were tested and rejected with numbers. Examples:
  - "Silent attrition" shrinks from +21pp to 0 once the portfolio-wide trend is accounted for.
  - The pre-closure "decay curve" disappears after calendar adjustment.
  - Card usage doesn't predict closure (AUC 0.52).
  - MetroMart's own Wallet isn't what is eating the card.
- **We target moments, not people.** Ticket size is the only behavioural signal in the data, so offers fire at checkout.
- **Break-even-first economics.** Every offer shows the shift rate it needs to pay for itself. Every ₹ figure is labelled Measured, Simulated or Assumed.

## Repository structure
```
├── README.md, PROJECT_PLAN.md, TASKS.md, requirements.txt
├── data/            # the 4 case CSVs (see "Data handling")
├── analysis/        # Python pipeline; run_all.py rebuilds every output
├── notebooks/       # story.ipynb: narrative walk-through, imports analysis/
├── outputs/         # key_numbers.md, impact_ledger.csv, experiment_log.csv, charts/, model_eval/
└── dashboard/       # React + Vite + ECharts app; reads dashboard/public/data/*.json
```
`synchrony_hackathon_strategy_blueprint.md` is an earlier brainstorm, kept for reference. Plan v5 supersedes it.

## Getting started
1. **Create the conda env** (Miniconda). Nothing is installed globally:
   ```bash
   conda create -n synchrony python=3.12 nodejs=20 -y
   conda activate synchrony
   pip install -r requirements.txt
   ```
2. **Add the data:** put `Customer Data.csv`, `Transactions Data.csv`, `Category Code.csv` and `Payment Code.csv` in `data/`, keeping the original file names.
3. **Run the analysis:** `python analysis/run_all.py`. Every assert must pass. Outputs go to `outputs/` and `dashboard/public/data/`.
4. **Run the dashboard:**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
   For a static build, run `npm run build`; the output goes to `dashboard/dist/`.

## Team workflow
- **Pick a task** from [TASKS.md](TASKS.md), put your name in the Owner column and respect its dependencies. There are three parallel tracks: Analysis, Dashboard and Deck.
- **One branch per task** (e.g. `task/A05-closure-model`). Keep PRs small; one teammate reviews each.
- **No hand-typed numbers.** Every figure in the deck or UI comes from `outputs/key_numbers.md` or the exported JSON.
- **Rules come first.** Decision rules go into `outputs/model_eval/selection_log.md` before the code that tests them runs.
- **Label every simulation.** Anything that depends on an assumption is tagged Simulated or Assumed.
- **Changing scope** means updating PROJECT_PLAN.md in the same PR, with a one-line reason.
- **Deadline:** the deck freezes at about 5 PM IST on 24 Oct and is emailed by 7 PM.

## Data handling
- Don't commit secrets, tokens, credentials or local tool settings (`.claude/`).
- The case data is hackathon material. Check the organisers' rules before pushing it to a public repo.
