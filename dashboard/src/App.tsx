import { useEffect, useState } from "react";
import { CardMark } from "./components/ui";
import Story from "./pages/Story";
import Segments from "./pages/Segments";
import Attrition from "./pages/Attrition";
import Priorities from "./pages/Priorities";

const PAGES = [
  { id: "story", label: "Share of wallet", icon: "M3 17l5-5 4 3 7-8M14 7h5v5", Page: Story },
  { id: "segments", label: "Segments", icon: "M4 6h16M4 12h10M4 18h6", Page: Segments },
  { id: "attrition", label: "Attrition & closures", icon: "M12 3v12m0 0l-4-4m4 4l4-4M5 21h14", Page: Attrition },
  { id: "priorities", label: "Priorities & offers", icon: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z", Page: Priorities },
] as const;

const REPO = "https://github.com/Mayank98762/Synchrony-Hackthon-";

function route() {
  const id = location.hash.replace(/^#\/?/, "");
  return PAGES.find((p) => p.id === id) ?? PAGES[0];
}

export default function App() {
  const [page, setPage] = useState(route);
  const [menu, setMenu] = useState(false);

  useEffect(() => {
    const on = () => { setPage(route()); setMenu(false); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  useEffect(() => { document.title = `${page.label} · HSIC Card Insights`; }, [page]);

  const { Page } = page;
  return (
    <div className="app">
      <header className="phone-bar">
        <span className="brand"><CardMark /></span>
        <b>{page.label}</b>
        <button className="btn ghost" aria-expanded={menu} aria-controls="nav" onClick={() => setMenu(true)}>Menu</button>
      </header>

      <nav id="nav" className={`sidebar${menu ? " open" : ""}`} aria-label="Pages">
        <div className="brand">
          <CardMark />
          <div><b>HSIC Card Insights</b><span>MetroMart co-branded card</span></div>
        </div>
        <button className="btn ghost close" onClick={() => setMenu(false)}>Close</button>
        <div className="scope">
          <b>All cardholders</b>
          <span>45,000 customers · Aug 2024 – Jul 2026</span>
        </div>
        <div className="group-label">Portfolio</div>
        {PAGES.map((p) => (
          <a key={p.id} href={`#/${p.id}`} className="nav-item" aria-current={p.id === page.id ? "page" : undefined}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d={p.icon} /></svg>
            {p.label}
          </a>
        ))}
        <div className="bottom">
          <span>Synchrony Analytics Hackathon 2026</span>
          <a href={`${REPO}#readme`} target="_blank" rel="noreferrer">Methods and code</a>
        </div>
      </nav>

      <main className="canvas" id="main">
        <Page />
      </main>
    </div>
  );
}
