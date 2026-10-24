import { useMemo, useState } from "react";
import { Badge, Card, Delta, Icon, Meter, Segmented, Swatch } from "../components/ui";
import { base, C, categoryAxis, EChart, hatch, METHOD, tipRow, valueAxis } from "../components/EChart";
import { experiments, key, overview, priority, segments } from "../lib/data";
import { inr, inrM, monthLabel, pct, pp, quarterLabel } from "../lib/format";

const k = overview.kpis;
const sowFy25 = k.f1_sow_fy25.value as number;
const sowFy26 = k.f1_sow_fy26.value as number;
const slope = k.f1_slope_pp_per_quarter.value as number;
const netAug = k.f14_aug24_net_per_card.value as number;
const netMay = k.f14_may26_net_per_card.value as number;
const hsicAug = k.f14_aug24_hsic_per_card.value as number;
const hsicMay = k.f14_may26_hsic_per_card.value as number;

function TrendChart({ view }: { view: "sow" | "spend" }) {
  const option = useMemo(() => {
    if (view === "sow") {
      const q = overview.sow_quarterly;
      return base({
        tooltip: { ...(base().tooltip as object), formatter: (p: { name: string; value: number }[]) =>
          `<div style="color:${C.label};margin-bottom:4px">${p[0].name}</div>${tipRow(C.green, "HSIC share of wallet", pct(p[0].value))}` },
        xAxis: categoryAxis(q.map((d) => quarterLabel(d.quarter))),
        yAxis: valueAxis({ max: 0.4, axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => `${v * 100}%` } }),
        series: [{
          type: "bar", barMaxWidth: 52, barCategoryGap: "28%",
          data: q.map((d, i) => ({
            value: d.sow,
            itemStyle: i === q.length - 1 ? { ...hatch(C.lime), borderRadius: 8 } : { color: C.ghost, borderRadius: 8 },
            emphasis: { itemStyle: i === q.length - 1 ? {} : { color: C.ghostHi } },
          })),
          // label the start and the end only; the tooltip carries the quarters between
          label: { show: true, position: "top", color: C.ink, fontSize: 12, fontWeight: 600,
            formatter: (p: { value: number; dataIndex: number }) => (p.dataIndex === 0 || p.dataIndex === q.length - 1 ? pct(p.value, 1) : "") },
        }],
      });
    }
    const m = overview.per_card_monthly;
    return base({
      tooltip: { ...(base().tooltip as object), axisPointer: { type: "line", lineStyle: { color: C.axis } },
        formatter: (p: { name: string; value: number; color: string; seriesName: string }[]) =>
          `<div style="color:${C.label};margin-bottom:4px">${p[0].name}</div>` +
          p.map((s) => tipRow(s.color, s.seriesName, inr(s.value))).join("") },
      xAxis: categoryAxis(m.map((d) => monthLabel(d.month)), { boundaryGap: false }),
      yAxis: valueAxis({ axisLabel: { color: C.label, fontSize: 11, formatter: (v: number) => `₹${v}` } }),
      series: [
        { name: "All MetroMart spend per card", type: "line", data: m.map((d) => d.net_per_card), symbol: "none",
          lineStyle: { width: 2, color: C.ink }, itemStyle: { color: C.ink } },
        { name: "Spend on HSIC per card", type: "line", data: m.map((d) => d.hsic_per_card), symbol: "none",
          lineStyle: { width: 2, color: C.green }, itemStyle: { color: C.green },
          areaStyle: { color: "rgba(78,138,28,0.10)" } },
      ],
    });
  }, [view]);
  return <div className="chart-fill" style={{ minHeight: 300 }}><EChart option={option} height={300}
    label={view === "sow" ? "HSIC share of wallet by quarter, FY25 Q1 to FY26 Q4" : "Monthly spend per card: all MetroMart spend versus spend on HSIC"} /></div>;
}

function Hero() {
  const [view, setView] = useState<"sow" | "spend">("sow");
  return (
    <section className="card hero" aria-label="Share of wallet trend">
      <div className="hero-main">
        <header className="card-head">
          <div>
            <p className="big">{pct(sowFy26)}</p>
            <p className="card-sub">HSIC share of wallet, FY26 <Badge label="Measured" /></p>
          </div>
          <div className="card-actions">
            <Segmented label="Chart" value={view} onChange={setView} options={[
              { id: "sow", label: <><Icon name="bars" size={16} /><span>Share</span></>, title: "Share of wallet by quarter" },
              { id: "spend", label: <><Icon name="line" size={16} /><span>Spend</span></>, title: "Spend per card by month" },
            ]} />
          </div>
        </header>
        <div className="legend">
          {view === "sow"
            ? <><span><Swatch color={C.ghostHi} />Earlier quarters</span><span><Swatch color={C.lime} />Latest quarter</span></>
            : <><span><Swatch color={C.ink} />All MetroMart spend per card</span><span><Swatch color={C.green} />Spend on HSIC per card</span></>}
        </div>
        <TrendChart view={view} />
      </div>
      <div className="hero-side">
        <div className="stat">
          <span className="stat-label">Share of wallet, FY25</span>
          <b className="stat-value">{pct(sowFy25)}</b>
          <Delta dir="down" good={false}>{pp((sowFy26 - sowFy25) * 100)} by FY26</Delta>
        </div>
        <div className="stat">
          <span className="stat-label">Trend per quarter</span>
          <b className="stat-value">{pp(slope)}</b>
          <Delta dir="down" good={false}>{overview.sow_quarterly.length} quarters, no plateau</Delta>
        </div>
        <div className="stat">
          <span className="stat-label">HSIC spend per card, {monthLabel("2026-05")}</span>
          <b className="stat-value">{inr(hsicMay)}</b>
          <Delta dir="down" good={false}>from {inr(hsicAug)} in {monthLabel("2024-08")}</Delta>
          <span className="stat-note">All spend per card held at {inr(netMay)} (was {inr(netAug)}). They still shop; they pay another way.</span>
        </div>
      </div>
    </section>
  );
}

function Cashback() {
  const earned = k.f8_rewards_earned_fy26.value as number;
  const left = key("f8_all_left_on_table");
  const primeGe = k.f8_prime_ge_left_on_table.value as number;
  return (
    <Card title="Cashback left on the table, FY26" sub="Rewards cardholders would have earned had they paid with HSIC"
      actions={<Badge label="Measured" />}>
      <Meter value={left} max={left + earned} label="Cashback left on the table as a share of all cashback available" />
      <div className="meter-scale">
        <span><b>{inrM(left, 2)}</b> left on the table</span>
        <span>{inrM(earned, 2)} earned</span>
      </div>
      <p className="note">Prime Grocery + Electronics alone left {inrM(primeGe, 2)}: the richer Prime reward did not move usage.
        Make the reward visible at the till, not bigger.</p>
    </Card>
  );
}

function Finding() {
  const s = segments.slices.filter((d) => d.dimension !== "Closer");
  const changes = s.map((d) => d.change_pp);
  const lo = Math.min(...changes), hi = Math.max(...changes);
  return (
    <section className="card finding" aria-label="The finding">
      <div className="finding-copy">
        <h2>The decline is universal, not a targeting problem</h2>
        <p>All {s.length} customer slices lost between {pp(hi)} and {pp(lo)} of share. Customers do not keep a stable
          HSIC habit, so clustering on share of wallet finds noise.</p>
        <a className="link" href="#/segments">See the heterogeneity test <Icon name="arrow" size={16} /></a>
      </div>
      <div className="mosaic" role="img" aria-label={`${s.length} slices, each losing between ${pp(hi)} and ${pp(lo)}`}>
        {s.map((d) => (
          <span key={d.dimension + d.level} title={`${d.dimension}: ${d.level} ${pp(d.change_pp)}`}
            style={{ opacity: 0.45 + 0.55 * ((d.change_pp - hi) / (lo - hi)) }} />
        ))}
      </div>
    </section>
  );
}

function LossShare() {
  const rows = [...overview.loss_share].sort((a, b) => b.share - a.share);
  return (
    <Card title="Where the lost share went" sub="Stayers' FY25 → FY26 shift, by payment method">
      <p className="big sm">{pp(overview.bridge.stayer)}</p>
      <p className="card-sub tight">HSIC share change among stayers <Badge label="Measured" /></p>
      <div className="stackbar" role="img" aria-label={rows.map((r) => `${r.method} ${pct(r.share, 0)}`).join(", ")}>
        {rows.map((r) => <span key={r.method} style={{ flexGrow: r.share, background: METHOD[r.method] }} />)}
      </div>
      <ul className="legend-list">
        {rows.map((r) => (
          <li key={r.method}><Swatch color={METHOD[r.method]} />{r.method}<b>{pct(r.share, 0)}</b></li>
        ))}
      </ul>
      <p className="note">Customers who stayed drove {pp(overview.bridge.stayer)} of the {pp(overview.bridge.total)} total.</p>
    </Card>
  );
}

function StillShopping() {
  const shopping = k.f11_still_shopping.value as number;
  const closed = key("f11_closed_cards");
  const share = shopping / closed;
  // a 180° gauge drawn as one arc; the filled length is the share of closers who still shop
  const r = 80, len = Math.PI * r;
  return (
    <Card title="Closed, still shopping" sub="Closed-card customers who kept shopping at MetroMart">
      <p className="big sm">{inrM(k.f11_post_close_net.value as number)}</p>
      <p className="card-sub tight">their MetroMart spend after closing <Badge label="Measured" /></p>
      <div className="gauge">
        <svg viewBox="0 0 200 112" role="img" aria-label={`${pct(share, 0)} of closers still shop`}>
          <defs>
            <pattern id="g-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="6" height="6" fill={C.lime} /><rect width="2" height="6" fill="rgba(255,255,255,.35)" />
            </pattern>
          </defs>
          <path d="M20 100a80 80 0 0 1 160 0" fill="none" stroke={C.ghost} strokeWidth="22" />
          <path d="M20 100a80 80 0 0 1 160 0" fill="none" stroke="url(#g-hatch)" strokeWidth="22"
            strokeDasharray={`${share * len} ${len}`} />
        </svg>
        <div className="gauge-label"><b>{pct(share, 0)}</b><span>{shopping.toLocaleString("en-IN")} of {closed.toLocaleString("en-IN")} closers</span></div>
      </div>
      <a className="link" href="#/attrition">Win them back <Icon name="arrow" size={16} /></a>
    </Card>
  );
}

function Mix() {
  return (
    <Card title="Payment mix" sub="Share of MetroMart spend, FY26 against FY25" actions={<Badge label="Measured" />}>
      <ul className="tracker">
        {overview.mix.map((m) => {
          const d = (m.fy26 - m.fy25) * 100;
          return (
            <li key={m.method}>
              <span className="thumb" style={{ background: METHOD[m.method] }} aria-hidden="true" />
              <div className="tracker-body">
                <div className="tracker-row"><b>{m.method}</b><span><b>{pct(m.fy26)}</b> / {pct(m.fy25)}</span></div>
                <Meter value={m.fy26} max={0.4} color={METHOD[m.method]} marker={m.fy25}
                  label={`${m.method}: ${pct(m.fy26)} in FY26, ${pct(m.fy25)} in FY25`} />
                <span className={`tracker-sub ${d < 0 ? "neg" : ""}`}>{pp(d)} since FY25</span>
              </div>
            </li>
          );
        })}
      </ul>
      <p className="note"><span className="marker-key" aria-hidden="true" /> marks FY25</p>
    </Card>
  );
}

function CardPanel() {
  const prime = segments.slices.find((d) => d.dimension === "Membership" && d.level === "Prime")!;
  const non = segments.slices.find((d) => d.dimension === "Membership" && d.level === "Non-Prime")!;
  const sizes = Object.fromEntries(priority.sizes.map((s) => [s.segment, s]));
  const people = ["A", "B", "C", "D", "E"].map((id) => sizes[id]).filter(Boolean);
  const actions = [
    { href: "#/segments", icon: "segments", label: "Segments" },
    { href: "#/attrition", icon: "attrition", label: "Closures" },
    { href: "#/priorities", icon: "priorities", label: "Offers" },
    { href: "#/overview/tests", icon: "flask", label: "Tests" },
  ] as const;
  return (
    <Card title="The card" sub="Share of wallet by membership, FY26" className="side-card">
      <div className="cards-row">
        <div className="plastic prime">
          <span className="plastic-top"><span>Prime</span><b>HSIC × MetroMart</b></span>
          <span className="chip-ic" aria-hidden="true" />
          <span className="plastic-num">{pct(prime.sow_fy26)} <small>{pp(prime.change_pp)}</small></span>
          <span className="plastic-foot"><span>Richer Grocery + Electronics cashback</span></span>
        </div>
        <div className="plastic plain">
          <span className="plastic-top"><span>Non-Prime</span></span>
          <span className="chip-ic" aria-hidden="true" />
          <span className="plastic-num">{pct(non.sow_fy26)} <small>{pp(non.change_pp)}</small></span>
          <span className="plastic-foot"><span>Base cashback</span></span>
        </div>
      </div>
      <p className="note">Richer rewards, the same share: Prime sits {(Math.abs(prime.sow_fy26 - non.sow_fy26) * 100).toFixed(1)}pp from Non-Prime.</p>
      <div className="quick">
        {actions.map((a) => (
          <a key={a.label} href={a.href}><span className="quick-ic"><Icon name={a.icon} /></span>{a.label}</a>
        ))}
      </div>
      <h3 className="minor">Who to prioritise</h3>
      <div className="people">
        {people.map((p) => (
          <a key={p.segment} href="#/priorities" className="person" title={`${p.name}: ${p.customers.toLocaleString("en-IN")} customers`}>
            <span className={`avatar seg-${p.segment}`}>{p.segment}</span>
            <span>{p.name.split(",")[0].replace("Closed", "Win-back")}</span>
          </a>
        ))}
      </div>
    </Card>
  );
}

function verdictKind(v: string) {
  if (/^infeasible/i.test(v)) return "Infeasible";
  return "Not supported";
}

function Tests() {
  const [filter, setFilter] = useState<"all" | "Not supported" | "Infeasible">("all");
  const rows = experiments.filter((e) => filter === "all" || verdictKind(e.verdict) === filter);
  return (
    <Card title="Hypotheses we tested" sub={`${experiments.length} common hypotheses, and what the data said`}
      className="side-card tests" id="tests"
      actions={<select className="select" aria-label="Filter hypotheses" value={filter}
        onChange={(e) => setFilter(e.target.value as typeof filter)}>
        <option value="all">All</option><option>Not supported</option><option>Infeasible</option>
      </select>}>
      <div className="list-head"><span>Hypothesis</span><span>Result</span></div>
      <ul className="tx">
        {rows.map((e) => {
          const kind = verdictKind(e.verdict);
          return (
            <li key={e.id}>
              <span className={`tx-id ${kind === "Infeasible" ? "inf" : ""}`}>{e.id}</span>
              <div className="tx-body">
                <b>{e.expected}</b>
                <span>{e.verdict.replace(/^infeasible: /, "")}</span>
              </div>
              <span className={`tx-status ${kind === "Infeasible" ? "inf" : ""}`}>{kind}</span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

export default function Overview() {
  return (
    <div className="ov">
      <Hero />
      <div className="ov-cash"><Cashback /></div>
      <div className="ov-find"><Finding /></div>
      <div className="ov-a"><LossShare /></div>
      <div className="ov-b"><StillShopping /></div>
      <div className="ov-c"><Mix /></div>
      <div className="ov-side"><CardPanel /></div>
      <div className="ov-tests"><Tests /></div>
    </div>
  );
}
