import type { ReactNode } from "react";
import type { Label } from "../lib/data";

/** One stroke family for every icon: 24px box, 1.6 stroke, round caps. */
const PATHS = {
  overview: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
  segments: "M4 6h16M4 12h11M4 18h6",
  attrition: "M3 7l6 6 4-4 8 8M15 17h6v-6",
  priorities: "M12 3l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.4 6.8 19.1l1-5.8L3.5 9.2l5.9-.9z",
  flask: "M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3M7.5 15h9",
  code: "M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14",
  bars: "M5 20V10M12 20V4M19 20v-7",
  line: "M3 17l5-5 4 3 8-8",
  arrow: "M5 12h14M13 6l6 6-6 6",
  up: "M7 17L17 7M9 7h8v8",
  down: "M7 7l10 10M17 9v8H9",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6L6 18",
  calendar: "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4",
  db: "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.5v.5",
} as const;
export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" width={size} height={size} aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}

export function Card({ title, sub, actions, className = "", children, id }:
  { title?: string; sub?: ReactNode; actions?: ReactNode; className?: string; children: ReactNode; id?: string }) {
  return (
    <section className={`card ${className}`} aria-label={title} id={id}>
      {(title || actions) && (
        <header className="card-head">
          <div>
            {title && <h2>{title}</h2>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

/** The evidence label every figure carries (PRODUCT.md: Measured / Simulated / Assumed / Hypothesis). */
export function Badge({ label }: { label: Label }) {
  return <span className={`badge ${label.toLowerCase()}`}>{label}</span>;
}

/** A change line under a figure. `good` decides the colour, the arrow follows the sign. */
export function Delta({ dir, good, children }: { dir: "up" | "down"; good: boolean; children: ReactNode }) {
  return (
    <span className={`delta ${good ? "good" : "bad"}`}>
      <Icon name={dir} size={13} />
      {children}
    </span>
  );
}

export function Segmented<T extends string>({ value, options, onChange, label }:
  { value: T; options: { id: T; label: ReactNode; title?: string }[]; onChange: (v: T) => void; label: string }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((o) => (
        <button key={o.id} type="button" aria-pressed={value === o.id} title={o.title}
          aria-label={o.title} onClick={() => onChange(o.id)}>{o.label}</button>
      ))}
    </div>
  );
}

/** A horizontal meter in the reference's style: hatched fill on a pale track, optional marker. */
export function Meter({ value, max = 1, color, marker, label }:
  { value: number; max?: number; color?: string; marker?: number; label: string }) {
  const w = Math.max(0, Math.min(1, value / max)) * 100;
  return (
    <div className="meter" role="meter" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
      <span className="meter-fill" style={{ width: `${w}%`, ...(color ? { backgroundColor: color } : {}) }} />
      {marker != null && <span className="meter-mark" style={{ left: `${(marker / max) * 100}%` }} />}
    </div>
  );
}

export const Swatch = ({ color }: { color: string }) => <span className="swatch" style={{ background: color }} />;
