"""Chart style guide for every slide chart (HANDOFF_SHREYASH §1). Owner: Shreyash.

The palette is the validated dataviz reference instance, light mode (the deck is a PDF). Payment methods keep one
fixed colour order, so a method is the same colour on every slide. Text stays in ink colours; colour carries identity
only on the marks. `critical` is reserved for "never breaks even" and is always paired with the word "never".

    from analysis import style
    style.apply()
    fig, ax = plt.subplots()
    ...
    style.save(fig, 11, "breakeven")     # -> outputs/charts/11_breakeven.png, 16:9 at 200 dpi
"""
import matplotlib as mpl

from analysis import config as C

COLORS = {
    "ink": "#0b0b0b",
    "secondary": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    "bg": "#fcfcfb",
    "hsic": "#2a78d6",        # hero: the HSIC card
    "accent": "#eb6834",
    "negative": "#e34948",    # a cost or loss step (categorical red, never used for a payment method)
    "critical": "#d03b3b",    # status: "never breaks even"
}

# Reference categorical slots 1-5 in order (adjacent pairs pass the CVD and normal-vision gates).
# Wallet, Debit and Other CC sit below 3:1 on the light surface, so charts using them need direct labels.
METHOD_COLORS = {
    "HSIC": "#2a78d6",
    "Cash/UPI": "#eb6834",
    "Wallet": "#1baf7a",
    "Debit": "#eda100",
    "Other CC": "#e87ba4",
}

# Slide badges: never a payment-method colour, and always shown with their word.
BADGE_COLORS = {
    "Measured": "#0b0b0b",
    "Simulated": "#6250d6",
    "Assumed": "#898781",
    "Hypothesis": "#e34948",
}

# Ordinal ramp (blue, light -> dark) for the three economics scenarios.
SCENARIO_COLORS = {"conservative": "#86b6ef", "base": "#2a78d6", "optimistic": "#104281"}

FIGSIZE = (10, 5.625)      # 16:9
DPI = 200


def apply():
    mpl.rcParams.update({
        "font.family": ["Segoe UI", "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelsize": 11,
        "axes.labelcolor": COLORS["secondary"],
        "axes.edgecolor": COLORS["axis"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": COLORS["grid"],
        "grid.linewidth": 0.6,
        "xtick.color": COLORS["muted"],
        "ytick.color": COLORS["muted"],
        "xtick.labelcolor": COLORS["secondary"],
        "ytick.labelcolor": COLORS["secondary"],
        "ytick.left": False,
        "text.color": COLORS["ink"],
        "figure.facecolor": COLORS["bg"],
        "axes.facecolor": COLORS["bg"],
        "savefig.facecolor": COLORS["bg"],
        "figure.figsize": FIGSIZE,
        "figure.dpi": 100,
        "lines.linewidth": 2,
        "legend.frameon": False,
    })


def save(fig, slide, name):
    C.CHARTS.mkdir(parents=True, exist_ok=True)
    path = C.CHARTS / f"{slide:02d}_{name}.png"
    fig.savefig(path, dpi=DPI)    # no tight bbox: keeps the exact 16:9 size
    return path
