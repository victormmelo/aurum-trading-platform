"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CandlestickSeries,
  createChart,
  HistogramSeries,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { MarketCandle } from "@/lib/api";

export function MarketHistoryChart({
  candles,
}: {
  candles: MarketCandle[];
  interval: MarketCandle["interval"];
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [activeCandle, setActiveCandle] = useState<MarketCandle | null>(null);
  const seriesData = useMemo(() => toSeriesData(candles), [candles]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || candles.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      height: 420,
      layout: {
        background: { color: "#ffffff" },
        textColor: "#334155",
        fontFamily: "Poppins, sans-serif",
      },
      grid: {
        horzLines: { color: "#eef2f7" },
        vertLines: { color: "#eef2f7" },
      },
      rightPriceScale: {
        borderColor: "#e5e7eb",
        scaleMargins: { top: 0.08, bottom: 0.28 },
      },
      timeScale: {
        borderColor: "#e5e7eb",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 0,
      },
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#107e59",
      downColor: "#dc2626",
      borderUpColor: "#107e59",
      borderDownColor: "#dc2626",
      wickUpColor: "#107e59",
      wickDownColor: "#dc2626",
    });
    candleSeries.setData(seriesData.candles);

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#64748b",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.78, bottom: 0 },
      borderVisible: false,
    });
    volumeSeries.setData(seriesData.volume);
    chart.timeScale().fitContent();

    chart.subscribeCrosshairMove((param) => {
      if (!param.time) {
        setActiveCandle(null);
        return;
      }
      const hovered = candles.find((candle) => toUtcSeconds(candle.open_time) === param.time);
      setActiveCandle(hovered ?? null);
    });

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [candles, seriesData]);

  if (candles.length === 0) {
    return (
      <div className="grid min-h-[320px] place-items-center rounded-lg border border-dashed border-border bg-muted p-6 text-center text-sm leading-6 text-muted-foreground">
        Nenhum candle histórico foi encontrado para o intervalo selecionado.
      </div>
    );
  }

  const detail = activeCandle ?? candles[candles.length - 1];

  return (
    <div className="grid gap-3">
      <div
        ref={containerRef}
        className="h-[420px] min-w-0 overflow-hidden rounded-lg border border-border bg-background"
        aria-label="Grafico candlestick historico BTCUSDT"
      />
      <div className="grid gap-2 rounded-lg border border-border bg-muted px-4 py-3 text-xs leading-5 text-muted-foreground md:grid-cols-6">
        <ChartFact label="Abertura" value={formatMoney(detail.open_price)} />
        <ChartFact label="Máxima" value={formatMoney(detail.high_price)} />
        <ChartFact label="Mínima" value={formatMoney(detail.low_price)} />
        <ChartFact label="Fechamento" value={formatMoney(detail.close_price)} />
        <ChartFact label="Volume" value={formatNumber(detail.volume)} />
        <ChartFact label="Janela" value={formatDateTime(detail.open_time)} />
      </div>
    </div>
  );
}

function ChartFact({ label, value }: { label: string; value: string }) {
  return (
    <span className="min-w-0">
      <span className="block font-medium text-muted-foreground">{label}</span>
      <strong className="block break-words font-semibold text-foreground">{value}</strong>
    </span>
  );
}

function toSeriesData(candles: MarketCandle[]) {
  const candleData: CandlestickData[] = [];
  const volumeData: HistogramData[] = [];

  for (const candle of candles) {
    const time = toUtcSeconds(candle.open_time);
    const open = Number(candle.open_price);
    const high = Number(candle.high_price);
    const low = Number(candle.low_price);
    const close = Number(candle.close_price);
    const volume = Number(candle.volume);

    if (![open, high, low, close, volume].every(Number.isFinite)) continue;

    candleData.push({ time, open, high, low, close });
    volumeData.push({
      time,
      value: volume,
      color: close >= open ? "rgba(16, 126, 89, 0.35)" : "rgba(220, 38, 38, 0.28)",
    });
  }

  return { candles: candleData, volume: volumeData };
}

function toUtcSeconds(value: string): UTCTimestamp {
  return Math.floor(new Date(value).getTime() / 1000) as UTCTimestamp;
}

function formatMoney(value: string | null | undefined, currency = "USDT") {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value} ${currency}`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 2 })} ${currency}`;
}

function formatNumber(value: string | null | undefined) {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  return number.toLocaleString("en-US", { maximumFractionDigits: 4 });
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo",
  }).format(date);
}
