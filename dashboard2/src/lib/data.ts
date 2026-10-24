// Every figure comes from the pipeline (python analysis/run_all.py): the four page files it writes for the
// dashboard, key_numbers.json for the few keys those files leave out, and the experiment log. Bundled at
// build time, so the static site needs no fetch and cannot show a stale mix of files.
import overviewJson from "../../../dashboard/public/data/overview.json";
import segmentsJson from "../../../dashboard/public/data/segments.json";
import attritionJson from "../../../dashboard/public/data/attrition.json";
import priorityJson from "../../../dashboard/public/data/priority.json";
import keyNumbersJson from "../../../outputs/key_numbers.json";
import experimentCsv from "../../../outputs/experiment_log.csv?raw";

export type Label = "Measured" | "Simulated" | "Assumed" | "Pending" | "Hypothesis";
export interface Fig { value: number | string | null; label: Label }
export interface Meta { generated: string; data_window: string; customers: number; source: string }

export interface Overview {
  meta: Meta;
  sow_quarterly: { quarter: string; sow: number }[];
  per_card_monthly: { month: string; net_per_card: number; hsic_per_card: number; cards: number }[];
  kpis: Record<string, Fig>;
  mix: { method: string; fy25: number; fy26: number }[];
  bridge: { leaver: number; stayer: number; joiner: number; total: number };
  loss_share: { method: string; share: number }[];
}
export interface Segments {
  meta: Meta;
  slices: { dimension: string; level: string; sow_fy25: number; sow_fy26: number; change_pp: number }[];
  gate: Record<string, Fig>;
  band_movement: { fy25_band: string; Zero: number; Low: number; Mid: number; High: number }[];
  kmeans: Record<string, Fig>;
  kmeans_clusters: { cluster: number; customers: number; sow_fy25: number; sow_fy26: number }[];
}
export interface Attrition {
  meta: Meta;
  silent: { cutoff: string; customers: number; observed: number; expected_fixed: number; expected_time: number;
    excess_fixed: number; excess_time: number; excess_time_lo: number; excess_time_hi: number }[];
  decay: { months_before: number; raw: number; expected: number; excess: number; rows: number; chance_band: number }[];
  closures_quarterly: { quarter: string; closed: number; closed_any: number; open_at_start: number; rate: number }[];
  closure_by_age: { cutoff: string; bin: string; rate: number }[];
  closure_model: { model: string; roc_auc: number; pr_auc: number; top_decile_capture: number }[];
  figures: Record<string, Fig>;
}
export interface Box {
  segment: string; name: string; customers: number; sow: number; sow_lo: number; sow_hi: number;
  closure_6m: number; closure_lo: number; closure_hi: number; nonhsic_per_cust: number; prime_share: number;
}
export interface Priority {
  meta: Meta;
  boxes: Box[];
  sizes: { segment: string; customers: number; customers_at_score: number; name: string }[];
  young_split: { segment: string; age_bin: string; customers: number; closure_6m: number; nonhsic_per_cust: number }[];
  segment_a: Record<string, Fig>;
  axes: Record<string, Fig>;
  offers: { id: string; name: string; layer: string; who: string; what: string; tests: string | null }[];
  economics: Record<string, Fig>;
  scenarios: Record<string, Fig>;
}
export interface Experiment { id: string; expected: string; verdict: string; result: string }

export const overview = overviewJson as unknown as Overview;
export const segments = segmentsJson as unknown as Segments;
export const attrition = attritionJson as unknown as Attrition;
export const priority = priorityJson as unknown as Priority;
const keyNumbers = keyNumbersJson as unknown as Record<string, Fig>;
export const meta = overview.meta;

/** A key from key_numbers.json; throws at load if the pipeline stopped writing it, so a gap is never silent. */
export function key(name: string): number {
  const f = keyNumbers[name];
  if (!f || typeof f.value !== "number") throw new Error(`key_numbers.json has no numeric "${name}"`);
  return f.value;
}
export const num = (f: Fig | undefined): number | null => (f && typeof f.value === "number" ? f.value : null);

/** experiment_log.csv: id,expected,verdict,result with RFC 4180 quoting */
function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], cell = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); rows.push(row); row = []; cell = "";
    } else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows.filter((r) => r.some(Boolean));
}

export const experiments: Experiment[] = parseCsv(experimentCsv).slice(1)
  .map(([id, expected, verdict, result = ""]) => ({ id, expected, verdict, result }));
