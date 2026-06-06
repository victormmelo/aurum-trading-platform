"use client";

import { useEffect, useRef } from "react";
import {
  LineSeries,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { BacktestEquityPoint, BacktestTrade } from "@/lib/api";

export function BacktestEquityChart({
  points,
  trades,
}: {
  points: BacktestEquityPoint[];
  trades: BacktestTrade[];
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || points.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      height: 360,
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

    const lineSeries = chart.addSeries(LineSeries, {
      color: "#107e59",
      lineWidth: 2,
    });

    const lineData = points
      .map((ep) => ({
        time: toUtcSeconds(ep.timestamp),
        value: Number(ep.equity),
      }))
      .filter((d) => Number.isFinite(d.value));

    lineSeries.setData(lineData);

    const markers = trades.flatMap((t) => [
      {
        time: toUtcSeconds(t.entry_time),
        position: "belowBar" as const,
        color: "#107e59",
        shape: "arrowUp" as const,
        text: "C",
      },
      {
        time: toUtcSeconds(t.exit_time),
        position: "aboveBar" as const,
        color: "#dc2626",
        shape: "arrowDown" as const,
        text: "V",
      },
    ]);
    createSeriesMarkers(lineSeries, markers);

    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [points, trades]);

  if (points.length === 0) {
    return (
      <div className="grid min-h-[280px] place-items-center rounded-lg border border-dashed border-border bg-muted p-6 text-center text-sm text-muted-foreground">
        Nenhum ponto de equity disponível.
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-[360px] min-w-0 overflow-hidden rounded-lg border border-border bg-background"
      aria-label="Curva de equity do backtest"
    />
  );
}

function toUtcSeconds(value: string): UTCTimestamp {
  return Math.floor(new Date(value).getTime() / 1000) as UTCTimestamp;
}
