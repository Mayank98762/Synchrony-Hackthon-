import { useEffect, useState } from "react";
import logo from "../synchrony_logo.jpg";
import { Badge, Icon, type IconName } from "./components/ui";
import { meta } from "./lib/data";
import { dateLabel } from "./lib/format";
import Overview from "./pages/Overview";
import Segments from "./pages/Segments";
import Attrition from "./pages/Attrition";
import Priorities from "./pages/Priorities";

const PAGES: { id: string; label: string; title: string; sub: string; icon: IconName; Page: () => JSX.Element }[] = [
  { id: "overview", label: "Overview", title: "Share of wallet", icon: "overview", Page: Overview,
    sub: "Why HSIC's share of MetroMart spend fell, and where it went" },
  { id: "segments", label: "Segments", title: "Segments", icon: "segments", Page: Segments,
    sub: "We tested whether customers differ before segmenting them" },
  { id: "attrition", label: "Attrition & closures", title: "Attrition & closures", icon: "attrition", Page: Attrition,
    sub: "Silent attrition against the portfolio trend, and who closes the card" },
  { id: "priorities", label: "Priorities & offers", title: "Priorities & offers", icon: "priorities", Page: Priorities,
    sub: "Who to protect first, and offers that fire at the moment of payment" },
];
const REPO = "https://github.com/Mayank98762/Synchrony-Hackthon-";

function route() {
  const id = location.hash.replace(/^#\/?/, "").split("/")[0];
  return PAGES.find((p) => p.id === id) ?? PAGES[0];
}

/** "#/overview/tests" scrolls to the card with id "tests" once the page has rendered; otherwise to the top. */
function toAnchor() {
  const sub = location.hash.split("/")[2];
  requestAnimationFrame(() => {
    const el = sub ? document.getElementById(sub) : null;
    if (el) el.scrollIntoView({ block: "start" });
    else window.scrollTo(0, 0);
  });
}

const [from, to] = meta.data_window.split(" to ");
const WINDOW = `${dateLabel(from).replace(/^\d+ /, "")} – ${dateLabel(to).replace(/^\d+ /, "")}`;

export default function App() {
  const [page, setPage] = useState(route);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const on = () => { setPage(route()); setMenu(false); toAnchor(); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  useEffect(() => { toAnchor(); }, []);
  useEffect(() => { document.title = `${page.title} · HSIC Card Insights`; }, [page]);
  useEffect(() => {
    if (!menu) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setMenu(false);
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [menu]);

  const { Page } = page;
  return (
    <div className="app">
      <a className="skip" href="#main">Skip to content</a>

      <aside className={`sidebar${menu ? " open" : ""}`} id="nav" aria-label="Pages">
        <div className="brand">
          <img src={logo} alt="Synchrony" width={164} height={45} />
          <button type="button" className="icon-btn close" aria-label="Close menu" onClick={() => setMenu(false)}>
            <Icon name="close" />
          </button>
        </div>
        <div className="product">
          <b>HSIC Card Insights</b>
          <span>MetroMart co-branded card</span>
        </div>
        <nav className="nav">
          {PAGES.map((p) => (
            <a key={p.id} href={`#/${p.id}`} className="nav-item" aria-current={p.id === page.id ? "page" : undefined}>
              <Icon name={p.icon} />
              {p.label}
            </a>
          ))}
        </nav>
        <hr />
        <nav className="nav">
          <a className="nav-item" href="#/overview/tests"><Icon name="flask" />Hypotheses tested</a>
          <a className="nav-item" href={`${REPO}#readme`} target="_blank" rel="noreferrer"><Icon name="code" />Methods and code</a>
        </nav>

        <div className="legend-card">
          <div className="legend-icon"><Icon name="info" /></div>
          <b>Every figure is labelled</b>
          <dl>
            <div><dt><Badge label="Measured" /></dt><dd>from the case data</dd></div>
            <div><dt><Badge label="Simulated" /></dt><dd>a modelled outcome</dd></div>
            <div><dt><Badge label="Assumed" /></dt><dd>an input we chose</dd></div>
            <div><dt><Badge label="Hypothesis" /></dt><dd>a why we can&rsquo;t test</dd></div>
          </dl>
          <a className="btn dark" href={`${REPO}#readme`} target="_blank" rel="noreferrer">Read the method</a>
        </div>
        <p className="foot">Synchrony Analytics Hackathon 2026</p>
      </aside>
      {menu && <div className="scrim" onClick={() => setMenu(false)} aria-hidden="true" />}

      <div className="main">
        <header className="topbar">
          <button type="button" className="icon-btn menu" aria-label="Open menu" aria-expanded={menu} aria-controls="nav"
            onClick={() => setMenu(true)}><Icon name="menu" /></button>
          <img className="topbar-logo" src={logo} alt="Synchrony" width={120} height={33} />
          <div className="page-title">
            <h1>{page.title}</h1>
            <p>{page.sub}</p>
          </div>
          <div className="chips">
            <span className="chip"><Icon name="calendar" size={16} />{WINDOW}</span>
            <span className="chip"><Icon name="db" size={16} />{meta.customers.toLocaleString("en-IN")} customers</span>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <Page />
        </main>
        <footer className="page-foot">
          Generated by <code>run_all.py</code> on {meta.generated}. HSIC Bank and MetroMart are fictional case brands.
        </footer>
      </div>
    </div>
  );
}
