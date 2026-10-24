import { useMemo, useState } from "react";
import { Badge, Card, Delta, Icon, Segmented, Swatch } from "../components/ui";
import { base, C, categoryAxis, EChart, hatch, METHOD, tipRow, valueAxis } from "../components/EChart";
import { attrition, num } from "../lib/data";
import { calQuarter, count, dateLabel, dec, inrM, pct, pp } from "../lib/format";

const f = attrition.figures;
const q = attrition.closures_quarterly;
const pctAxis = (d = 0) => ({ color: C.label, fontSize: 11, formatter: (v: number) => `${(v * 100).toFixed(d)}%` });

function Kpis() {
  const first = num(f.f9_rate_first)!, last = num(f.f9_rate_last)!;
  const tiles = [
    { label: "Closures per quarter", value: pct(last), delta: <Delta dir="up" good={false}>from {pct(first)} in {calQuarter(q[0].quarter)}</Delta> },
    { label: "New cards close faster", value: `${dec(num(f.f10_2026_01_31_young_over_old), 1)}×`, delta: <span className="stat-note">cards under 6 months vs 3 years+, from 31 Jan 2026</span> },
    { label: "Closed, still shopping", value: count(num(f.f11_still_shopping)), delta: <span className="stat-note">customers with {inrM(num(f.f11_post_close_net))} of MetroMart spend after closing</span> },
    { label: "Silent attrition beyond trend", value: pp(attrition.silent[attrition.silent.length - 1].excess_time * 100), delta: <span className="stat-note">time-adjusted excess at {dateLabel(attrition.silent[attrition.silent.length - 1].cutoff)}</span> },
  ];
  return (
    <div className="kpi-row">
      {tiles.map((t) => (
        <section className="card stat" key={t.label} aria-label={t.label}>
          <span className="stat-label">{t.label} <Badge label="Measured" /></span>
          <b className="stat-value">{t.value}</b>
          {t.delta}
        </section>
      ))}
    </div>
  );
}

function Closures() {
  const option = useMemo(() => base({
    tooltip: { ...(base().tooltip as object), formatter: (p: { dataIndex: number }[]) => {
      const r = q[p[0].dataIndex];
      return `<div style="color:${C.label};margin-bottom:4px">${calQuarter(r.quarter)}</div>${tipRow(C.lime, "Closure rate", pct(r.rate, 2))}${tipRow("transparent", "Cards closed", count(r.closed))}${tipRow("transparent", "Open at start", count(r.open_at_start))}`;
    } },
    xAxis: categoryAxis(q.map((r) => calQuarter(r.quarter))),
    yAxis: valueAxis({ axisLabel: pctAxis(1) }),
    series: [{
      type: "bar", barMaxWidth: 40,
      data: q.map((r, i) => ({ value: r.rate, itemStyle: i === q.length - 1 ? { ...hatch(C.yellow), borderRadius: 8 } : { color: C.ghost, borderRadius: 8 } })),
      label: { show: true, position: "top", color: C.ink, fontSize: 12, fontWeight: 600,
        formatter: (p: { value: number; dataIndex: number }) => (p.dataIndex === 0 || p.dataIndex === q.length - 1 ? pct(p.value, 1) : "") },
    }],
  }), []);
  return (
    <Card title="Card closures doubled" sub="Share of open cards closed each calendar quarter" actions={<Badge label="Measured" />}>
      <EChart option={option} height={260} label="Quarterly card closure rate" />
    </Card>
  );
}

function ByAge() {
  const cutoffs = [...new Set(attrition.closure_by_age.map((r) => r.cutoff))];
  const bins = [...new Set(attrition.closure_by_age.map((r) => r.bin))];
  const colors = [C.ghostHi, C.yellow];
  const option = useMemo(() => base({
    tooltip: { ...(base().tooltip as object), formatter: (p: { name: string; seriesName: string; value: number; color: string; dataIndex: number; seriesIndex: number }[]) =>
      `<div style="color:${C.label};margin-bottom:4px">Card age ${p[0].name}</div>` + p.map((s) => tipRow(colors[s.seriesIndex], s.seriesName, pct(s.value, 1))).join("") },
    xAxis: categoryAxis(bins),
    yAxis: valueAxis({ axisLabel: pctAxis(0) }),
    series: cutoffs.map((c, i) => ({
      name: `Next 6 months from ${dateLabel(c)}`, type: "bar", barMaxWidth: 18, barGap: "20%",
      data: bins.map((b) => attrition.closure_by_age.find((r) => r.cutoff === c && r.bin === b)?.rate ?? null),
      itemStyle: i === cutoffs.length - 1 ? { ...hatch(colors[i]), borderRadius: [4, 4, 0, 0] } : { color: colors[i], borderRadius: [4, 4, 0, 0] },
    })),
  }), [bins, cutoffs]);
  return (
    <Card title="Young cards close most" sub="Six-month closure rate by card age" actions={<Badge label="Measured" />}>
      <div className="legend">{cutoffs.map((c, i) => <span key={c}><Swatch color={colors[i]} />From {dateLabel(c)}</span>)}</div>
      <EChart option={option} height={236} label="Six-month closure rate by card age at two cutoffs" />
    </Card>
  );
}

function Silent() {
  const rows = attrition.silent;
  const series = [
    { key: "observed", name: "Went quiet (observed)", color: C.ink },
    { key: "expected_fixed", name: "Expected from own past", color: C.ghostHi },
    { key: "expected_time", name: "Expected from portfolio trend", color: C.lime },
  ] as const;
  const option = useMemo(() => base({
    tooltip: { ...(base().tooltip as object), formatter: (p: { name: string; seriesIndex: number; value: number }[]) =>
      `<div style="color:${C.label};margin-bottom:4px">Next 6 months from ${p[0].name}</div>` + p.map((s) => tipRow(series[s.seriesIndex].color, series[s.seriesIndex].name, pct(s.value, 1))).join("") },
    xAxis: categoryAxis(rows.map((r) => dateLabel(r.cutoff))),
    yAxis: valueAxis({ max: 0.8, axisLabel: pctAxis(0) }),
    series: series.map((s) => ({
      name: s.name, type: "bar", barMaxWidth: 18, barGap: "20%", data: rows.map((r) => r[s.key]),
      itemStyle: s.key === "expected_time" ? { ...hatch(s.color), borderRadius: [4, 4, 0, 0] } : { color: s.color, borderRadius: [4, 4, 0, 0] },
    })),
  }), []);
  const last = rows[rows.length - 1];
  return (
    <Card title="Silent attrition is the trend, not a group" sub="Open-card customers with no HSIC use in the 6 months after each snapshot"
      actions={<Badge label="Measured" />}>
      <div className="legend">{series.map((s) => <span key={s.key}><Swatch color={s.color} />{s.name}</span>)}</div>
      <EChart option={option} height={236} label="Silent attrition observed versus two expected baselines" />
      <p className="note">Measured against each customer's own past, the usual test flags {pp(last.excess_fixed * 100)} of cardholders as silent attriters.
        Against the portfolio trend the excess is {pp(last.excess_time * 100)} (95% CI {pp(last.excess_time_lo * 100)} to {pp(last.excess_time_hi * 100)}).</p>
    </Card>
  );
}

function Decay() {
  const [view, setView] = useState<"raw" | "adj">("raw");
  const d = [...attrition.decay].sort((a, b) => b.months_before - a.months_before);
  const option = useMemo(() => {
    const x = categoryAxis(d.map((r) => (r.months_before === 0 ? "0" : `−${r.months_before}m`)), { boundaryGap: false });
    const tip = { ...(base().tooltip as object), axisPointer: { type: "line", lineStyle: { color: C.axis } } };
    if (view === "raw") {
      return base({
        tooltip: { ...tip, formatter: (p: { dataIndex: number }[]) => {
          const r = d[p[0].dataIndex];
          return `<div style="color:${C.label};margin-bottom:4px">${r.months_before} months before closing · ${count(r.rows)} rows</div>${tipRow(C.ink, "HSIC share, closers", pct(r.raw, 1))}${tipRow(C.green, "Expected from calendar", pct(r.expected, 1))}`;
        } },
        xAxis: x,
        yAxis: valueAxis({ min: 0.15, max: 0.3, interval: 0.05, axisLabel: pctAxis(0) }),
        grid: { left: 4, right: 18, top: 16, bottom: 4, containLabel: true },
        series: [
          { name: "Closers", type: "line", data: d.map((r) => r.raw), symbolSize: 7, lineStyle: { width: 2, color: C.ink }, itemStyle: { color: C.ink, borderColor: "#fff", borderWidth: 2 } },
          { name: "Expected", type: "line", data: d.map((r) => r.expected), symbol: "none", lineStyle: { width: 2, color: C.green, type: "solid" } },
        ],
      });
    }
    return base({
      tooltip: { ...tip, formatter: (p: { dataIndex: number }[]) => {
        const r = d[p[0].dataIndex];
        return `<div style="color:${C.label};margin-bottom:4px">${r.months_before} months before closing</div>${tipRow(C.ink, "Excess over calendar", pp(r.excess * 100))}${tipRow(C.limeSoft, "Chance band", `±${(r.chance_band * 100).toFixed(1)}pp`)}`;
      } },
      xAxis: x,
      grid: { left: 4, right: 18, top: 16, bottom: 4, containLabel: true },
      yAxis: valueAxis({ min: -0.04, max: 0.04, interval: 0.02, axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => pp(v * 100, 0) } }),
      series: [
        { name: "band-lo", type: "line", data: d.map((r) => -r.chance_band), symbol: "none", lineStyle: { opacity: 0 }, stack: "band", stackStrategy: "all", tooltip: { show: false } },
        { name: "band", type: "line", data: d.map((r) => 2 * r.chance_band), symbol: "none", lineStyle: { opacity: 0 }, stack: "band", stackStrategy: "all",
          areaStyle: { color: "rgba(156,205,90,0.28)" }, tooltip: { show: false } },
        { name: "Excess", type: "line", data: d.map((r) => r.excess), symbolSize: 7, lineStyle: { width: 2, color: C.ink },
          itemStyle: { color: C.ink, borderColor: "#fff", borderWidth: 2 },
          markLine: { silent: true, symbol: "none", label: { show: false }, lineStyle: { color: C.axis, type: "solid" }, data: [{ yAxis: 0 }] } },
      ],
    });
  }, [view, d]);
  return (
    <Card title="No decay before a card closes" sub="HSIC share of closers' MetroMart spend, months before closing (0 = the closing month)"
      actions={<Segmented label="Curve" value={view} onChange={setView} options={[
        { id: "raw", label: "Raw" }, { id: "adj", label: "Calendar-adjusted" }]} />}>
      <div className="legend">
        {view === "raw"
          ? <><span><Swatch color={C.ink} />Closers</span><span><Swatch color={C.green} />Expected from the calendar trend</span></>
          : <><span><Swatch color={C.ink} />Excess over the calendar trend</span><span><Swatch color={C.limeSoft} />Chance band</span></>}
        <Badge label="Measured" />
      </div>
      <EChart option={option} height={236} label={view === "raw" ? "Closers' HSIC share before closing, raw and expected" : "Closers' excess HSIC share over the calendar trend, with chance band"} />
      <p className="note">The raw curve falls from {pct(num(f.x4_raw_m12), 1)} to {pct(num(f.x4_raw_m0), 1)}, but the whole book fell too.
        Adjusted slope {dec(num(f.x4_slope_pp_per_month))}pp a month (95% CI {dec(num(f.x4_slope_ci_lo_pp))} to {dec(num(f.x4_slope_ci_hi_pp))}): no early warning to act on.</p>
    </Card>
  );
}

function Model() {
  const best = Math.max(...attrition.closure_model.map((m) => m.roc_auc));
  return (
    <Card title="What predicts a closure" sub={`Test set of ${count(num(f.cm_test_cards))} cards, ${pct(num(f.cm_test_base_rate), 1)} closed`}
      actions={<Badge label="Measured" />}>
      <div className="table-wrap">
        <table className="data">
          <thead><tr><th scope="col">Model</th><th scope="col">ROC AUC</th><th scope="col">PR AUC</th><th scope="col">Top-decile capture</th></tr></thead>
          <tbody>
            {attrition.closure_model.map((m) => (
              <tr key={m.model} className={m.roc_auc === best ? "best" : ""}>
                <th scope="row">{m.model}{m.roc_auc === best && <span className="tag">Best</span>}</th>
                <td>{dec(m.roc_auc, 3)}</td><td>{dec(m.pr_auc, 3)}</td><td>{pct(m.top_decile_capture, 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">Card age alone matches every richer model; recent usage adds {dec(num(f.x5_usage_increment_roc), 4)} ROC AUC.
        Protect cards by age, not by a usage alert.</p>
    </Card>
  );
}

function AfterClose() {
  const mix = [
    { method: "Wallet", share: num(f.f11_mix_wallet)! },
    { method: "Cash/UPI", share: num(f.f11_mix_cash_upi)! },
    { method: "Other CC", share: num(f.f11_mix_other_cc)! },
    { method: "Debit", share: num(f.f11_mix_debit)! },
  ];
  return (
    <Card title="How closers pay now" sub="Payment mix of MetroMart spend after the card closed" actions={<Badge label="Measured" />}>
      <p className="big sm">{inrM(num(f.f11_post_close_net))}</p>
      <p className="card-sub tight">spent by {count(num(f.f11_still_shopping))} closed-card customers</p>
      <div className="stackbar" role="img" aria-label={mix.map((r) => `${r.method} ${pct(r.share, 0)}`).join(", ")}>
        {mix.map((r) => <span key={r.method} style={{ flexGrow: r.share, background: METHOD[r.method] }} />)}
      </div>
      <ul className="legend-list">
        {mix.map((r) => <li key={r.method}><Swatch color={METHOD[r.method]} />{r.method}<b>{pct(r.share, 0)}</b></li>)}
      </ul>
      <a className="link" href="#/priorities">Win-back offer <Icon name="arrow" size={16} /></a>
    </Card>
  );
}

export default function Attrition() {
  return (
    <div className="page-grid">
      <div className="span-12"><Kpis /></div>
      <div className="span-7"><Closures /></div>
      <div className="span-5"><ByAge /></div>
      <div className="span-6"><Silent /></div>
      <div className="span-6"><Decay /></div>
      <div className="span-8"><Model /></div>
      <div className="span-4"><AfterClose /></div>
    </div>
  );
}
