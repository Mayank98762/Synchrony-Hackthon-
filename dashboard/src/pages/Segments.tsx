import { useMemo, useState } from "react";
import { usePageData, num, type Segments as Data } from "../lib/data";
import { count, dec, pct, pp } from "../lib/format";
import { Kpi, PageState, Panel, TitleRow } from "../components/ui";
import { C, EChart, base, categoryAxis, valueAxis } from "../components/EChart";

const DIMENSIONS = [
  { id: "Membership", label: "Membership" }, { id: "Age", label: "Age" }, { id: "Credit limit", label: "Credit limit" },
  { id: "APR", label: "APR" }, { id: "Card vintage", label: "Card opened in" }, { id: "Category", label: "Category" },
  { id: "Closer", label: "Future closers" },
];
const BANDS = ["Zero", "Low", "Mid", "High"] as const;

export default function Segments() {
  const { data, error } = usePageData<Data>("segments");
  const [dim, setDim] = useState("Category");
  const rows = useMemo(() => data?.slices.filter((s) => s.dimension === dim) ?? [], [data, dim]);
  const dumbbell = useMemo(() => rows.length ? dumbbellOption(rows) : null, [rows]);
  const kmeans = useMemo(() => data && kmeansOption(data), [data]);
  if (!data || !dumbbell || !kmeans) return <PageState title="Segments" error={error} />;

  const g = data.gate;
  const changes = data.slices.map((s) => s.change_pp);
  const lo = Math.min(...changes.map(Math.abs)), hi = Math.max(...changes.map(Math.abs));
  const dimLabel = DIMENSIONS.find((d) => d.id === dim)!.label.toLowerCase();
  const dimChanges = rows.map((r) => r.change_pp);
  const km = data.kmeans;

  return (
    <>
      <TitleRow
        title="Segments"
        sub={<>Every customer group lost between {lo.toFixed(0)} and {hi.toFixed(0)} points of share. No slice explains the decline,
          and a customer&rsquo;s card use this year says nothing about next year.</>}
      />

      <div className="kpis">
        <Kpi label="Spread of card use vs pure chance" value={dec(num(g.x1_variance_ratio_fy26))}
          delta={<>variance ratio, FY26 (FY25 {dec(num(g.x1_variance_ratio_fy25))}); 1.00 is chance</>} />
        <Kpi label="Same customer, two halves of a year" value={`r = ${dec(num(g.x1_split_half_r), 3)}`}
          delta={<>95% CI {dec(num(g.x1_split_half_ci_lo), 3)} to {dec(num(g.x1_split_half_ci_hi), 3)}</>} />
        <Kpi label="HSIC share, FY25 → FY26" value={`r = ${dec(num(g.x1_persistence_r), 3)}`}
          delta={<>{count(num(g.x1_persistence_n))} customers; last year predicts nothing</>} />
        <Kpi label="Purchase frequency, FY25 → FY26" value={`r = ${dec(num(g.f13_r_purchases), 2)}`}
          delta={<>what does persist: how often they shop</>} />
      </div>

      <div className="grid">
        <Panel span="s8" title={`HSIC share, FY25 → FY26, by ${dimLabel}`} meta={
          <span className="legend"><span><i style={{ background: C.grey }} />FY25</span><span><i style={{ background: C.hue }} />FY26</span></span>}>
          <div className="tabs" role="tablist" aria-label="Customer dimension">
            {DIMENSIONS.map((d) => (
              <button key={d.id} role="tab" aria-selected={d.id === dim} onClick={() => setDim(d.id)}>{d.label}</button>
            ))}
          </div>
          <p className="lede" style={{ marginTop: 0 }}>Every {dimLabel} group falls by {Math.min(...dimChanges.map(Math.abs)).toFixed(1)} to {Math.max(...dimChanges.map(Math.abs)).toFixed(1)} points: the lines run in parallel.</p>
          <EChart option={dumbbell} height={330} label={`HSIC share by ${dimLabel}: every group falls by ${Math.min(...dimChanges.map(Math.abs)).toFixed(1)} to ${Math.max(...dimChanges.map(Math.abs)).toFixed(1)} points`} />
        </Panel>
        <Panel span="s4" title="Where FY25’s customers landed in FY26" meta="Share of each row">
          <p className="lede">Customers with 3+ purchases in each year, by FY25 SoW band.</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>FY25 band</th>{BANDS.map((b) => <th key={b} className="n">{b}</th>)}</tr></thead>
              <tbody>
                {data.band_movement.map((r) => {
                  const total = BANDS.reduce((s, b) => s + r[b], 0);
                  return (
                    <tr key={r.fy25_band}>
                      <td>{r.fy25_band}<span className="sub">{count(total)}</span></td>
                      {BANDS.map((b) => <td key={b} className="n">{pct(r[b] / total, 0)}</td>)}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="foot">The rows are near-identical: last year&rsquo;s band doesn&rsquo;t predict this year&rsquo;s.</p>
        </Panel>
      </div>

      <div className="grid">
        <Panel span="s8" title="Clustering customers on FY25 card use" meta={`${num(km.seg_kmeans_k)} K-means clusters · ${count(num(km.seg_kmeans_customers))} customers`}>
          <p className="lede">Stable clusters (ARI {dec(num(km.seg_kmeans_ari))}) that sit {num(km.seg_kmeans_fy25_sow_spread_pp)!.toFixed(0)} points apart in FY25
            land {num(km.seg_kmeans_fy26_sow_spread_pp)!.toFixed(1)} points apart a year later.</p>
          <EChart option={kmeans} height={240} label="Eight clusters from 1% to 79% SoW in FY25 all land between 20% and 22% in FY26" />
        </Panel>
        <Panel span="s4" title="What this means" meta="For targeting">
          <div className="rows">
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>No group to target on SoW</b>
              <div className="note">Every slice fell {lo.toFixed(0)}–{hi.toFixed(0)} points; the clusters explain {pct(num(km.seg_kmeans_eta2), 2)} of next year&rsquo;s SoW</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Light users are not a type</b>
              <div className="note">Last year&rsquo;s low-SoW customers were unlucky, not loyal elsewhere</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Value and risk do persist</b>
              <div className="note">Purchase frequency (r = {dec(num(g.f13_r_purchases), 2)}) and card age predict, so we prioritise on those</div></div></div>
          </div>
          <p className="foot"><a className="card-link" href="#/priorities">See the priority grid</a></p>
        </Panel>
      </div>
    </>
  );
}

function dumbbellOption(rows: Data["slices"]) {
  const levels = rows.map((r) => r.level).reverse();
  const byLevel = Object.fromEntries(rows.map((r) => [r.level, r]));
  return base({
    grid: { left: 8, right: 16, top: 6, bottom: 4, containLabel: true },
    tooltip: {
      ...(base().tooltip as object), trigger: "axis", axisPointer: { type: "none" },
      formatter: (ps: { name: string }[]) => {
        const r = byLevel[ps[0].name];
        return `<b style="font-weight:500">${r.level}</b><br/>FY25 ${pct(r.sow_fy25)} → FY26 ${pct(r.sow_fy26)} (${pp(r.change_pp)})`;
      },
    },
    xAxis: valueAxis({ min: 0, max: 0.4, interval: 0.1, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${v * 100}%` },
      splitLine: { lineStyle: { color: C.grid } } }),
    yAxis: categoryAxis(levels, { boundaryGap: true, axisLine: { show: false }, splitLine: { show: false } }),
    series: [
      {
        type: "custom", silent: true,
        renderItem: (_: unknown, api: { value: (i: number) => number; coord: (v: number[]) => number[] }) => {
          const a = api.coord([api.value(1), api.value(0)]), b = api.coord([api.value(2), api.value(0)]);
          return { type: "line", shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style: { stroke: C.pale, lineWidth: 2 } };
        },
        encode: { y: 0, x: [1, 2] },
        data: levels.map((l, i) => [i, byLevel[l].sow_fy25, byLevel[l].sow_fy26]),
      },
      { name: "FY25", type: "scatter", symbolSize: 11, itemStyle: { color: C.grey }, data: levels.map((l) => [byLevel[l].sow_fy25, l]) },
      {
        name: "FY26", type: "scatter", symbolSize: 11, itemStyle: { color: C.hue },
        label: { show: true, position: "left", distance: 8, color: C.label, fontSize: 12, formatter: (p: { data: [number, string] }) => pp(byLevel[p.data[1]].change_pp) },
        data: levels.map((l) => [byLevel[l].sow_fy26, l]),
      },
    ],
  });
}

function kmeansOption(d: Data) {
  const clusters = [...d.kmeans_clusters].sort((a, b) => b.sow_fy25 - a.sow_fy25);
  return base({
    grid: { left: 8, right: 56, top: 10, bottom: 4, containLabel: true },
    tooltip: { ...(base().tooltip as object), trigger: "item",
      formatter: (p: { seriesIndex: number }) => {
        const c = clusters[p.seriesIndex];
        return `Cluster of ${count(c.customers)} customers<br/>FY25 ${pct(c.sow_fy25)} → FY26 ${pct(c.sow_fy26)}`;
      } },
    xAxis: categoryAxis(["FY25, clusters built", "FY26, same customers"], { boundaryGap: ["22%", "22%"], axisLabel: { color: C.label, fontSize: 12, margin: 10, interval: 0 } }),
    yAxis: valueAxis({ min: 0, max: 0.8, interval: 0.2, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
    series: clusters.map((c) => ({
      type: "line", data: [c.sow_fy25, c.sow_fy26], symbol: "circle", symbolSize: 7,
      lineStyle: { color: C.ink, width: 1.5, opacity: 0.55 }, itemStyle: { color: C.ink },
      emphasis: { lineStyle: { width: 2.5, opacity: 1 } },
    })),
  });
}
