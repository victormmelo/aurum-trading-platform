import { AlertTriangle, Database, LineChart } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { CompactList, InfoRow, MetricCard, Notice, PageHeader, Panel, PanelHeader, StatPill, StatusPill } from "@/components/ui";
import { fetchApi, formatDateTime, formatMoney, type MarketSummary } from "@/lib/api";

export default async function MarketPage() {
  const result = await fetchApi<MarketSummary>("/market/summary");
  const market = result.ok ? result.data.snapshot : null;
  const environment = result.ok ? result.data.environment : "testnet";
  const symbol = result.ok ? result.data.symbol : "BTCUSDT";

  return (
    <AppShell navItems={navItems} activeLabel="Mercado">
      <PageHeader
        eyebrow={`Mercado ${environment}`}
        title={symbol}
        trailing={<StatusPill><Database size={16} aria-hidden="true" />{formatDateTime(market?.captured_at)}</StatusPill>}
      />
      {!result.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>API sem resposta: {result.error}</Notice> : null}
      <section className="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-md:grid-cols-1">
        <MetricCard label="Último preço" value={formatMoney(market?.last_price, "USDT")} detail="Binance Spot Testnet" tone={market ? "positive" : "neutral"} />
        <MetricCard label="Variação 24h" value={percentLabel(market?.price_change_pct_24h)} detail="Snapshot de mercado" tone="neutral" />
        <MetricCard label="Volume 24h" value={market?.volume_24h ?? "-"} detail="BTCUSDT" tone="neutral" />
        <MetricCard label="Volatilidade" value={percentLabel(market?.volatility_pct)} detail="Indicador operacional" tone="warning" />
      </section>
      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Tendências" title="1h / 4h / 1d" icon={<LineChart />} />
          <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
            <StatPill label="1h" value={market?.trend_1h ?? "sem dado"} />
            <StatPill label="4h" value={market?.trend_4h ?? "sem dado"} />
            <StatPill label="1d" value={market?.trend_1d ?? "sem dado"} />
          </div>
        </Panel>
        <Panel>
          <PanelHeader eyebrow="Faixa 24h" title="Preço e spread" icon={<LineChart />} />
          <CompactList>
            <InfoRow label="Máxima" value={formatMoney(market?.high_price_24h)} />
            <InfoRow label="Mínima" value={formatMoney(market?.low_price_24h)} />
            <InfoRow label="Spread" value={market?.spread_bps == null ? "-" : `${market.spread_bps} bps`} />
          </CompactList>
        </Panel>
      </section>
    </AppShell>
  );
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}
