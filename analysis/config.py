"""Every constant the pipeline uses: paths, dates, codes, rule-9 definitions, thresholds, assumptions.

Nothing in here is computed from the data. Change a value here, never inline in a module.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUTS = ROOT / "outputs"
CHARTS = OUTPUTS / "charts"
MODEL_EVAL = OUTPUTS / "model_eval"
DASHBOARD_DATA = ROOT / "dashboard" / "public" / "data"

FILES = {
    "customers": DATA_DIR / "Customer Data.csv",
    "transactions": DATA_DIR / "Transactions Data.csv",
    "categories": DATA_DIR / "Category Code.csv",
    "payments": DATA_DIR / "Payment Code.csv",
}

SEED = 42

# ---------------------------------------------------------------- data window and expected shape (plan §2)
DATA_START = pd.Timestamp("2024-08-01")
DATA_END = pd.Timestamp("2026-07-31")
FISCAL_YEARS = (2025, 2026)          # FY25 = Aug 2024-Jul 2025, FY26 = Aug 2025-Jul 2026
FY_START_MONTH = 8

EXPECTED_ROWS = {"customers": 45_000, "transactions": 444_118, "categories": 10, "payments": 5}

# ---------------------------------------------------------------- codes
HSIC_CODE = 3
PAYMENT_SHORT = {1: "Debit", 2: "Other CC", 3: "HSIC", 4: "Cash/UPI", 5: "Wallet"}
GROCERY, ELECTRONICS = 1, 2

# Rewards at MetroMart (brief). Rewards earned in month m are credited in month m + 1.
PRIME_RATES = {GROCERY: 0.05, ELECTRONICS: 0.03}
PRIME_OTHER_RATE = 0.01
NON_PRIME_RATE = 0.01

# ---------------------------------------------------------------- snapshots (plan §3 rule 4)
CUTOFF_TRAIN = pd.Timestamp("2025-07-31")     # labels Aug 2025-Jan 2026
CUTOFF_TEST = pd.Timestamp("2026-01-31")      # labels Feb-Jul 2026; also where the 2x2 boxes are built
CUTOFF_SCORE = pd.Timestamp("2026-07-31")     # deployment scoring, no labels
LOOKBACK_MONTHS = 12
HORIZON_MONTHS = 6
SILENT_ATTRITION_CUTOFFS = (pd.Timestamp("2025-01-31"), pd.Timestamp("2025-07-31"), pd.Timestamp("2026-01-31"))

# ---------------------------------------------------------------- rule-9 shared definitions
DAYS_PER_YEAR = 365.25
CARD_AGE_BINS = [-np.inf, 0.5, 1, 2, 3, np.inf]                 # years, right-closed below each edge
CARD_AGE_LABELS = ["<6m", "6-12m", "1-2y", "2-3y", "3y+"]
YOUNG_CARD_YEARS = 1.0                                          # 2x2 column split: young = card age < 1 year

FREQ_TOP_QUANTILE = 2 / 3                                       # top tercile of purchase frequency
FREQ_INDEPENDENCE_TOL = 0.03                                    # young vs mature top-tercile share, max gap

MIN_PURCHASES_PER_PERIOD = 3                                    # customer-level SoW filter

TICKET_CAP = 9999.99
TICKET_BANDS = [0, 1000, 3000, TICKET_CAP - 0.005, np.inf]
TICKET_LABELS = ["<1k", "1k-3k", "3k-10k", "capped"]

# ---------------------------------------------------------------- heterogeneity gate (plan §3 rule 3)
GATE = {
    "variance_ratio_min": 1.10,      # observed / binomial variance of per-customer HSIC share
    "split_half_min": 0.10,          # odd vs even purchases in the same FY
    "persistence_min": 0.20,         # FY25 -> FY26 correlation
    "min_rows": 4,                   # customers need this many active rows in the period to enter the gate
}

# ---------------------------------------------------------------- modelling
BOOTSTRAP_N = 1000
KMEANS_K_RANGE = range(3, 9)
KMEANS_N_INIT = 20
KMEANS_STABILITY_RESAMPLES = 20
BOUNDARY_SHIFT = 0.10                # +/-10% move of the tercile and 12-month cuts

# ---------------------------------------------------------------- pilot design (plan §8)
HOLDOUT_SHARE = 0.10
ALPHA = 0.05
POWER = 0.80

# ---------------------------------------------------------------- business assumptions (plan §8, all labelled Assumed)
SCENARIOS = {
    "conservative": {"interchange": 0.015, "revolve_income": 0.00, "cofunding": 0.0},
    "base": {"interchange": 0.0175, "revolve_income": 0.01, "cofunding": 0.5},
    "optimistic": {"interchange": 0.020, "revolve_income": 0.02, "cofunding": 0.5},
}
