import { AlertTriangle, Database } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { LiveMarketCards, LiveMarketPanel } from "@/components/live-market";
import { Notice, PageHeader, StatusPill } from "@/components/ui";
import { fetchApi, formatDateTime, type MarketSummary } from "@/lib/api";

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
      <LiveMarketCards initial={result.ok ? result.data : { environment, symbol, snapshot: null }} />
      <LiveMarketPanel initial={result.ok ? result.data : { environment, symbol, snapshot: null }} />
    </AppShell>
  );
}
