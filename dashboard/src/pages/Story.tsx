import { useMemo } from "react";
import { usePageData, num, type Overview } from "../lib/data";
import { inr, inrM, count, pct, pp, quarterLabel, monthLabel, signedInr } from "../lib/format";
import { Bad, Kpi, PageState, Panel, TitleRow } from "../components/ui";
import { C, EChart, base, categoryAxis, valueAxis } from "../components/EChart";

const METHOD_NAME: Record<string, string> = {
  HSIC: "HSIC card", "Cash/UPI": "Cash/UPI", Wallet: "MetroMart Wallet", Debit: "Debit card", "Other CC": "Other banks' cards",
};
const STRIP_ORDER = ["HSIC", "Wallet", "Cash/UPI", "Debit", "Other CC"];
const STRIP_CLASS: Record<string, string> = { HSIC: "hsic", Wallet: "m1", "Cash/UPI": "m2", Debit: "m3", "Other CC": "m4" };
const STRIP_SWATCH: Record<string, string> = { HSIC: C.hue, Wallet: "#3d3d3d", "Cash/UPI": "#6b6b6b", Debit: "#b9b9b9", "Other CC": "#dcdcdc" };

const r1 = (v: number) => Math.round(v * 10) / 10;
const signedRupee = (v: number) => `${v < 0 ? "−" : "+"}₹${Math.abs(v).toFixed(1)}`;

export default function Story() {
  const { data, error } = usePageData<Overview>("overview");
  const quarterly = useMemo(() => data && sowQuarterOption(data), [data]);
  const perCard = useMemo(() => data && perCardOption(data), [data]);
  if (!data || !quarterly || !perCard) return <PageState title="Share of wallet" error={error} />;

  const k = data.kpis;
  // every change is the difference of the two values as displayed
  const sow25 = r1(num(k.f1_sow_fy25)! * 100), sow26 = r1(num(k.f1_sow_fy26)! * 100);
  const hsicAug = Math.round(num(k.f14_aug24_hsic_per_card)!), hsicMay = Math.round(num(k.f14_may26_hsic_per_card)!);
  const netAug = Math.round(num(k.f14_aug24_net_per_card)!), netMay = Math.round(num(k.f14_may26_net_per_card)!);
  const clFirst = r1(num(k.f9_rate_first)! * 100), clLast = r1(num(k.f9_rate_last)! * 100);
  const lossRows = [...data.loss_share].sort((a, b) => b.share - a.share);
  const b = data.bridge;
  const bridgeRows = [
    { label: "Cards that closed", sub: "their exit nudged SoW up", v: b.leaver },
    { label: "Cards open both years", sub: "the same cardholders paying differently", v: b.stayer },
    { label: "New cards", sub: "joined at today's lower share", v: b.joiner },
  ];
  const shown = bridgeRows.map((r) => Number(r.v.toFixed(2)));
  const bridgeTotal = shown.reduce((s, v) => s + v, 0);
  // a change per ₹100 is the difference of the two values the strip shows, so the figure, the bars and the row agree
  const stripChange = (m: string) => {
    const row = data.mix.find((x) => x.method === m)!;
    return Number((row.fy26 * 100).toFixed(1)) - Number((row.fy25 * 100).toFixed(1));
  };
  const hsicStripChange = stripChange("HSIC");

  return (
    <>
      <TitleRow
        title="Share of wallet"
        sub={<>HSIC&rsquo;s share of MetroMart spend fell from {sow25}% to {sow26}% in a year, while what each cardholder
          spends at MetroMart stayed flat. Customers did not shop less; they paid another way.</>}
        actions={<>
          <span className="stamp">Pipeline run {data.meta.generated}</span>
          <a className="btn primary" href="#/priorities">Open the priority list</a>
        </>}
      />

      <section className="panel lead" aria-label="Of every ₹100 spent at MetroMart">
        <header>
          <h2>Of every ₹100 spent at MetroMart</h2>
          <span className="meta">Active cards · net of returns</span>
        </header>
        <div className="lead-grid">
          <div className="lead-answer">
            <div className="kpi-label">Paid on the HSIC card, FY26</div>
            <div className="lead-fig">₹{sow26.toFixed(1)}</div>
            <div className="delta"><Bad>{signedRupee(hsicStripChange)}</Bad> from ₹{sow25.toFixed(1)} in FY25</div>
            <div className="rows lead-bridge" aria-label={`The ${pp(bridgeTotal, 2)} change, split`}>
              {bridgeRows.map((r, i) => (
                <div className="row" key={r.label}>
                  <div className="grow">{r.label}<div className="note">{r.sub}</div></div>
                  <span className="fig">{pp(shown[i], 2)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="lead-strip">
            <div className="strip">
              {(["fy25", "fy26"] as const).map((fy) => (
                <div className="strip-row" key={fy}>
                  <span>{fy === "fy25" ? "FY25" : "FY26"}</span>
                  <div className="strip-bar" role="img" aria-label={`${fy.toUpperCase()}: ` + STRIP_ORDER.map((m) =>
                    `${METHOD_NAME[m]} ₹${(data.mix.find((x) => x.method === m)![fy] * 100).toFixed(1)}`).join(", ")}>
                    {STRIP_ORDER.map((m) => {
                      const v = data.mix.find((x) => x.method === m)![fy] * 100;
                      return (
                        <div key={m} className={`strip-seg ${STRIP_CLASS[m]}${v < 12 ? " narrow" : ""}`} style={{ flexBasis: `${v}%` }} title={`${METHOD_NAME[m]}: ₹${v.toFixed(1)} of every ₹100`}>
                          {m === "HSIC" ? <b><span className="wide-label">HSIC </span>₹{v.toFixed(1)}</b> : <span>₹{v.toFixed(1)}</span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="strip-key">
              {STRIP_ORDER.map((m) => <span key={m}><i style={{ background: STRIP_SWATCH[m] }} />{METHOD_NAME[m]}</span>)}
            </div>
            <div className="strip-change" aria-label="Change per ₹100, FY25 to FY26">
              {STRIP_ORDER.map((m) => (
                <div key={m}>
                  <span>{METHOD_NAME[m]}</span>
                  <b className={m === "HSIC" ? "neg" : undefined}>{signedRupee(stripChange(m))}</b>
                </div>
              ))}
            </div>
            <p className="note lead-note">The same cardholders, the same MetroMart basket: {pct(lossRows[0].share, 0)} of the share HSIC lost on cards open both
              years went to Cash/UPI.</p>
          </div>
        </div>
      </section>

      <div className="kpis">
        <Kpi label="HSIC spend per card, May 2026" value={inr(hsicMay)} unit="/month"
          delta={<><Bad>{signedInr(hsicMay - hsicAug)}</Bad> from {inr(hsicAug)} in Aug 2024</>} />
        <Kpi label="MetroMart spend per card, May 2026" value={inr(netMay)} unit="/month"
          delta={<>{signedInr(netMay - netAug)} from {inr(netAug)} in Aug 2024</>} />
        <Kpi label="Closure rate, Apr–Jun 2026" value={`${clLast}%`}
          delta={<><Bad>{pp(clLast - clFirst)}</Bad> from {clFirst}% in Jul–Sep 2024</>} />
        <Kpi label="Spent at MetroMart after closing" value={inrM(num(k.f11_post_close_net))}
          delta={<>by {count(num(k.f11_still_shopping))} cardholders who closed the card</>} />
      </div>

      <div className="grid">
        <Panel span="s8" title="HSIC share of MetroMart spend, by fiscal quarter" meta="Active cards · net of returns">
          <p className="lede">Down about {Math.abs(num(k.f1_slope_pp_per_quarter)!).toFixed(1)} points every quarter, with no quarter of recovery.</p>
          <EChart option={quarterly} height={232} label={`HSIC share of MetroMart spend by quarter, from ${pct(data.sow_quarterly[0].sow)} to ${pct(data.sow_quarterly.at(-1)!.sow)}`} />
        </Panel>
        <Panel span="s4" title="Where the lost share went" meta="Cards open both years">
          <p className="lede">Share of HSIC&rsquo;s {pp(b.stayer)} on cards open throughout.</p>
          <div className="barlist">
            {lossRows.map((r, i) => (
              <div key={r.method} className={i === 0 ? "first" : ""}>
                <div className="lab"><span>{METHOD_NAME[r.method]}</span><b>{pct(r.share)}</b></div>
                <div className="track"><div className="fill" style={{ width: `${(r.share / lossRows[0].share) * 88}%` }} /></div>
              </div>
            ))}
          </div>
          <p className="foot">Why Cash/UPI? Immediacy is a <b>hypothesis</b> (H-imm); the instant-cashback pilot arm tests it.</p>
        </Panel>
      </div>

      <div className="grid">
        <Panel span="s8" title="Spend per active card, by month" meta={
          <span className="legend"><span><i className="line" style={{ background: C.ink }} />At MetroMart, all methods</span>
            <span><i className="line" style={{ background: C.hue }} />On the HSIC card</span></span>}>
          <EChart option={perCard} height={220} label="MetroMart spend per active card stays near ₹1,030 a month while HSIC spend per card halves" />
        </Panel>
        <Panel span="s4" title="What we recommend" meta="Product first">
          <div className="rows">
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Show the reward at the till</b>
              <div className="note">Prime members left {inrM(num(k.f8_prime_ge_left_on_table), 2)} of Grocery and Electronics cashback on the table</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Credit cashback at checkout</b>
              <div className="note">Instead of on next month&rsquo;s statement</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Put the card on UPI</b>
              <div className="note">Cash/UPI took {pct(lossRows[0].share, 0)} of the lost share</div></div></div>
          </div>
          <p className="foot"><a className="card-link" href="#/priorities">All eight offers and who gets them</a></p>
        </Panel>
      </div>
    </>
  );
}

function sowQuarterOption(d: Overview) {
  const q = d.sow_quarterly;
  const last = q.length - 1;
  return base({
    grid: { left: 8, right: 12, top: 26, bottom: 4, containLabel: true },
    tooltip: { ...(base().tooltip as object), valueFormatter: (v: number) => pct(v) },
    xAxis: categoryAxis(q.map((r) => quarterLabel(r.quarter)), { boundaryGap: ["4%", "4%"] }),
    yAxis: valueAxis({ min: 0, max: 0.4, interval: 0.1, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => `${v * 100}%` } }),
    series: [{
      name: "HSIC share", type: "line", data: q.map((r, i) => ({
        value: r.sow,
        label: i === 0 || i === last ? { show: true, position: "top", distance: 8, formatter: () => pct(r.sow), color: C.text, fontSize: 13, fontWeight: 500 } : undefined,
      })),
      lineStyle: { color: C.hue, width: 2 }, itemStyle: { color: C.hue }, symbol: "circle", symbolSize: 6, showSymbol: true,
    }],
  });
}

function perCardOption(d: Overview) {
  const m = d.per_card_monthly;
  return base({
    tooltip: { ...(base().tooltip as object), valueFormatter: (v: number) => inr(v) },
    xAxis: categoryAxis(m.map((r) => monthLabel(r.month)), { axisLabel: { color: C.label, fontSize: 12, margin: 10, interval: 4 } }),
    yAxis: valueAxis({ min: 0, max: 1200, interval: 300, axisLabel: { color: C.label, fontSize: 12, formatter: (v: number) => inr(v) } }),
    series: [
      { name: "At MetroMart, all methods", type: "line", data: m.map((r) => r.net_per_card), lineStyle: { color: C.ink, width: 2 }, itemStyle: { color: C.ink }, showSymbol: false },
      { name: "On the HSIC card", type: "line", data: m.map((r) => r.hsic_per_card), lineStyle: { color: C.hue, width: 2 }, itemStyle: { color: C.hue }, showSymbol: false },
    ],
  });
}
