"use client";

import { useEffect, useMemo, useState } from "react";
import { Database, LineChart, Radio } from "lucide-react";

import {
  CompactList,
  InfoRow,
  MetricCard,
  MetricCardGroup,
  Panel,
  PanelHeader,
  StatPill,
  StatusPill,
} from "@/components/ui";
import type { MarketSummary } from "@/lib/api";

type ConnectionState = "connecting" | "live" | "fallback";

export function LiveMarketCards({ initial }: { initial: MarketSummary }) {
  const { market, connection } = useLiveMarket(initial);

  return (
    <MetricCardGroup aria-label="Indicadores de mercado">
      <MetricCard
        label="Último preço"
        value={formatMoney(market.snapshot?.last_price, "USDT")}
        detail={`Atualizado ${formatDateTime(market.snapshot?.captured_at)}`}
        tone={market.snapshot ? "positive" : "neutral"}
      />
      <MetricCard
        label="Variação 24h"
        value={percentLabel(market.snapshot?.price_change_pct_24h)}
        detail={connectionLabel(connection)}
        tone={marketChangeTone(market.snapshot?.price_change_pct_24h)}
      />
      <MetricCard
        label="Volume 24h"
        value={formatNumber(market.snapshot?.volume_24h)}
        detail={market.symbol}
        tone="neutral"
      />
      <MetricCard
        label="Volatilidade"
        value={percentLabel(market.snapshot?.volatility_pct)}
        detail="Indicador operacional"
        tone="warning"
      />
    </MetricCardGroup>
  );
}

export function LiveMarketPanel({ initial }: { initial: MarketSummary }) {
  const { market, connection } = useLiveMarket(initial);
  const snapshot = market.snapshot;

  return (
    <div className="grid gap-4">
      <div className="flex justify-end">
        <LiveBadge connection={connection} capturedAt={snapshot?.captured_at ?? null} />
      </div>
      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Tendências" title="1h / 4h / 1d" icon={<LineChart />} />
          <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
            <StatPill label="1h" value={snapshot?.trend_1h ?? "sem dado"} />
            <StatPill label="4h" value={snapshot?.trend_4h ?? "sem dado"} />
            <StatPill label="1d" value={snapshot?.trend_1d ?? "sem dado"} />
          </div>
        </Panel>
        <Panel>
          <PanelHeader eyebrow="Faixa 24h" title="Preço e spread" icon={<LineChart />} />
          <CompactList>
            <InfoRow label="Máxima" value={formatMoney(snapshot?.high_price_24h)} />
            <InfoRow label="Mínima" value={formatMoney(snapshot?.low_price_24h)} />
            <InfoRow label="Spread" value={snapshot?.spread_bps == null ? "-" : `${snapshot.spread_bps} bps`} />
          </CompactList>
        </Panel>
      </section>
    </div>
  );
}

export function LiveMarketDashboardPanel({ initial }: { initial: MarketSummary }) {
  const { market, connection } = useLiveMarket(initial);
  const snapshot = market.snapshot;
  const marketPrice = formatMoney(snapshot?.last_price, "USDT");

  return (
    <Panel>
      <PanelHeader eyebrow="Mercado" title={`${market.symbol} operacional`} icon={<LineChart />} />
      <div className="grid gap-5" aria-label="Indicadores de mercado">
        <div className="flex items-start justify-between gap-5 max-md:flex-col">
          <div className="min-w-0">
            <span className="text-sm font-medium leading-5 text-muted-foreground">Último preço</span>
            <strong className="mt-2 block break-words text-3xl font-semibold leading-tight tracking-tight md:text-4xl">
              {marketPrice === "-" ? "Sem preço" : marketPrice}
            </strong>
            <p className="m-0 mt-3 max-w-[520px] text-sm leading-6 text-muted-foreground">
              Snapshot de mercado capturado em {formatDateTime(snapshot?.captured_at)}.
            </p>
          </div>
          <LiveBadge connection={connection} capturedAt={snapshot?.captured_at ?? null} />
        </div>
        <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
          <InfoRow label="Máxima 24h" value={formatMoney(snapshot?.high_price_24h)} />
          <InfoRow label="Mínima 24h" value={formatMoney(snapshot?.low_price_24h)} />
          <InfoRow label="Volume 24h" value={formatNumber(snapshot?.volume_24h)} />
          <InfoRow label="Spread" value={snapshot?.spread_bps == null ? "-" : `${snapshot.spread_bps} bps`} />
          <InfoRow label="Volatilidade" value={percentLabel(snapshot?.volatility_pct)} />
          <InfoRow label="Origem" value={sourceLabel(snapshot?.source_payload)} />
        </div>
        <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <StatPill label="Tendência 1h" value={snapshot?.trend_1h ?? "sem dado"} />
          <StatPill label="Tendência 4h" value={snapshot?.trend_4h ?? "sem dado"} />
          <StatPill label="Tendência 1d" value={snapshot?.trend_1d ?? "sem dado"} />
        </div>
      </div>
    </Panel>
  );
}

function useLiveMarket(initial: MarketSummary) {
  const [market, setMarket] = useState(initial);
  const [connection, setConnection] = useState<ConnectionState>("connecting");

  useEffect(() => {
    let closed = false;
    let pollId: ReturnType<typeof setInterval> | null = null;
    const events = new EventSource("/api/market/stream");

    async function poll() {
      try {
        const response = await fetch("/api/market/summary", { cache: "no-store" });
        if (!response.ok) return;
        setMarket((await response.json()) as MarketSummary);
      } catch {
        // Keep the last good snapshot visible while the connection recovers.
      }
    }

    function startFallback() {
      if (closed) return;
      setConnection("fallback");
      if (pollId === null) {
        poll();
        pollId = setInterval(poll, 10000);
      }
    }

    events.addEventListener("snapshot", (event) => {
      setConnection("live");
      setMarket(JSON.parse((event as MessageEvent).data) as MarketSummary);
      if (pollId !== null) {
        clearInterval(pollId);
        pollId = null;
      }
    });
    events.addEventListener("heartbeat", () => setConnection("live"));
    events.onerror = startFallback;

    return () => {
      closed = true;
      events.close();
      if (pollId !== null) clearInterval(pollId);
    };
  }, []);

  return useMemo(() => ({ market, connection }), [market, connection]);
}

function LiveBadge({ connection, capturedAt }: { connection: ConnectionState; capturedAt: string | null }) {
  return (
    <StatusPill tone={connection === "live" ? "positive" : "warning"}>
      {connection === "live" ? <Radio size={16} aria-hidden="true" /> : <Database size={16} aria-hidden="true" />}
      {connectionLabel(connection)} · {formatDateTime(capturedAt)}
    </StatusPill>
  );
}

function connectionLabel(value: ConnectionState) {
  if (value === "live") return "ao vivo";
  if (value === "fallback") return "reconectando";
  return "conectando";
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

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${Number(value).toLocaleString("en-US", { maximumFractionDigits: 4 })}%`;
}

function marketChangeTone(value: string | null | undefined): "positive" | "warning" | "neutral" {
  const parsed = value == null ? Number.NaN : Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return "neutral";
  return parsed > 0 ? "positive" : "warning";
}

function sourceLabel(source: Record<string, unknown> | undefined) {
  if (!source) return "sem dado";
  const value = source.source;
  return typeof value === "string" ? value.replaceAll("_", " ") : "persistido";
}
