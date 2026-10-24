import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, CustomChart, LineChart, ScatterChart } from "echarts/charts";
import { GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";

echarts.use([BarChart, CustomChart, LineChart, ScatterChart, GridComponent, MarkAreaComponent, MarkLineComponent,
  TooltipComponent, SVGRenderer]);

export const C = {
  hue: "#2470cc", ink: "#0b0b0b", grey: "#8a909b", pale: "#c4dbf5", grid: "#e9edf2", axis: "#c3cad4",
  label: "#5b6270", text: "#0b0b0b",
};
const FONT = '"Archivo", Inter, system-ui, sans-serif';

/** The app-screen chart rules as a base: 3-5 faint horizontal gridlines, no y-axis line, ticks in grey at 12px,
 *  flat x labels, a plain tooltip box, no animation (motion on app screens is feedback only). */
export function base(extra: EChartsCoreOption = {}): EChartsCoreOption {
  return {
    animation: false,
    textStyle: { fontFamily: FONT, color: C.text },
    grid: { left: 8, right: 12, top: 14, bottom: 4, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#ffffff",
      borderColor: "#e3e8ef",
      borderWidth: 1,
      padding: [6, 10],
      textStyle: { color: C.text, fontSize: 12, fontFamily: FONT },
      extraCssText: "box-shadow:0 4px 12px rgba(0,0,0,.08);border-radius:6px;", // taste-skill-ignore: the tooltip floats
      axisPointer: { type: "line", lineStyle: { color: C.axis, width: 1 } },
    },
    ...extra,
  };
}

export const valueAxis = (o: Record<string, unknown> = {}) => ({
  type: "value",
  splitNumber: 4,
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: C.label, fontSize: 12, margin: 10 },
  splitLine: { lineStyle: { color: C.grid, width: 1 } },
  ...o,
});

export const categoryAxis = (data: string[], o: Record<string, unknown> = {}) => ({
  type: "category",
  data,
  boundaryGap: false,
  axisLine: { lineStyle: { color: C.axis, width: 1 } },
  axisTick: { show: false },
  axisLabel: { color: C.label, fontSize: 12, margin: 10, hideOverlap: true },
  ...o,
});

export function EChart({ option, height, label }: { option: EChartsCoreOption; height: number; label: string }) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!el.current) return;
    chart.current = echarts.init(el.current, undefined, { renderer: "svg" });
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(el.current);
    // lay labels out again once Archivo has loaded, so measured text widths are the real ones
    document.fonts?.ready.then(() => chart.current?.resize());
    return () => { ro.disconnect(); chart.current?.dispose(); chart.current = null; };
  }, []);

  useEffect(() => { chart.current?.setOption(option, true); }, [option]);

  return <div ref={el} className="chart" style={{ height }} role="img" aria-label={label} />;
}
