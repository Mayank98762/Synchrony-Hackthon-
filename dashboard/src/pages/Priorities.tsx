import { useState } from "react";
import { usePageData, num, type Priority } from "../lib/data";
import { count, inr, inrM, pct } from "../lib/format";
import { PageState, Panel, TitleRow } from "../components/ui";

const LEVER: Record<string, string> = {
  A: "Win-back (O6)", B: "Onboarding protection (O7) + reward visibility (O3)", C: "Activation milestone + Prime trial (O7)",
  D: "Threshold bonus (O8) + reward visibility (O3)", E: "Product fixes only (O1–O5), no paid incentive",
};
const WHO: Record<string, string> = { B: "Young card, high frequency", C: "Young card, low/mid frequency", D: "Mature card, high frequency", E: "Mature card, low/mid frequency", A: "Card closed, still shopping" };

interface SimBox { id: string; name: string; customers: number; sow: number; offCard: number }

export default function Priorities() {
  const { data, error } = usePageData<Priority>("priority");
  const [sel, setSel] = useState("B");
  const [shift, setShift] = useState(5);
  if (!data) return <PageState title="Priorities & offers" error={error} />;

  const now = Object.fromEntries(data.sizes.map((s) => [s.segment, s.customers_at_score]));
  const box = Object.fromEntries(data.boxes.map((b) => [b.segment, b]));
  const a = data.segment_a;
  const sim: Record<string, SimBox> = {
    ...Object.fromEntries(data.boxes.map((b) => [b.segment, { id: b.segment, name: b.name, customers: now[b.segment], sow: b.sow, offCard: b.nonhsic_per_cust }])),
    A: { id: "A", name: "Closed, still shopping", customers: num(a.seg_A_n_score)!, sow: 0, offCard: num(a.seg_A_horizon_net_per_cust)! },
  };
  const s = sim[sel];
  const x = shift / 100;
  const moved = x * s.offCard * s.customers;
  const sowAfter = s.sow + x * (1 - s.sow);
  // the same assumed shift applied to every box, largest ₹ first: where an offer has the most spend to win
  const compare = Object.values(sim).map((b) => ({ ...b, moved: x * b.offCard * b.customers })).sort((p, q) => q.moved - p.moved);
  const maxMoved = compare[0].moved;
  const ax = data.axes;
  const econ = data.economics;

  const Cell = ({ id, area }: { id: "B" | "C" | "D" | "E"; area: string }) => {
    const b = box[id];
    return (
      <button className="box" style={{ gridArea: area }} aria-pressed={sel === id} onClick={() => setSel(id)}>
        <span className="name">{id} · {b.name}</span>
        {id === "B" && <span className="pill" style={{ justifySelf: "start" }}>Highest priority</span>}
        <span className="count">{count(now[id])} customers</span>
        <dl>
          <dt>6-month closure</dt><dd>{pct(b.closure_6m)}</dd>
          <dt>Off-card spend</dt><dd>{inr(b.nonhsic_per_cust)}</dd>
          <dt>FY26 SoW</dt><dd>{pct(b.sow)}</dd>
        </dl>
      </button>
    );
  };

  return (
    <>
      <TitleRow
        title="Priorities & offers"
        sub={<>SoW is within {num(ax.seg_sow_max_gap_pp)!.toFixed(1)} points in every box, so low SoW is the whole book.
          We prioritise by closure risk (card age) and value (purchase frequency). Select a box to size an offer for it.</>}
      />

      <div className="grid">
        <Panel span="s8" title="Who to prioritise" meta="Customers on 31 Jul 2026 · outcomes Feb–Jul 2026">
          <div className="matrix">
            <span className="axis" style={{ gridArea: "mh" }}>Mature card, 12 months +</span>
            <span className="axis" style={{ gridArea: "yh" }}>Young card, under 12 months</span>
            <span className="axis" style={{ gridArea: "oh" }}>Outside the grid</span>
            <span className="axis row" style={{ gridArea: "hf" }}>High purchase frequency</span>
            <span className="axis row" style={{ gridArea: "lf" }}>Low/mid purchase frequency</span>
            <Cell id="D" area="d" /><Cell id="B" area="b" /><Cell id="E" area="e" /><Cell id="C" area="c" />
            <button className="box outside" style={{ gridArea: "a" }} aria-pressed={sel === "A"} onClick={() => setSel("A")}>
              <span className="name">A · Closed, still shopping</span>
              <span className="count">{count(num(a.seg_A_n_score))} customers</span>
              <dl>
                <dt>Spent after closing</dt><dd>{inrM(num(a.seg_A_post_close_net))}</dd>
                <dt>Off-card spend</dt><dd>{inr(num(a.seg_A_horizon_net_per_cust))}</dd>
                <dt>HSIC SoW</dt><dd>0.0%</dd>
              </dl>
              <span className="note" style={{ marginTop: 8 }}>The most literal low-SoW group: HSIC gets none of their MetroMart spend.</span>
            </button>
          </div>
          <p className="foot">Young cards close {(num(ax.seg_age_closure_diff)! * 100).toFixed(1)} points more often; high-frequency customers spend {inr(num(ax.seg_freq_nonhsic_diff))} more off the card.
            B outranks C on value at the same risk. Off-card spend is per customer, Feb–Jul 2026.</p>
        </Panel>

        <Panel span="s4" title={`Size an offer for ${s.id} · ${s.name}`} meta={<span className="pill">Simulated</span>}>
          <p className="lede" style={{ marginTop: 0 }}>{WHO[s.id]}. Lever: {LEVER[s.id]}.</p>
          <label htmlFor="shift" style={{ display: "flex", justifyContent: "space-between", fontWeight: 500 }}>
            <span>Off-card spend moved to HSIC</span><span className="num">{shift}%</span>
          </label>
          <input id="shift" className="range" type="range" min={0} max={20} step={1} value={shift} onChange={(e) => setShift(Number(e.target.value))} />
          <div className="sim-out">
            <div><span className="muted">Spend moved to HSIC, 6 months</span><div className="v">{inrM(moved, 2)}</div></div>
            <div><span className="muted">The box&rsquo;s SoW</span><div className="v">{pct(s.sow)} → {pct(sowAfter)}</div></div>
          </div>
          <h3 className="sim-h">The same {shift}% shift in every box</h3>
          <div className="compare">
            {compare.map((c) => (
              <div key={c.id} className={c.id === sel ? "on" : ""}>
                <span>{c.id} · {c.name}</span>
                <b>{inrM(c.moved, 2)}</b>
                <i style={{ width: `${maxMoved ? (c.moved / maxMoved) * 100 : 0}%` }} />
              </div>
            ))}
          </div>
          <p className="foot">The shift is an assumption, not a forecast. Margins and break-even come from the economics module; the pilot measures the real shift.</p>
        </Panel>
      </div>

      <div className="grid">
        <Panel span="s8" title="Offers, in priority order" meta={Object.keys(econ).length ? "Break-even per offer" : "Break-even: waiting on the economics module"}>
          <div className="table-wrap">
            <table className="offers">
              <thead><tr><th>Offer</th><th>Who</th><th>Tests</th><th className="n">Break-even shift</th></tr></thead>
              <tbody>
                {data.offers.map((o, i) => {
                  const be = econ[`${o.id.toLowerCase()}_breakeven_base`];
                  return (
                    <tr key={o.id}>
                      <td style={{ maxWidth: 360 }}><b style={{ fontWeight: i === 0 ? 600 : 500 }}>{o.id} · {o.name}</b>
                        <span className="sub">{i === 0 ? "Lead offer. " : ""}{o.what}</span></td>
                      <td>{o.layer}<span className="sub">{o.who}</span></td>
                      <td>{o.tests ? <span className="pill">{o.tests}</span> : <span className="muted">{"—"}</span>}</td>
                      <td className="n" data-label="Break-even shift">{be ? (typeof be.value === "number" ? pct(be.value) : String(be.value)) : <span className="muted">{"—"}</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
        <Panel span="s4" title="How the pilot proves it" meta="Randomised holdout">
          <div className="rows">
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>10% holdout per offer and box</b>
              <div className="note">Turns simulated shifts into measured ones</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>O3 tests H-aware, O1 tests H-imm</b>
              <div className="note">Do Prime members notice their rates? Does instant payoff win back Cash/UPI spend?</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Read out after 3 months</b>
              <div className="note">SoW, active rate, closure rate and net value per arm</div></div></div>
            <div className="row"><div className="grow"><b style={{ fontWeight: 500 }}>Scale only on evidence</b>
              <div className="note">When the lift&rsquo;s CI excludes zero and net value is positive; a null result is reported</div></div></div>
          </div>
        </Panel>
      </div>
    </>
  );
}
