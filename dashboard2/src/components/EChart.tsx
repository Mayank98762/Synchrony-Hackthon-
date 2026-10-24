import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, LineChart, ScatterChart } from "echarts/charts";
import { GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent, AriaComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";

echarts.use([BarChart, LineChart, ScatterChart, GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent,
  AriaComponent, SVGRenderer]);

/** Chart tokens. The categorical slots are fixed per payment method and were run through the dataviz
 *  validator (lightness band, chroma, CVD and normal-vision separation all pass on the white card). */
export const C = {
  green: "#4e8a1c", lime: "#9ccd5a", limeSoft: "#cfe6a6", yellow: "#d9a400", rust: "#c8562a", violet: "#8a6bb0",
  ink: "#17181b", label: "#62656b", ghost: "#ebebe8", ghostHi: "#dededa", grid: "#efefec", axis: "#d6d6d2",
};
export const METHOD: Record<string, string> = {
  HSIC: C.green, "Cash/UPI": C.rust, Wallet: C.yellow, Debit: C.lime, "Other CC": C.violet,
};
const FONT = '"Manrope", system-ui, sans-serif';

/** The reference's highlighted bar: lime with fine diagonal hatching. */
export const hatch = (color = C.lime) => ({
  color,
  decal: { symbol: "rect", symbolSize: 1, color: "rgba(255,255,255,0.35)", dashArrayX: [1, 0], dashArrayY: [2, 5], rotation: -Math.PI / 4 },
});

export function base(extra: EChartsCoreOption = {}): EChartsCoreOption {
  return {
    animationDuration: 500,
    animationEasing: "cubicOut",
    textStyle: { fontFamily: FONT, color: C.ink },
    grid: { left: 4, right: 8, top: 16, bottom: 4, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#ffffff",
      borderColor: "#ececea",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: C.ink, fontSize: 12, fontFamily: FONT },
      extraCssText: "box-shadow:0 8px 24px rgba(20,20,20,.10);border-radius:10px;",
      axisPointer: { type: "shadow", shadowStyle: { color: "rgba(0,0,0,0.03)" } },
    },
    ...extra,
  };
}

export const valueAxis = (o: Record<string, unknown> = {}) => ({
  type: "value",
  splitNumber: 4,
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: C.label, fontSize: 11, margin: 10 },
  splitLine: { lineStyle: { color: C.grid, width: 1 } },
  ...o,
});

export const categoryAxis = (data: (string | number)[], o: Record<string, unknown> = {}) => ({
  type: "category",
  data,
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: C.label, fontSize: 11, margin: 12, hideOverlap: true },
  ...o,
});

/** A tooltip row: swatch + label + value, all in text ink. */
export const tipRow = (color: string, label: string, value: string) =>
  `<div style="display:flex;align-items:center;gap:8px;min-width:150px"><span style="width:8px;height:8px;border-radius:2px;background:${color}"></span><span style="color:${C.label}">${label}</span><b style="margin-left:auto;font-variant-numeric:tabular-nums">${value}</b></div>`;

export function EChart({ option, height, label }: { option: EChartsCoreOption; height: number; label: string }) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!el.current) return;
    chart.current = echarts.init(el.current, undefined, { renderer: "svg" });
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(el.current);
    // lay labels out again once the web font has loaded, so measured text widths are the real ones
    document.fonts?.ready.then(() => chart.current?.resize());
    return () => { ro.disconnect(); chart.current?.dispose(); chart.current = null; };
  }, []);

  useEffect(() => {
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    chart.current?.setOption({ ...option, ...(reduce ? { animation: false } : {}) }, true);
  }, [option]);

  return <div ref={el} className="chart" style={{ height }} role="img" aria-label={label} />;
}
