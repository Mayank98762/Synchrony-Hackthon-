import type { ReactNode } from "react";

/** The product's mark: the co-branded card itself, in the one hue. */
export function CardMark() {
  return (
    <svg viewBox="0 0 28 28" aria-hidden="true">
      <rect x="1.5" y="5.5" width="25" height="17" rx="3" fill="#2470cc" />
      <rect x="1.5" y="9.5" width="25" height="3" fill="#ffffff" />
      <rect x="5" y="16" width="7" height="2.5" rx="1" fill="#ffffff" opacity="0.85" />
    </svg>
  );
}

export function TitleRow({ title, sub, actions }: { title: string; sub: ReactNode; actions?: ReactNode }) {
  return (
    <div className="title-row">
      <div>
        <h1>{title}</h1>
        <p className="sub">{sub}</p>
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}

export function Panel({ title, meta, span, children, className = "" }:
  { title: string; meta?: ReactNode; span: string; children: ReactNode; className?: string }) {
  return (
    <section className={`panel ${span} ${className}`} aria-label={title}>
      <header>
        <h2>{title}</h2>
        {meta && <span className="meta">{meta}</span>}
      </header>
      {children}
    </section>
  );
}

export function Kpi({ label, value, unit, delta, lead }:
  { label: string; value: string; unit?: string; delta?: ReactNode; lead?: boolean }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value${lead ? " lead" : ""}`}>{value}{unit && <small>{unit}</small>}</div>
      {delta && <div className="delta">{delta}</div>}
    </div>
  );
}

/** Loading keeps the final layout: flat grey bars at the real sizes, no shimmer. Errors stay inside the canvas. */
export function PageState({ title, error }: { title: string; error: string | null }) {
  if (error) {
    return (
      <>
        <TitleRow title={title} sub="The data for this page did not load." />
        <div className="panel error" role="alert">
          <p><b>Couldn&rsquo;t load the page data</b> ({error}). Run <code>python analysis/run_all.py</code> to rebuild
            <code> dashboard/public/data/</code>, then reload.</p>
          <p style={{ marginTop: 12 }}><button className="btn" onClick={() => location.reload()}>Retry</button></p>
        </div>
      </>
    );
  }
  return (
    <div aria-busy="true">
      <div className="title-row"><div><div className="skeleton" style={{ width: 220, height: 29 }} />
        <div className="skeleton" style={{ width: 520, height: 18, marginTop: 8 }} /></div></div>
      <div className="kpis">{[0, 1, 2, 3].map((i) => (
        <div className="kpi" key={i}><div className="skeleton" style={{ width: 140, height: 16 }} />
          <div className="skeleton" style={{ width: 90, height: 28, marginTop: 8 }} /></div>))}</div>
      <div className="grid"><div className="panel s8"><div className="skeleton" style={{ height: 300 }} /></div>
        <div className="panel s4"><div className="skeleton" style={{ height: 300 }} /></div></div>
    </div>
  );
}

export const Bad = ({ children }: { children: ReactNode }) => <span className="bad">{children}</span>;
