"use client";

import { useEffect, useRef } from "react";
import {
  LineSeries,
  createChart,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { BacktestCompareItem } from "@/lib/api";

const SERIES_COLORS = ["#107e59", "#2563eb", "#dc2626", "#d97706", "#7c3aed"];

export function BacktestCompareChart({ runs }: { runs: BacktestCompareItem[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || runs.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      height: 400,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#334155",
        fontFamily: "Poppins, sans-serif",
      },
      grid: {
        horzLines: { color: "#eef2f7" },
        vertLines: { color: "#eef2f7" },
      },
      rightPriceScale: { borderColor: "#e5e7eb" },
      timeScale: {
        borderColor: "#e5e7eb",
        timeVisible: true,
        secondsVisible: false,
      },
    });
    chartRef.current = chart;

    for (const [i, run] of runs.entries()) {
      const color = SERIES_COLORS[i % SERIES_COLORS.length];
      const series = chart.addSeries(LineSeries, { color, lineWidth: 2 });
      const data = run.equity_points
        .map((ep) => ({
          time: toUtcSeconds(ep.timestamp),
          value: Number(ep.equity),
        }))
        .filter((d) => Number.isFinite(d.value));
      series.setData(data);
    }

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [runs]);

  if (runs.every((r) => r.equity_points.length === 0)) {
    return (
      <div className="grid min-h-[280px] place-items-center rounded-lg border border-dashed border-border bg-muted p-6 text-center text-sm text-muted-foreground">
        Selecione simulações para comparar.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      <div
        ref={containerRef}
        className="h-[400px] min-w-0 overflow-hidden rounded-lg border border-border bg-background"
        aria-label="Curvas de equity comparativas"
      />
      <div className="flex flex-wrap gap-4">
        {runs.map((run, i) => (
          <div key={run.id} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span
              className="inline-block size-3 rounded-sm"
              style={{ backgroundColor: SERIES_COLORS[i % SERIES_COLORS.length] }}
            />
            {run.name}
          </div>
        ))}
      </div>
    </div>
  );
}

function toUtcSeconds(value: string): UTCTimestamp {
  return Math.floor(new Date(value).getTime() / 1000) as UTCTimestamp;
}
