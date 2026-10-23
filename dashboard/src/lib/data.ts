import { useEffect, useState } from "react";

// One JSON file per page, written by analysis/dashboard_data.py (run_all.py). Aggregates only.
export type Label = "Measured" | "Simulated" | "Assumed" | "Pending";
export interface Fig { key: string; value: number | string | null; label: Label }
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
  economics: Record<string, { value: number | string; label: Label }>;
  scenarios: Record<string, Fig>;
}

type State<T> = { data: T | null; error: string | null };

export function usePageData<T>(page: string): State<T> {
  const [state, setState] = useState<State<T>>({ data: null, error: null });
  useEffect(() => {
    let live = true;
    fetch(`./data/${page}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status} ${r.statusText}`))))
      .then((data: T) => live && setState({ data, error: null }))
      .catch((e: Error) => live && setState({ data: null, error: e.message }));
    return () => { live = false; };
  }, [page]);
  return state;
}

export const num = (f: Fig | undefined): number | null => (f && typeof f.value === "number" ? f.value : null);
