import { useMemo, useState } from "react";
import { Badge, Card, Swatch } from "../components/ui";
import { base, C, categoryAxis, EChart, hatch, tipRow, valueAxis } from "../components/EChart";
import { num, segments } from "../lib/data";
import { dec, pct, pp } from "../lib/format";

const g = segments.gate;
const DIMS = [...new Set(segments.slices.map((s) => s.dimension))];

function Gate() {
  const ci = (lo: string, hi: string) => `95% CI ${dec(num(g[lo]), 3)} to ${dec(num(g[hi]), 3)}`;
  const tiles = [
    { label: "Variance ratio, FY25", value: dec(num(g.x1_variance_ratio_fy25)), note: `FY26 ${dec(num(g.x1_variance_ratio_fy26))}. 1.00 is what pure chance gives.` },
    { label: "Split-half correlation", value: dec(num(g.x1_split_half_r), 3), note: `${ci("x1_split_half_ci_lo", "x1_split_half_ci_hi")}, n = ${num(g.x1_split_half_n)?.toLocaleString("en-IN")}` },
    { label: "Year-over-year correlation", value: dec(num(g.x1_persistence_r), 3), note: `${ci("x1_persistence_ci_lo", "x1_persistence_ci_hi")}, n = ${num(g.x1_persistence_n)?.toLocaleString("en-IN")}` },
  ];
  return (
    <section className="card gate" aria-label="Heterogeneity gate">
      <div className="gate-copy">
        <h2>The heterogeneity gate</h2>
        <p>Before clustering customers on share of wallet, we asked whether their share differs by more than chance.
          All three tests say no: a customer's HSIC share in one half-year tells you nothing about the next.</p>
        <p className="gate-verdict"><span className="verdict-dot" aria-hidden="true" />Verdict: do not segment on SoW <Badge label="Measured" /></p>
      </div>
      {tiles.map((t) => (
        <div className="stat" key={t.label}>
          <span className="stat-label">{t.label}</span>
          <b className="stat-value">{t.value}</b>
          <span className="stat-note">{t.note}</span>
        </div>
      ))}
    </section>
  );
}

function Slices() {
  const [dim, setDim] = useState("Category");
  const rows = segments.slices.filter((s) => s.dimension === dim);
  const option = useMemo(() => base({
    grid: { left: 4, right: 56, top: 8, bottom: 4, containLabel: true },
    tooltip: { ...(base().tooltip as object), formatter: (p: { name: string; dataIndex: number }[]) => {
      const r = rows[p[0].dataIndex];
      return `<div style="color:${C.label};margin-bottom:4px">${r.level}</div>${tipRow(C.ghostHi, "FY25", pct(r.sow_fy25))}${tipRow(C.lime, "FY26", pct(r.sow_fy26))}${tipRow("transparent", "Change", pp(r.change_pp))}`;
    } },
    yAxis: categoryAxis(rows.map((r) => r.level), { inverse: true, axisLabel: { color: C.ink, fontSize: 12, margin: 12 } }),
    xAxis: valueAxis({ max: 0.4, interval: 0.1, axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
    series: [
      { name: "FY25", type: "bar", barMaxWidth: 10, barGap: "30%", data: rows.map((r) => r.sow_fy25),
        itemStyle: { color: C.ghostHi, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", offset: [0, 7], color: C.ink, fontSize: 11, fontWeight: 600, formatter: (p: { dataIndex: number }) => pp(rows[p.dataIndex].change_pp) } },
      { name: "FY26", type: "bar", barMaxWidth: 10, data: rows.map((r) => r.sow_fy26),
        itemStyle: { ...hatch(C.lime), borderRadius: [0, 4, 4, 0] } },
    ],
  }), [rows]);
  return (
    <Card title="Every slice fell by about the same" sub="Share of wallet by customer attribute, FY25 against FY26"
      className="slices"
      actions={<select className="select" aria-label="Slice by" value={dim} onChange={(e) => setDim(e.target.value)}>
        {DIMS.map((d) => <option key={d}>{d}</option>)}
      </select>}>
      <div className="legend"><span><Swatch color={C.ghostHi} />FY25</span><span><Swatch color={C.lime} />FY26</span><Badge label="Measured" /></div>
      <EChart option={option} height={Math.max(220, rows.length * 34 + 30)} label={`Share of wallet by ${dim}, FY25 and FY26`} />
    </Card>
  );
}

const BANDS = ["Zero", "Low", "Mid", "High"] as const;

function Bands() {
  return (
    <Card title="Last year's band says nothing about this year's" sub="Customers by SoW band, FY25 (rows) → FY26 (columns), row shares"
      actions={<Badge label="Measured" />}>
      <div className="heat-wrap">
        <table className="heat">
          <thead><tr><th scope="col">FY25 ↓ · FY26 →</th>{BANDS.map((b) => <th key={b} scope="col">{b}</th>)}</tr></thead>
          <tbody>
            {segments.band_movement.map((r) => {
              const total = BANDS.reduce((s, b) => s + r[b], 0);
              return (
                <tr key={r.fy25_band}>
                  <th scope="row">{r.fy25_band}</th>
                  {BANDS.map((b) => {
                    const share = r[b] / total;
                    return (
                      <td key={b} style={{ background: `rgba(78,138,28,${(share * 2.2).toFixed(2)})`, color: share > 0.3 ? "#fff" : undefined }}
                        title={`${r[b].toLocaleString("en-IN")} customers`}>{pct(share, 0)}</td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="note">Every row splits the same way, whatever band the customer started in: regression to the mean, not a habit.</p>
    </Card>
  );
}

function Kmeans() {
  const km = segments.kmeans;
  const rows = [...segments.kmeans_clusters].sort((a, b) => b.sow_fy25 - a.sow_fy25);
  const option = useMemo(() => base({
    tooltip: { ...(base().tooltip as object), formatter: (p: { dataIndex: number }[]) => {
      const r = rows[p[0].dataIndex];
      return `<div style="color:${C.label};margin-bottom:4px">Cluster ${r.cluster} · ${r.customers.toLocaleString("en-IN")} customers</div>${tipRow(C.ghostHi, "FY25 SoW", pct(r.sow_fy25))}${tipRow(C.green, "FY26 SoW", pct(r.sow_fy26))}`;
    } },
    xAxis: categoryAxis(rows.map((r) => `C${r.cluster}`)),
    yAxis: valueAxis({ max: 1, interval: 0.25, axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => `${v * 100}%` } }),
    series: [
      { name: "FY25", type: "bar", barMaxWidth: 16, barGap: "20%", data: rows.map((r) => r.sow_fy25), itemStyle: { color: C.ghostHi, borderRadius: [4, 4, 0, 0] } },
      { name: "FY26", type: "bar", barMaxWidth: 16, data: rows.map((r) => r.sow_fy26), itemStyle: { ...hatch(C.green), borderRadius: [4, 4, 0, 0] } },
    ],
  }), [rows]);
  return (
    <Card title="Clusters that dissolve a year later" sub={`K-means on FY25 behaviour, k = ${num(km.seg_kmeans_k)}, ${num(km.seg_kmeans_customers)?.toLocaleString("en-IN")} customers`}
      actions={<Badge label="Measured" />}>
      <div className="duo">
        <div className="stat"><span className="stat-label">SoW spread, FY25</span><b className="stat-value">{dec(num(km.seg_kmeans_fy25_sow_spread_pp), 1)}pp</b></div>
        <div className="stat"><span className="stat-label">SoW spread, FY26</span><b className="stat-value">{dec(num(km.seg_kmeans_fy26_sow_spread_pp), 1)}pp</b></div>
      </div>
      <div className="legend"><span><Swatch color={C.ghostHi} />FY25</span><span><Swatch color={C.green} />FY26</span></div>
      <EChart option={option} height={220} label="Share of wallet by K-means cluster, FY25 and FY26" />
      <p className="note">The clusters are stable (ARI {dec(num(km.seg_kmeans_ari))}) but explain {pct(num(km.seg_kmeans_eta2), 2)} of the variation in FY26 share.</p>
    </Card>
  );
}

function Persist() {
  return (
    <Card title="What does persist" sub="Year-over-year correlation per customer, for traits worth segmenting on"
      actions={<Badge label="Measured" />}>
      <ul className="tracker">
        {[
          { label: "Purchase frequency at MetroMart", r: num(g.f13_r_purchases)! },
          { label: "Total MetroMart spend", r: num(g.f13_r_net)! },
          { label: "HSIC share of wallet", r: num(g.x1_persistence_r)! },
        ].map((t) => (
          <li key={t.label}>
            <div className="tracker-body">
              <div className="tracker-row"><b>{t.label}</b><span><b>r = {dec(t.r)}</b></span></div>
              <div className="meter" role="meter" aria-label={`${t.label}: r = ${dec(t.r)}`} aria-valuenow={t.r} aria-valuemin={0} aria-valuemax={1}>
                <span className="meter-fill" style={{ width: `${Math.max(t.r, 0.005) * 100}%` }} />
              </div>
            </div>
          </li>
        ))}
      </ul>
      <p className="note">So we segment on frequency and card age, and target the moment of payment, not the person.</p>
    </Card>
  );
}

export default function Segments() {
  return (
    <div className="page-grid">
      <div className="span-12"><Gate /></div>
      <div className="span-7"><Slices /></div>
      <div className="span-5"><Bands /></div>
      <div className="span-8"><Kmeans /></div>
      <div className="span-4"><Persist /></div>
    </div>
  );
}
