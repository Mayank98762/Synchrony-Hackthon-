# Synchrony Analytics Hackathon 2026: Winning Strategy & Execution Blueprint

---

## 1. Executive Summary & Problem Statement Breakdown

### Business Context
**MetroMart Inc.** (a retail giant operating on an August–July fiscal year) and **HSIC Bank** have partnered to offer a co-branded credit card. The card features:
* **Zero Joining/Annual Fees**
* **Prime Members:** $5\%$ cashback on Groceries, $3\%$ cashback on Electronics, $1\%$ cashback on all other eligible purchases at MetroMart.
* **Non-Prime Members:** $1\%$ cashback on all eligible purchases at MetroMart.
* **Market Position:** Unmatched, industry-leading cashback rates for MetroMart Grocery and Electronics purchases.
* **Reward Credit Logic:** Cashback earned in month $t$ is applied as a statement credit/adjustment in month $t+1$.

### The Core Problem: Silent Attrition
Despite offering the highest reward rates on the market, HSIC leadership observes that cardholders are reducing their spend on MetroMart using the co-branded card. Customers are shifting spend to alternative payment methods (competitor cards, cash, UPI, digital wallets).

Unlike **hard churn** (canceling the card), **silent attrition** occurs when a customer keeps the card account open but quietly stops using it for MetroMart purchases.

### Mathematical & Business Definitions
1. **Share of Wallet (SoW):**
   $$\text{SoW}_i = \frac{\text{Net Spend on HSIC Card at MetroMart by Customer } i}{\text{Total Net Spend at MetroMart by Customer } i}$$
2. **Net Sales Formulation:**
   $$\text{Net Spend} = \text{Gross Purchases} - \text{Returns}$$
   *Note: For returned items, set transaction count = $0$.*
3. **Card Tenure Filtering:**
   Calculate SoW **only** during active/open card periods. Do not penalize SoW for months prior to card activation or after account closure.
4. **Fiscal Calendar:**
   Align temporal aggregations to MetroMart's fiscal year: **August 1 to July 31**.

---

## 2. Exploratory Data Analysis (EDA) & Feature Engineering

### Key Hypotheses to Test
* **H1 (Cashback Delay Friction):** The 1-month delay in receiving statement credits reduces instant gratification, driving users toward instant-discount competitor cards.
* **H2 (Non-Prime Disincentive):** Non-Prime members ($1\%$ flat cashback) see insufficient value compared to generic flat-rate cards, leading to rapid drop-off.
* **H3 (Credit Limit Bottleneck):** High-spend customers hit their credit limit during peak sale events (e.g., Diwali, Electronics Sales), forcing them to use secondary cards.
* **H4 (Category Leakage):** Customers use the HSIC card for Groceries ($5\%$) but switch to alternative cards for General Purchases ($1\%$) or non-promotional categories.

### Feature Engineering Roadmap

| Feature Category | Feature Name | Description / Formula |
| :--- | :--- | :--- |
| **SoW Trajectory** | `SoW_30d`, `SoW_90d`, `SoW_180d` | Rolling Share of Wallet over 30, 90, and 180 days. |
| **Delta Metrics** | $\Delta \text{SoW}$ | $\text{SoW}_{\text{Current Quarter}} - \text{SoW}_{\text{Previous Quarter}}$ |
| **Category Leakage** | `Grocery_SoW_Share` | $\frac{\text{HSIC Grocery Spend}}{\text{Total Grocery Spend}}$ |
| **Category Leakage** | `Electronics_SoW_Share` | $\frac{\text{HSIC Electronics Spend}}{\text{Total Electronics Spend}}$ |
| **Return Ratio** | `Return_Rate` | $\frac{\text{Total Return Amount}}{\text{Gross Spend}}$ |
| **Payment Diversification** | `Alt_Payment_Count` | Number of distinct non-HSIC payment methods used at MetroMart. |
| **Tenure & Recency** | `Card_Tenure_Months` | Active months since card issuance. |

---

## 3. Machine Learning Architecture

```
[Raw Transaction Data] ──► [Preprocessing & Net Sales Filter] ──► [Feature Store (RFM + SoW)]
                                                                          │
         ┌────────────────────────────────────────────────────────────────┴────────────────┐
         ▼                                                 ▼                               ▼
[Model 1: XGBoost Risk Score]            [Model 2: K-Means Segmentation]         [Model 3: Uplift Model]
 Predicts P(SoW Drop > 20%)              Clusters by Behavior & Spending         Predicts Incremental Lift
```

### Model 1: Silent Attrition Predictive Model
* **Target Variable ($Y$):** Binary classification ($1$ if customer's SoW drops by $>20\%$ in the next 60 days, $0$ otherwise).
* **Algorithm:** XGBoost / LightGBM Classifier.
* **Outputs:** Attrition Risk Score ($0.0$ to $1.0$) for every cardholder.

### Model 2: Unsupervised Customer Micro-Segmentation
* **Algorithm:** K-Means / Gaussian Mixture Models with silhouette optimization.
* **Target Segments:**
  1. *Unclaimed Loyalty Champions:* High total spend, High HSIC SoW, Prime status.
  2. *At-Risk Grocery Shoppers:* High total grocery spend, sharply declining HSIC SoW.
  3. *Lapsed Electronics Buyers:* High historical electronics spend, switched to competitor cards.
  4. *Disengaged Non-Prime Users:* Low overall engagement, $1\%$ cashback tier.

### Model 3: Uplift Modeling (Offer Sensitivity)
* **Goal:** Determine which customers will increase SoW **only if given an offer**, avoiding marketing spend on "Sure Things" or "Lost Causes".
* **Formula:**
  $$\text{Uplift} = P(\text{SoW Increase} \mid \text{Offer}) - P(\text{SoW Increase} \mid \text{No Offer})$$

---

## 4. Multi-Technology Stack Integration

### Stack Architecture
* **Data Processing & Analytics:** Python (`pandas`, `numpy`, `scikit-learn`, `xgboost`).
* **Backend API:** FastAPI / Python.
* **Frontend Web Dashboard:** Streamlit or React + Tailwind CSS.
* **Generative AI & RAG:** LangChain / LlamaIndex + OpenAI / Gemini API + ChromaDB vector database.

### Core Tech Features

#### A. Interactive Executive Dashboard (Web App)
* **Overview Tab:** Real-time macro metrics (Overall SoW, total lost spend due to silent attrition, fiscal year breakdown).
* **Customer Drill-Down:** Searchable database filtered by Attrition Risk Score, category drop-offs, and Prime status.
* **What-If ROI Simulator:** Slide-based controls allowing business managers to test campaign parameters in real time.

#### B. GenAI & RAG Engine
1. **Hyper-Personalized Notification Generator:**
   * Automatically crafts targeted email/push copy based on customer segment and risk drivers.
   * *Example:* *"Hi Sarah, unlock an extra 2% instant cashback on your next MetroMart Grocery purchase with your HSIC card!"*
2. **Internal Analytics Knowledge Assistant (RAG):**
   * Index data dictionary, case study rules, and EDA insights into ChromaDB.
   * Query interface: Allows executives to ask natural language questions like *"Which category has the highest spend leakage among Non-Prime users?"*

---

## 5. Campaign Strategy & Financial ROI Simulator

### Targeted Intervention Matrix

| Customer Segment | Risk Level | Primary Root Cause | Proposed Intervention | Incentive Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **At-Risk Grocery Shoppers** | High | Delayed cashback perception | Instant point credit notification + 30-day $1\%$ bonus boost | $+1\%$ temporary cashback boost on Groceries |
| **Lapsed Electronics Buyers** | Medium | Credit limit constraints | Temporary credit limit upgrade during sale events | Flexible EMI / Limit Extension |
| **Disengaged Non-Prime** | High | Low base reward ($1\%$) | 3-month complimentary Prime trial conditional on $3$ card swipes | Prime Trial Upsell |

### Financial ROI Formula
To ensure the proposed interventions make business sense, evaluate them using Net ROI:

$$\text{Net Incremental Revenue} = (\text{Recovered Spend} \times \text{Interchange Fee \%}) + \text{Merchant Margin}$$

$$\text{Net Campaign Cost} = \text{Bonus Cashback Paid} + \text{Communication/Marketing Cost}$$

$$\text{Campaign ROI} = \frac{\text{Net Incremental Revenue} - \text{Net Campaign Cost}}{\text{Net Campaign Cost}} \times 100\%$$

---

## 6. Hackathon Winning USPs & Differentiation Factors

1. **Closed-Loop Campaign Simulator:** A fully functioning interactive web widget allowing judges to input marketing budget and simulate predicted SoW recovery and ROI.
2. **Behavioral Root-Cause Attribution Engine:** Going beyond identifying *who* is leaving to quantitatively explaining *why* they are leaving (e.g., credit limit issues vs. category drift).
3. **GenAI Automation Pipeline:** Demonstrating how ML predictions feed directly into AI-generated marketing copy for end-to-end execution.
4. **Strict Compliance with Business Constraints:** Flawlessly adhering to Net Sales calculations, card tenure filtering, and MetroMart's August–July fiscal year calendar.

---

## 7. Submission Checklist & Slide Deck Structure

### Submission Constraints
* **Format:** Single PDF presentation slide deck.
* **Recipient Email:** `analyticshiring@syf.com`
* **Deadline:** **8:00 PM IST on October 24, 2026**
* **Subject Line:** *Student Roll Number ONLY* (e.g., `2023XX12345`). No additional text.
* **Storage Constraint:** Do **NOT** use Google Drive links or external cloud hosting; attach the PDF directly.

### Recommended 10-Slide Deck Outline

```
Slide 1: Title Slide & Team Identification
Slide 2: Executive Summary & Problem Understanding
Slide 3: Data Pipeline, Cleaning Rules & Fiscal Calendar Alignment
Slide 4: Key Insights & Silent Attrition Root-Cause Analysis
Slide 5: Predictive Modeling (Silent Attrition Risk Architecture)
Slide 6: Customer Micro-Segmentation & Behavioral Personas
Slide 7: Personalized Campaign Strategies & Reward Matrix
Slide 8: Full-Stack App & GenAI / RAG Architecture
Slide 9: Financial ROI & Campaign Simulator Results
Slide 10: Conclusion & Business Roadmap
```