import { useMemo } from "react";
import { Badge, Card, Swatch } from "../components/ui";
import { base, C, categoryAxis, EChart, hatch, tipRow, valueAxis } from "../components/EChart";
import { key, num, priority } from "../lib/data";
import { count, inr, inrM, pct } from "../lib/format";

const SEG_COLOR: Record<string, string> = { A: C.rust, B: C.yellow, C: C.violet, D: C.green, E: C.lime, F: C.ghostHi, Z: C.ghost };

function Sizes() {
  const s = priority.sizes;
  const total = s.reduce((a, r) => a + r.customers, 0);
  return (
    <Card title="Who to prioritise" sub={`${count(total)} customers, segmented on card status, card age and purchase frequency. Ranges below are 95% intervals.`}
      actions={<Badge label="Measured" />}>
      <div className="stackbar tall" role="img" aria-label={s.map((r) => `${r.segment} ${r.name} ${count(r.customers)}`).join(", ")}>
        {s.map((r) => <span key={r.segment} style={{ flexGrow: r.customers, background: SEG_COLOR[r.segment] }} title={`${r.segment} · ${r.name}: ${count(r.customers)}`} />)}
      </div>
      <ul className="legend-list cols">
        {s.map((r) => (
          <li key={r.segment}><Swatch color={SEG_COLOR[r.segment]} /><span><b className="seg-id">{r.segment}</b> {r.name}</span><b>{count(r.customers)}</b></li>
        ))}
      </ul>
    </Card>
  );
}

function SegmentA() {
  const a = priority.segment_a;
  return (
    <section className="card seg-card win" aria-label="Segment A, closed but still shopping">
      <div className="seg-top"><span className="avatar seg-A">A</span><div><h2>Closed, still shopping</h2><p className="card-sub">Win-back · protect first</p></div></div>
      <p className="big sm">{inrM(num(a.seg_A_post_close_net))}</p>
      <p className="card-sub tight">MetroMart spend after closing, by the {count(num(a.seg_A_n_score))} customers in this segment at scoring <Badge label="Measured" /></p>
      <dl className="facts">
        <div><dt>In the segment today</dt><dd>{count(num(a.seg_A_n))}</dd></div>
        <div><dt>Spend per customer</dt><dd>{inr(num(a.seg_A_horizon_net_per_cust))}</dd></div>
      </dl>
    </section>
  );
}

function Boxes() {
  return (
    <>
      {priority.boxes.map((b) => (
        <section className="card seg-card" key={b.segment} aria-label={`Segment ${b.segment}, ${b.name}`}>
          <div className="seg-top"><span className={`avatar seg-${b.segment}`}>{b.segment}</span>
            <div><h2>{b.name}</h2><p className="card-sub">{count(b.customers)} customers</p></div><span className="seg-badge"><Badge label="Measured" /></span></div>
          <dl className="facts">
            <div><dt>Share of wallet</dt><dd>{pct(b.sow)}<small>{pct(b.sow_lo)}–{pct(b.sow_hi)}</small></dd></div>
            <div><dt>6-month closure</dt><dd>{pct(b.closure_6m)}<small>{pct(b.closure_lo)}–{pct(b.closure_hi)}</small></dd></div>
            <div><dt>Non-HSIC spend</dt><dd>{inr(b.nonhsic_per_cust)}</dd></div>
            <div><dt>Prime members</dt><dd>{pct(b.prime_share, 0)}</dd></div>
          </dl>
        </section>
      ))}
    </>
  );
}

const BANDS = [
  { id: "lt1k", label: "Under ₹1k" }, { id: "1k_3k", label: "₹1k–3k" }, { id: "3k_10k", label: "₹3k–10k" }, { id: "capped", label: "Capped" },
];

function Tickets() {
  const rows = BANDS.map((b) => ({
    ...b, fy25: key(`f5_hsic_share_fy25_${b.id}`), fy26: key(`f5_hsic_share_fy26_${b.id}`),
    sales: key(`f5_sales_fy26_${b.id}`), cash: key(`f5_cash_upi_gain_pp_${b.id}`),
  }));
  const option = useMemo(() => base({
    tooltip: { ...(base().tooltip as object), formatter: (p: { dataIndex: number }[]) => {
      const r = rows[p[0].dataIndex];
      return `<div style="color:${C.label};margin-bottom:4px">${r.label} tickets · ${inrM(r.sales)} FY26 sales</div>${tipRow(C.ghostHi, "HSIC share FY25", pct(r.fy25))}${tipRow(C.green, "HSIC share FY26", pct(r.fy26))}${tipRow("transparent", "Cash/UPI gain", `+${r.cash.toFixed(1)}pp`)}`;
    } },
    xAxis: categoryAxis(rows.map((r) => r.label)),
    yAxis: valueAxis({ max: 0.4, interval: 0.1, axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => `${Math.round(v * 100)}%` } }),
    series: [
      { name: "FY25", type: "bar", barMaxWidth: 22, barGap: "20%", data: rows.map((r) => r.fy25), itemStyle: { color: C.ghostHi, borderRadius: [4, 4, 0, 0] } },
      { name: "FY26", type: "bar", barMaxWidth: 22, data: rows.map((r) => r.fy26), itemStyle: { ...hatch(C.green), borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", color: C.label, fontSize: 11, formatter: (p: { value: number }) => pct(p.value, 0) } },
    ],
  }), [rows]);
  return (
    <Card title="HSIC lost share at every ticket size" sub="HSIC share of spend by basket size; ticket size is the one signal we can act on at checkout"
      actions={<Badge label="Measured" />}>
      <div className="legend"><span><Swatch color={C.ghostHi} />FY25</span><span><Swatch color={C.green} />FY26</span></div>
      <EChart option={option} height={230} label="HSIC share of spend by ticket band, FY25 and FY26" />
      <p className="note">Wallet carries {pct(key("f7_wallet_share_capped_fy26"), 0)} of capped tickets in FY26, against HSIC's {pct(key("f7_hsic_share_capped_fy26"), 0)}.</p>
    </Card>
  );
}

function Offers() {
  return (
    <Card title="Offers that fire at checkout" sub="Product fixes for everyone first, then moments, then segments" className="offers">
      <div className="table-wrap">
        <table className="data offers-table">
          <thead><tr><th scope="col">Offer</th><th scope="col">Layer</th><th scope="col">Who</th><th scope="col">What</th><th scope="col">Evidence</th></tr></thead>
          <tbody>
            {priority.offers.map((o) => (
              <tr key={o.id}>
                <th scope="row"><span className="offer-name"><span className="tx-id">{o.id}</span>{o.name}</span></th>
                <td><span className={`layer ${o.layer.startsWith("Seg") ? "seg" : o.layer.toLowerCase()}`}>{o.layer}</span></td>
                <td>{o.who}</td>
                <td>{o.what}</td>
                <td>{o.tests ? <span title={`Tests ${o.tests}`}><Badge label="Hypothesis" /></span> : <span className="muted">Proposed</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">Offer effects are simulated, not measured: nothing here has been piloted. A holdout pilot is the proposed next step.</p>
    </Card>
  );
}

const SCEN = ["conservative", "base", "optimistic"] as const;
const INPUTS = [
  { id: "interchange", label: "Interchange on HSIC spend" },
  { id: "revolve_income", label: "Revolve income on HSIC spend" },
  { id: "cofunding", label: "MetroMart co-funding of offers" },
];

function Economics() {
  const s = priority.scenarios;
  const pending = Object.keys(priority.economics).length === 0;
  return (
    <Card title="Break-even economics, net of rewards" sub="The inputs every offer is costed on" actions={<Badge label="Assumed" />}>
      <div className="table-wrap">
        <table className="data">
          <thead><tr><th scope="col">Input</th>{SCEN.map((c) => <th key={c} scope="col">{c[0].toUpperCase() + c.slice(1)}</th>)}</tr></thead>
          <tbody>
            {INPUTS.map((i) => (
              <tr key={i.id}>
                <th scope="row">{i.label}</th>
                {SCEN.map((c) => <td key={c}>{pct(num(s[`assumed_${i.id}_${c}`]), i.id === "interchange" ? 2 : 0)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pending && (
        <p className="pending" role="status"><Badge label="Pending" /><span>Break-even shift rates fill in when the economics module lands and <code>run_all.py</code> reruns.</span></p>
      )}
    </Card>
  );
}

export default function Priorities() {
  return (
    <div className="page-grid">
      <div className="span-8"><Sizes /></div>
      <div className="span-4"><SegmentA /></div>
      <div className="span-12 seg-grid"><Boxes /></div>
      <div className="span-12"><Offers /></div>
      <div className="span-7"><Tickets /></div>
      <div className="span-5"><Economics /></div>
    </div>
  );
}
