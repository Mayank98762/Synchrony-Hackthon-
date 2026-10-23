// Figures: fixed decimals per metric, a real minus sign, thousands separators, a sign on every change.
const MINUS = "−";

const sign = (s: string, v: number) => (v > 0 ? `+${s}` : v < 0 ? `${MINUS}${s}` : s);
const abs = Math.abs;

export const pct = (v: number | null, d = 1) => (v == null ? "—" : `${(v * 100).toFixed(d).replace("-", MINUS)}%`);
/** a change in percentage points, from values already in points */
export const pp = (v: number, d = 1) => sign(`${abs(v).toFixed(d)}pp`, Number(v.toFixed(d)));
export const inr = (v: number | null, d = 0) =>
  v == null ? "—" : `${v < 0 ? MINUS : ""}₹${abs(v).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d })}`;
export const inrM = (v: number | null, d = 1) => (v == null ? "—" : `₹${(v / 1e6).toFixed(d)}M`);
export const count = (v: number | null) => (v == null ? "—" : Math.round(v).toLocaleString("en-IN"));
export const signedInr = (v: number) => sign(`₹${abs(v).toLocaleString("en-IN")}`, v);
export const dec = (v: number | null, d = 2) => (v == null ? "—" : v.toFixed(d).replace("-", MINUS));

/** "FY25 Q1" -> "Q1 FY25" reads better on a time axis */
export const quarterLabel = (q: string) => q.replace(/^(FY\d\d) (Q\d)$/, "$2 $1");
/** "2026-05" -> "May 26" */
export const monthLabel = (m: string) => {
  const [y, mo] = m.split("-").map(Number);
  return `${new Date(y, mo - 1, 1).toLocaleString("en-GB", { month: "short" })} ${String(y).slice(2)}`;
};
/** "2026Q2" -> "Apr–Jun 26" */
export const calQuarter = (q: string) => {
  const [y, n] = q.split("Q").map(Number);
  const names = ["Jan–Mar", "Apr–Jun", "Jul–Sep", "Oct–Dec"];
  return `${names[n - 1]} ${String(y).slice(2)}`;
};
export const dateLabel = (iso: string) =>
  new Date(`${iso}T00:00:00`).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
