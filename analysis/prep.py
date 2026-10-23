"""Load, validate and enrich the case data (plan §2), plus the shared helpers every module uses.

    from analysis import prep
    d = prep.load()                 # cached; d.cust, d.txn
    act = prep.active(d.txn)        # rows inside an open card window
    prep.sow(act[act.fy == 2026])   # 0.195

Smoke test: `python -m analysis.prep`
"""
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from analysis import config as C

CUST_COLUMNS = {
    "Customer_ID": "customer_id",
    "Age": "age",
    "Gender": "gender",
    "Membership_Type": "membership",
    "Credit_Card_Open_Date": "open_date",
    "Credit_Card_Closed_Date": "close_date",
    "Credit_Card_Limit": "credit_limit",
    "Credit_Card_APR": "apr",
}
TXN_COLUMNS = {
    "Customer_ID": "customer_id",
    "Transaction_ID": "txn_id",
    "Transaction_Date": "date",
    "Category_Code": "category_code",
    "Transaction_Type": "txn_type",
    "Transaction_Amount": "amount",
    "Payment_Code": "payment_code",
    "Number_of_Transactions": "n_txn",
}


@dataclass(frozen=True)
class Data:
    cust: pd.DataFrame      # one row per customer
    txn: pd.DataFrame       # one row per transaction, customer fields joined
    categories: pd.DataFrame
    payments: pd.DataFrame


# ---------------------------------------------------------------- loading
def load_raw():
    """The four CSVs exactly as delivered (original column names)."""
    return {
        "customers": pd.read_csv(C.FILES["customers"], parse_dates=["Credit_Card_Open_Date", "Credit_Card_Closed_Date"]),
        "transactions": pd.read_csv(C.FILES["transactions"], parse_dates=["Transaction_Date"]),
        "categories": pd.read_csv(C.FILES["categories"]),
        "payments": pd.read_csv(C.FILES["payments"]),
    }


def validate_raw(raw):
    cust, txn, cat, pay = raw["customers"], raw["transactions"], raw["categories"], raw["payments"]
    for name, n in C.EXPECTED_ROWS.items():
        assert len(raw[name]) == n, f"{name}: expected {n} rows, got {len(raw[name])}"
    assert cust.Customer_ID.is_unique, "duplicate Customer_ID"
    assert txn.Transaction_ID.is_unique, "duplicate Transaction_ID"
    assert txn.Customer_ID.isin(cust.Customer_ID).all(), "orphan transactions"
    assert txn.Category_Code.isin(cat.Category_Code).all(), "unknown Category_Code"
    assert txn.Payment_Code.isin(pay.Payment_Code).all(), "unknown Payment_Code"
    assert pay.set_index("Payment_Code").Payment_Method[C.HSIC_CODE] == "HSIC Bank Credit Card"
    assert set(txn.Transaction_Type) == {"Sale", "Return"}
    assert txn.loc[txn.Transaction_Type == "Return", "Number_of_Transactions"].isna().all(), "Return with a count"
    assert txn.loc[txn.Transaction_Type == "Sale", "Number_of_Transactions"].notna().all(), "Sale without a count"
    assert (txn.Transaction_Amount > 0).all(), "non-positive amount"
    assert txn.Transaction_Date.between(C.DATA_START, C.DATA_END).all(), "transaction outside the data window"
    assert not (cust.Credit_Card_Closed_Date < cust.Credit_Card_Open_Date).any(), "card closed before it opened"
    assert (cust.Credit_Card_Open_Date.isna() == cust.Credit_Card_Limit.isna()).all()
    assert (cust.Credit_Card_Open_Date.isna() == cust.Credit_Card_APR.isna()).all()
    assert cust.Credit_Card_Closed_Date[cust.Credit_Card_Open_Date.isna()].isna().all(), "close date without a card"


def _enrich_customers(raw):
    cust = raw["customers"].rename(columns=CUST_COLUMNS)
    cust["is_prime"] = cust.membership.eq("Prime")
    cust["has_card"] = cust.open_date.notna()
    cust["is_closed"] = cust.close_date.notna()
    return cust


def _enrich_transactions(raw, cust):
    txn = raw["transactions"].rename(columns=TXN_COLUMNS)
    cat = raw["categories"].set_index("Category_Code").Category
    pay = raw["payments"].set_index("Payment_Code").Payment_Method

    txn["category"] = txn.category_code.map(cat)
    txn["payment_method"] = txn.payment_code.map(pay)
    txn["payment_short"] = txn.payment_code.map(C.PAYMENT_SHORT)
    txn["is_sale"] = txn.txn_type.eq("Sale")
    txn["is_return"] = ~txn.is_sale
    txn["is_hsic"] = txn.payment_code.eq(C.HSIC_CODE)
    # Brief: net sales, and returns count as zero transactions.
    txn["net"] = np.where(txn.is_sale, txn.amount, -txn.amount)
    txn["n_txn"] = txn.n_txn.fillna(0).astype(int)

    # Fiscal calendar: FY runs Aug-Jul and is named by the year it ends in.
    month = txn.date.dt.month
    txn["fy"] = txn.date.dt.year + (month >= C.FY_START_MONTH)
    txn["fq"] = ((month - C.FY_START_MONTH) % 12) // 3 + 1
    txn["fq_label"] = "FY" + (txn.fy % 100).astype(str) + " Q" + txn.fq.astype(str)
    txn["half"] = np.where(txn.fq <= 2, "H1", "H2")
    txn["month"] = txn.date.dt.to_period("M")

    txn["ticket_band"] = pd.cut(txn.amount, C.TICKET_BANDS, labels=C.TICKET_LABELS)
    txn["is_capped"] = txn.amount.eq(C.TICKET_CAP)

    txn = txn.merge(cust[["customer_id", "is_prime", "has_card", "open_date", "close_date"]], on="customer_id", how="left")
    # Card active on both its open and close dates; a null close date means still open.
    txn["is_active"] = txn.has_card & (txn.date >= txn.open_date) & (
        txn.close_date.isna() | (txn.date <= txn.close_date))

    prime_rate = txn.category_code.map(C.PRIME_RATES).fillna(C.PRIME_OTHER_RATE)
    txn["reward_rate"] = np.where(txn.is_prime, prime_rate, C.NON_PRIME_RATE)
    # Derived rewards: earned on active HSIC net spend (returns claw back), credited the following month.
    txn["reward"] = np.where(txn.is_hsic & txn.is_active, txn.net * txn.reward_rate, 0.0)
    txn["reward_credit_month"] = txn.month + 1
    return txn


def validate_enriched(cust, txn):
    assert len(txn) == C.EXPECTED_ROWS["transactions"], "rows lost in the merge"
    assert not (txn.is_hsic & ~txn.is_active).any(), "HSIC transaction outside an active card window"
    assert set(txn.fy) == set(C.FISCAL_YEARS)
    gross, returns = txn.loc[txn.is_sale, "amount"].sum(), txn.loc[txn.is_return, "amount"].sum()
    assert np.isclose(gross - returns, txn.net.sum()), "gross - returns != net"
    assert txn.loc[txn.is_return, "n_txn"].eq(0).all()
    assert txn.ticket_band.notna().all()


@lru_cache(maxsize=1)
def load():
    """Validated, enriched data. Cached, so every module shares one copy; don't mutate the frames."""
    raw = load_raw()
    validate_raw(raw)
    cust = _enrich_customers(raw)
    txn = _enrich_transactions(raw, cust)
    validate_enriched(cust, txn)
    return Data(cust=cust, txn=txn, categories=raw["categories"], payments=raw["payments"])


# ---------------------------------------------------------------- shared helpers
def active(txn):
    """Rows inside an open card window: the only rows SoW may use."""
    return txn[txn.is_active]


def purchases(txn):
    """Rule 9: a purchase is an active-window Sale row."""
    return txn[txn.is_active & txn.is_sale]


def sow(txn):
    """Share of Wallet as a ratio of sums over net spend. Pass active rows only."""
    total = txn.net.sum()
    return txn.loc[txn.is_hsic, "net"].sum() / total if total > 0 else np.nan


def months_after(date, months):
    """Calendar-month offset (rule 9): 2025-07-31 + 6 -> 2026-01-31."""
    return pd.Timestamp(date) + pd.DateOffset(months=months)


def in_window(dates, start, end):
    """Rule 9 windows are (start, end]: exclusive start, inclusive end."""
    return (dates > start) & (dates <= end)


def horizon(cutoff):
    return cutoff, months_after(cutoff, C.HORIZON_MONTHS)


def lookback(cutoff):
    return months_after(cutoff, -C.LOOKBACK_MONTHS), cutoff


def open_at(cust, cutoff):
    """Rule 9 closure-model universe: card opened on or before the cutoff and not closed on or before it."""
    return cust.has_card & (cust.open_date <= cutoff) & (cust.close_date.isna() | (cust.close_date > cutoff))


def closed_in(cust, start, end):
    return in_window(cust.close_date, start, end).fillna(False)


def card_age_years(cust, cutoff):
    return (cutoff - cust.open_date).dt.days / C.DAYS_PER_YEAR


def card_age_bin(cust, cutoff):
    return pd.cut(card_age_years(cust, cutoff), C.CARD_AGE_BINS, labels=C.CARD_AGE_LABELS)


def is_young(cust, cutoff):
    return card_age_years(cust, cutoff) < C.YOUNG_CARD_YEARS


def purchase_frequency(txn, cutoff):
    """Rule 9: all MetroMart Sale rows (any method, card open or not) in the 12 months up to the cutoff.

    Returns a Series indexed by customer_id; customers with no purchases are absent (treat as 0).
    """
    start, end = lookback(cutoff)
    rows = txn[txn.is_sale & in_window(txn.date, start, end)]
    return rows.groupby("customer_id").size()


def snapshot_universe(cutoff):
    """Cards open at the cutoff, with card age, age bin, young flag and 6-month closure label."""
    d = load()
    u = d.cust[open_at(d.cust, cutoff)].copy()
    u["card_age_years"] = card_age_years(u, cutoff)
    u["card_age_bin"] = card_age_bin(u, cutoff)
    u["is_young"] = u.card_age_years < C.YOUNG_CARD_YEARS
    h0, h1 = horizon(cutoff)
    u["closed_6m"] = closed_in(u, h0, h1) if cutoff < C.DATA_END else np.nan
    return u


if __name__ == "__main__":
    d = load()
    act = active(d.txn)
    print(f"customers {len(d.cust):,} | cardholders {d.cust.has_card.sum():,} | closed {d.cust.is_closed.sum():,}")
    print(f"transactions {len(d.txn):,} | returns {d.txn.is_return.sum():,} | active rows {len(act):,}")
    for fy in C.FISCAL_YEARS:
        print(f"SoW FY{fy % 100}: {sow(act[act.fy == fy]):.4f}")
    for cut in (C.CUTOFF_TRAIN, C.CUTOFF_TEST):
        u = snapshot_universe(cut)
        print(f"{cut.date()}: open cards {len(u):,}, closers in 6m {int(u.closed_6m.sum()):,}")
