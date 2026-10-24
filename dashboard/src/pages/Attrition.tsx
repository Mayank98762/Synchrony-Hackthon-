import { useMemo, useState } from "react";
import { usePageData, num, type Attrition as Data } from "../lib/data";
import { calQuarter, count, dateLabel, dec, inrM, pct, pp } from "../lib/format";
import { PageState, Panel, TitleRow } from "../components/ui";
import { C, EChart, base, categoryAxis, valueAxis } from "../components/EChart";

const AGE = { "<6m": "Under 6 months", "6-12m": "6–12 months", "1-2y": "1–2 years", "2-3y": "2–3 years", "3y+": "3+ years" } as Record<string, string>;
const MODELS: Record<string, string> = {
  "B2 card age": "Card age alone", "LR-profile": "Logistic regression, profile", "LR-all": "Logistic regression, all features",
  HGB: "Gradient boosting, all features", "LR-usage": "Logistic regression, usage only", "B1 recency": "Months since last HSIC use",
  "B0 random": "Random guess",
};
const MIX = [["cash_upi", "Cash/UPI"], ["wallet", "MetroMart Wallet"], ["debit", "Debit card"], ["other_cc", "Other banks' cards"]] as const;

export default function Attrition() {
  const { data, error } = usePageData<Data>("attrition");
  const [mode, setMode] = useState<"raw" | "adjusted">("adjusted");
  const decay = useMemo(() => data && decayOption(data, mode), [data, mode]);
  const age = useMemo(() => data && ageOption(data), [data]);
  const quarters = useMemo(() => data && quarterOption(data), [data]);
  if (!data || !decay || !age || !quarters) return <PageState title="Attrition and closures" error={error} />;

  const f = data.figures;
  const d = [...data.decay].sort((a, b) => b.months_before - a.months_before);
  const excessAbs = Math.max(...d.map((r) => Math.abs(r.excess))) * 100;
  const models = [...data.closure_model].sort((a, b) => b.roc_auc - a.roc_auc);
  const testAge = data.closure_by_age.filter((r) => r.cutoff === "2026-01-31");
  const young = testAge[0].rate, old = testAge.at(-1)!.rate;

  return (
    <>
      <TitleRow
        title="Attrition and closures"
        sub={<>Silent attrition is real and universal: measured against the portfolio&rsquo;s own decline, no extra cardholders go quiet.
          Closures doubled, and cards under six months close at {(young / old).toFixed(1)}× the rate of cards over three years.</>}
      />

      <div className="grid">
        <Panel span="s8" title="HSIC use in the 12 months before a card closes" meta={`${count(d.reduce((s, r) => s + r.rows, 0))} purchases on closed cards`}>
          <div className="filters">
            <div className="segmented" role="group" aria-label="View">
              <button aria-pressed={mode === "raw"} onClick={() => setMode("raw")}>Raw</button>
              <button aria-pressed={mode === "adjusted"} onClick={() => setMode("adjusted")}>Calendar-adjusted</button>
            </div>
            <span className="legend">{mode === "raw"
              ? <><span><i className="line" style={{ background: C.hue }} />Closing cards</span><span><i className="dash" />Whole portfolio, same months</span></>
              : <><span><i className="line" style={{ background: C.hue }} />Closing cards minus the portfolio</span><span><i style={{ background: C.pale, borderRadius: 2 }} />Chance range</span></>}
            </span>
          </div>
          <p className="lede" style={{ marginTop: 0 }}>{mode === "raw"
            ? <>Raw, HSIC use falls from {pct(num(f.x4_raw_m12))} a year before closing to {pct(num(f.x4_raw_m0))} at closing: it looks like customers fade out first.</>
            : <>Against the whole portfolio in the same months, closing cards are never more than {excessAbs.toFixed(1)} points off (slope {pp(num(f.x4_slope_pp_per_month)!, 2)} a month, 95% CI {pp(num(f.x4_slope_ci_lo_pp)!, 2)} to {pp(num(f.x4_slope_ci_hi_pp)!, 2)}): the fade is the calendar.</>}
          </p>
          <EChart option={decay} height={214} label={mode === "raw" ? "Raw HSIC use before closure falls from 27% to 20%, alongside the portfolio" : "Calendar-adjusted HSIC use before closure stays near zero, inside the chance range"} />
        </Panel>
        <Panel span="s4" title="Who goes quiet in the next 6 months" meta="3 snapshots">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Snapshot</th><th className="n">Went quiet</th><th className="n">vs own past</th><th className="n">vs trend</th></tr></thead>
              <tbody>
                {data.silent.map((r) => (
                  <tr key={r.cutoff}>
                    <td>{dateLabel(r.cutoff)}<span className="sub">{count(r.customers)} cards</span></td>
                    <td className="n">{pct(r.observed)}</td>
                    <td className="n">{pp(r.excess_fixed * 100)}</td>
                    <td className="n"><b style={{ fontWeight: 500 }}>{pp(r.excess_time * 100)}</b></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="foot">The usual test (against each customer&rsquo;s own past) flags about a fifth of cardholders. Against the portfolio trend the excess is about zero: everyone is drifting at once.</p>
        </Panel>
      </div>

      <div className="grid">
        <Panel span="s8" title="Six-month closure rate by card age" meta={
          <span className="legend"><span><i style={{ background: C.pale, borderRadius: 2 }} />Cards open on 31 Jul 2025</span>
            <span><i style={{ background: C.hue, borderRadius: 2 }} />Cards open on 31 Jan 2026</span></span>}>
          <p className="lede">The younger the card, the likelier it closes in the next six months, at both snapshots. Card age is the one early warning that works.</p>
          <EChart option={age} height={300} label={`Six-month closure rate falls with card age, from ${pct(young)} under 6 months to ${pct(old)} over 3 years`} />
        </Panel>
        <Panel span="s4" title="What predicts a closure" meta={`ROC-AUC · ${count(num(f.cm_test_cards))} cards`}>
          <div className="barlist">
            {models.map((m, i) => (
              <div key={m.model} className={i === 0 ? "first" : ""}>
                <div className="lab"><span>{MODELS[m.model] ?? m.model}</span><b>{dec(m.roc_auc, 3)}</b></div>
                <div className="track"><div className="fill" style={{ width: `${((m.roc_auc - 0.5) / (models[0].roc_auc - 0.5)) * 88}%` }} /></div>
              </div>
            ))}
          </div>
          <p className="foot">Bars measure skill above a coin flip (0.5). Usage adds nothing once card age is known.</p>
        </Panel>
      </div>

      <div className="grid">
        <Panel span="s8" title="Closures per open card, by calendar quarter" meta="Closed in the quarter ÷ open at its start">
          <EChart option={quarters} height={236} label={`Closures per open card rose from ${pct(num(f.f9_rate_first))} to ${pct(num(f.f9_rate_last))} a quarter`} />
        </Panel>
        <Panel span="s4" title="After closing the card" meta="Still shopping at MetroMart">
          <p className="lede" style={{ marginTop: 0 }}>{count(num(f.f11_still_shopping))} people closed the card and spent {inrM(num(f.f11_post_close_net))} at MetroMart afterwards, paid like this:</p>
          <div className="rows">
            {[...MIX].sort((p, q) => (num(f[`f11_mix_${q[0]}`]) ?? 0) - (num(f[`f11_mix_${p[0]}`]) ?? 0)).map(([k, label]) => (
              <div className="row" key={k}><span className="grow">{label}</span><span className="fig">{pct(num(f[`f11_mix_${k}`]))}</span></div>
            ))}
          </div>
        </Panel>
      </div>
    </>
  );
}

function decayOption(d: Data, mode: "raw" | "adjusted") {
  const rows = [...d.decay].sort((a, b) => b.months_before - a.months_before);
  const x = rows.map((r) => (r.months_before === 0 ? "Close" : `${r.months_before} mo`));
  const tip = { ...(base().tooltip as object) };
  if (mode === "raw") {
    return base({
      tooltip: { ...tip, valueFormatter: (v: number) => pct(v) },
      xAxis: categoryAxis(x, { axisLabel: { color: C.label, fontSize: 12, margin: 10, interval: 1 } }),
      yAxis: valueAxis({ min: 0, max: 0.35, interval: 0.05, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
      series: [
        { name: "Closing cards", type: "line", data: rows.map((r) => r.raw), lineStyle: { color: C.hue, width: 2 }, itemStyle: { color: C.hue }, showSymbol: false },
        { name: "Whole portfolio", type: "line", data: rows.map((r) => r.expected), lineStyle: { color: C.grey, width: 2, type: [4, 4] }, itemStyle: { color: C.grey }, showSymbol: false },
      ],
    });
  }
  return base({
    tooltip: { ...tip, formatter: (ps: { dataIndex: number }[]) => {
      const r = rows[ps[0].dataIndex];
      return `${x[ps[0].dataIndex]}<br/>Closing cards minus portfolio: <b style="font-weight:500">${pp(r.excess * 100)}</b><br/>Chance range ±${(r.chance_band * 100).toFixed(1)}pp`;
    } },
    xAxis: categoryAxis(x, { axisLabel: { color: C.label, fontSize: 12, margin: 10, interval: 1 } }),
    yAxis: valueAxis({ min: -0.06, max: 0.06, interval: 0.03, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => pp(v * 100, 0) } }),
    series: [
      { name: "band-low", type: "line", stack: "band", stackStrategy: "all", data: rows.map((r) => -r.chance_band), lineStyle: { opacity: 0 }, showSymbol: false, silent: true, tooltip: { show: false } },
      { name: "band", type: "line", stack: "band", stackStrategy: "all", data: rows.map((r) => 2 * r.chance_band), lineStyle: { opacity: 0 }, areaStyle: { color: C.pale, opacity: 0.55 }, showSymbol: false, silent: true },
      { name: "Excess", type: "line", data: rows.map((r) => r.excess), lineStyle: { color: C.hue, width: 2 }, itemStyle: { color: C.hue }, showSymbol: false,
        markLine: { silent: true, symbol: "none", label: { show: false }, lineStyle: { color: C.axis, width: 1, type: "solid" }, data: [{ yAxis: 0 }] } },
    ],
  });
}

function ageOption(d: Data) {
  const bins = Object.keys(AGE);
  const at = (cut: string) => bins.map((b) => d.closure_by_age.find((r) => r.cutoff === cut && r.bin === b)!.rate);
  return base({
    tooltip: { ...(base().tooltip as object), axisPointer: { type: "shadow", shadowStyle: { color: "rgba(0,0,0,0.03)" } }, valueFormatter: (v: number) => pct(v) }, // taste-skill-ignore: the hover band, not a resting shadow
    xAxis: categoryAxis(bins.map((b) => AGE[b]), { boundaryGap: true }),
    yAxis: valueAxis({ min: 0, max: 0.16, interval: 0.04, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
    series: [
      { name: "Open on 31 Jul 2025", type: "bar", data: at("2025-07-31"), itemStyle: { color: C.pale }, barGap: "8%", barMaxWidth: 44 },
      { name: "Open on 31 Jan 2026", type: "bar", data: at("2026-01-31"), itemStyle: { color: C.hue }, barMaxWidth: 44,
        label: { show: true, position: "top", color: C.text, fontSize: 12, fontWeight: 500, formatter: (p: { value: number }) => pct(p.value) } },
    ],
  });
}

function quarterOption(d: Data) {
  const q = d.closures_quarterly;
  return base({
    grid: { left: 8, right: 12, top: 26, bottom: 4, containLabel: true },
    tooltip: { ...(base().tooltip as object), formatter: (ps: { dataIndex: number }[]) => {
      const r = q[ps[0].dataIndex];
      return `${calQuarter(r.quarter)}<br/><b style="font-weight:500">${pct(r.rate)}</b> · ${count(r.closed)} of ${count(r.open_at_start)} open cards`;
    } },
    xAxis: categoryAxis(q.map((r) => calQuarter(r.quarter)), { boundaryGap: ["4%", "4%"] }),
    yAxis: valueAxis({ min: 0, max: 0.04, interval: 0.01, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
    series: [{
      type: "line", data: q.map((r, i) => ({ value: r.rate, label: i === 0 || i === q.length - 1
        ? { show: true, position: "top", distance: 8, formatter: () => pct(r.rate), color: C.text, fontSize: 13, fontWeight: 500 } : undefined })),
      lineStyle: { color: C.ink, width: 2 }, itemStyle: { color: C.ink }, symbol: "circle", symbolSize: 6,
    }],
  });
}
