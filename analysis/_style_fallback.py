"""Stand-in for Shreyash's analysis/style.py until it lands.

Exposes the same names (HANDOFF_SHREYASH.md §1), so chart code imports
`style` and falls back here; once style.py exists, it wins with no code change.
Colours are the validated reference palette (light mode; the deck is a PDF).
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
    "hsic": "#2a78d6",     # hero: the HSIC card
    "accent": "#eb6834",
}

# Fixed order, validated adjacent-pair CVD-safe. Aqua, yellow and magenta sit
# below 3:1 on the light surface, so charts using them need direct labels.
METHOD_COLORS = {
    "HSIC": "#2a78d6",
    "Cash/UPI": "#eb6834",
    "Wallet": "#1baf7a",
    "Debit": "#eda100",
    "Other CC": "#e87ba4",
}

BADGE_COLORS = {
    "Measured": "#2a78d6",
    "Simulated": "#6250d6",
    "Assumed": "#52514e",
    "Hypothesis": "#eb6834",
}

FIGSIZE = (10, 5.625)   # 16:9
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
