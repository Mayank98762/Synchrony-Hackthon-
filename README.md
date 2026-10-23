# MetroMart–HSIC: Silent Attrition & Share of Wallet

Our entry for the **Synchrony Analytics Hackathon 2026** case study. HSIC Bank and MetroMart issue a co-branded credit card, but cardholders are moving their MetroMart spend onto other payment methods. We measure how much **Share of Wallet (SoW)** the card is losing, find who is quietly attriting, segment the low-SoW customers and design targeted rewards to win the spend back.

> **Status:** the plan is final, and implementation hasn't started yet.
> **Deliverable:** slides as a PDF, emailed to the organisers by **8:00 PM IST, 24 Oct 2026**.
> **Full plan:** [PROJECT_PLAN.md](PROJECT_PLAN.md) · **Task board:** [TASKS.md](TASKS.md)

## Objectives (from the case brief)
1. Analyse 2 years (FY25 + FY26, fiscal year Aug–Jul) of MetroMart and HSIC transactions.
2. Find insights on silent attrition and declining SoW, computed on **net** sales during **active-card** periods only.
3. Build segments, using a model or method, that identify low-SoW customers.
4. Create targeted offers that increase card usage at MetroMart.

## What we already know (profiling)
- **SoW fell from 28.9% in FY25 to 19.5% in FY26** (by quarter, 33% down to 15%). The lost share went mainly to Cash/UPI, Debit and other banks' cards.
- **Reward paradox:** Prime members use the card for Grocery and Electronics *no more* than Non-Prime members, even though they earn 5%/3% there.
- **6,227 of the 7,664 customers who closed their card still shop at MetroMart.**
- **The data is sparse.** There are only about 2.5 rows per customer per 6 months, so the naive "zero HSIC use" measure overstates silent attrition about 3×. That finding shaped our whole method.

## Planned features
**Mandatory analysis**
- SoW computed under the brief's rules.
- Attrition classes (explicit, silent, decliner, never-activated).
- Low-SoW segments.
- Targeted offers.
- An assumption ledger.

**Model comparisons:** each one is checked with time-based validation, leakage controls, bootstrap confidence intervals and a written failure analysis.

| ID | Problem | What competes |
|---|---|---|
| C1 | Predicting card closure | Recency rule vs logistic regression vs gradient boosting (+ random forest and Cox model if time allows) |
| C2 | Detecting a SoW decline in sparse data | Naive change vs empirical-Bayes vs Bayesian posterior vs Fisher test with false-discovery control |
| C3 | Segmentation | SoW quartiles vs rule-based personas vs K-means vs Gaussian mixture |
| C4 | Offer economics (simulated) | Blanket cashback vs category boost vs bonus above the customer's baseline vs instant credit |

**Selected USPs:** SoW Bridge · Reward paradox and "₹ left on the table" · Early-Warning Score · Pre-closure decay curve · Payment-switching Sankey · Explainable segments · Next-Best-Offer engine · Reward economics what-if · SoW simulator · Campaign test design and ROI · Customer 360 · Onboarding cliff · Big-ticket 0% EMI gap · Campaign calendar · Executive story dashboard · Data trust panel · Noise-adjusted silent attrition · Model Lab · Failure Atlas · Impact Ledger · Operating playbook.

**Impact reporting:** every ₹ figure is tagged **Measured**, **Simulated** or **Assumed**. Headline claims are given as measured loss + break-even uplift + simulated range, never as guaranteed recovery.

## Repository structure
```
├── README.md            # this file
├── PROJECT_PLAN.md      # finalised plan: scope, methods, experiments, USPs, phases
├── TASKS.md             # actionable task board with priorities and dependencies
├── sow_analysis.ipynb   # (planned) the only analysis code
├── outputs/             # (planned) CSVs, charts, model_eval/, impact_ledger.csv, key_numbers.md
└── dashboard/           # (planned) index.html, app.js, data/*.json
```
The case-study data (`Customer Data.csv`, `Transactions Data.csv`, `Category Code.csv`, `Payment Code.csv`) and the case PDF go in the repo root. Whether they are committed is up to the repo owner (see "Data handling").

## Getting started
1. Install **Anaconda (Python 3.13)**. Every library we need is already in the base environment: pandas, numpy, matplotlib, scikit-learn, statsmodels, scipy and Jupyter. Nothing else needs installing.
   - On Windows, use Anaconda's `python.exe` or Jupyter rather than the Microsoft Store `python` stub.
2. Put the four case CSVs in the repo root, using the original file names.
3. Open `sow_analysis.ipynb` and use **Restart & Run All**. Every validation assert has to pass.
4. Results are written to `outputs/`. The dashboard reads `dashboard/data/*.json`, so open `dashboard/index.html` in a browser.

## Team workflow
- **Pick a task** from [TASKS.md](TASKS.md), add your name in the Owner column and stick to its dependencies.
- **One branch per task** (`task/T12-c1-models`). Open a small PR into `main` and get one teammate to review it.
- **Notebook hygiene**
  - Clear outputs before you commit.
  - Keep sections in the order given in PROJECT_PLAN.md §5.
  - Don't edit sections you don't own without coordinating first, because notebook merges conflict easily.
- **No hand-typed numbers.** Every figure in the deck must come from `outputs/key_numbers.md` or `outputs/impact_ledger.csv`.
- **Rules are fixed in advance.** Selection rules for model comparisons go into `outputs/model_eval/selection_log.md` *before* any model runs. Don't re-tune after you've seen the test results.
- **Label every simulation.** Any number that depends on an assumption is tagged Simulated or Assumed.
- **Changing scope** means updating PROJECT_PLAN.md in the same PR, with a one-line reason.
- **Deadline:** the deck freezes at about 5 PM IST on 24 Oct and gets emailed by 7 PM (subject line = roll number only).

## Data handling
- Don't commit secrets, tokens or credentials, or local tool settings (`.claude/`).
- The case data is hackathon material. Check the organisers' rules before pushing it to a public repo.
