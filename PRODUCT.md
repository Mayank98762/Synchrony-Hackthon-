# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Primary: the Synchrony Analytics Hackathon 2026 judges** (Synchrony analytics hiring). They reach the dashboard from the link on slide 12 of the submitted PDF deck, if they open it at all, and skim fast. They are judging analytical rigour and judgement (whether the team tested its ideas before acting on them) as much as the headline finding.

The UI is framed as an analysis of the MetroMart–HSIC co-branded card portfolio. Judges are the people who actually use it.

## Product Purpose

HSIC Card Insights is the interactive companion to our hackathon entry. It shows why HSIC's Share of Wallet (SoW) at MetroMart fell from 28.9% (FY25) to 19.5% (FY26), what we tested to explain it, who to prioritise, and which offers would win the spend back.

It succeeds when a judge who opens it comes away believing the numbers and the reasoning: the decline is universal silent attrition (a product problem, not a targeting problem), and every claim is either measured or clearly labelled.

## Positioning

What sets this entry apart, and what a neighbouring entry couldn't truthfully claim:
- **We test before we segment.** A three-part heterogeneity gate (variance ratio 1.00, split-half r ≈ 0, year-over-year r = 0.00) shows that clustering customers on SoW would produce noise.
- **We measure silent attrition against the portfolio trend,** not by the usual count, which mislabels about 21pp of cardholders.
- **We show the common hypotheses we tested and what the data said,** including the ones that failed.
- **We target moments, not people.** Offers fire at checkout, because ticket size is the only behavioural signal.
- **Break-even-first economics, net of rewards.**

## Operating Context

- The deck decides the hackathon. The PDF is emailed to analyticshiring@syf.com by 8:00 PM IST on 24 Oct 2026, and the dashboard is a companion to it.
- Static site with no backend. It reads precomputed aggregate JSON in `dashboard/public/data/*.json` (overview, segments, attrition, priority), which `python analysis/run_all.py` rebuilds.
- The data covers 45,000 cardholders, Aug 2024 – Jul 2026, from the four case CSVs.
- Four pages: Share of wallet (Story), Segments, Attrition & closures, Priorities & offers. Routing is hash-based.
- It may be hosted as a private claude.ai Artifact or on GitHub Pages; the owner decides whether to share it.

## Capabilities and Constraints

- **Numbers come from the pipeline only.** Every figure in the UI comes from the JSON that `run_all.py` writes (the same objects as `outputs/key_numbers.md`). Never type a number into the UI by hand.
- **Evidence labels are required.** Every ₹ figure is labelled **Measured**, **Simulated** or **Assumed**. Every causal "why" the data can't test (e.g. immediacy driving the move to Cash/UPI, or low reward awareness among Prime members) carries a **Hypothesis** label.
- **Terminology:**
  - **SoW:** HSIC card spend at MetroMart ÷ the cardholder's total MetroMart spend.
  - **Silent attrition:** losing share while the card stays open.
  - **Card age:** time since the card was opened.
  - **Purchase frequency at MetroMart:** how often the customer shops at MetroMart.
  - **Closed but still shopping:** 6,227 customers with ₹91.2M of spend after closure.
  - Rejected ideas are "common hypotheses we tested". Never name earlier internal plans, and never claim pre-registration.
- **Planned interactions** (PROJECT_PLAN §11):
  - a slice selector on Segments;
  - a raw vs calendar-adjusted toggle for the pre-closure curve;
  - a shift-rate slider per offer, with Simulated badges on its outputs.
- **Open:** the break-even column fills in only after Shreyash's `economics.py` lands and the final `run_all.py` runs.

## Brand Commitments

- HSIC Bank and MetroMart Inc. are fictional case brands. The case supplies no logo, palette or identity.
- **Stay consistent with the deck.** The dashboard must visually match whatever the deck uses (Shreyash's `analysis/style.py` once it lands), so the screenshots on slide 12 read as one entry.
- The current blue (`#2a78d6` in `analysis/_style_fallback.py`, darkened to `#2470cc` in the dashboard) is a placeholder palette, not an HSIC brand colour.

## Evidence on Hand

- `outputs/key_numbers.md` / `.json`: every reported number (205+ keys).
- `dashboard/public/data/*.json`: the dashboard's aggregate data (~35 kB).
- `outputs/charts/04_*`–`09_*`: deck charts. `outputs/eda/`: EDA report and tables.
- `deck/slides_04-07.md`, `deck/slides_08_09.md`: slide content and speaker notes.
- **Absent, and never to be fabricated:** testimonials, customer quotes, real brand assets, pilot results, and any measured effect of the offers (the offers are simulated, and the pilot is only proposed).

## Product Principles

1. **Every number traces to the pipeline.** If it's not in the JSON, it's not on the screen.
2. **Label the evidence.** Measured, Simulated, Assumed and Hypothesis are always visible, never implied.
3. **Show the test, not just the result.** Rejected hypotheses and the heterogeneity gate are part of the story, because judges are scoring judgement.
4. **One entry, one look.** The dashboard reads as part of the deck, not a separate product.
5. **Fast to grasp.** A judge skimming for a minute should get the answer from the first view.
