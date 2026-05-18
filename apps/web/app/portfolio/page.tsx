import { AlertTriangle, Wallet } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { CompactList, InfoRow, MetricCard, Notice, PageHeader, Panel, PanelHeader, StatusPill } from "@/components/ui";
import { fetchApi, formatDateTime, formatMoney, formatQuantity, type PortfolioStatus } from "@/lib/api";

export default async function PortfolioPage() {
  const result = await fetchApi<PortfolioStatus>("/portfolio/status");
  const snapshot = result.ok ? result.data.snapshot : null;
  const position = result.ok ? result.data.position : null;
  const environment = result.ok ? result.data.environment : "testnet";
  const symbol = result.ok ? result.data.symbol : "BTCUSDT";

  return (
    <AppShell navItems={navItems} activeLabel="Carteira">
      <PageHeader
        eyebrow={`Carteira ${environment}`}
        title="Posição financeira"
        trailing={<StatusPill><Wallet size={16} aria-hidden="true" />{symbol}</StatusPill>}
      />
      {!result.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>API sem resposta: {result.error}</Notice> : null}
      <section className="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-md:grid-cols-1">
        <MetricCard label="Patrimônio" value={formatMoney(snapshot?.total_equity)} detail={`Captura ${formatDateTime(snapshot?.captured_at)}`} tone="neutral" />
        <MetricCard label="USDT" value={formatMoney(snapshot?.usdt_balance)} detail="Saldo disponível" tone="neutral" />
        <MetricCard label="BTC" value={formatQuantity(snapshot?.btc_balance)} detail={formatMoney(snapshot?.btc_market_value)} tone="positive" />
        <MetricCard label="Exposição" value={percentLabel(snapshot?.exposure_pct)} detail="Long-only" tone="warning" />
      </section>
      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Resultado" title="PnL e taxas" icon={<Wallet />} />
          <CompactList>
            <InfoRow label="PnL realizado" value={formatMoney(snapshot?.realized_pnl)} />
            <InfoRow label="PnL não realizado" value={formatMoney(snapshot?.unrealized_pnl)} />
            <InfoRow label="Taxas totais" value={formatMoney(snapshot?.total_fees_usdt)} />
          </CompactList>
        </Panel>
        <Panel>
          <PanelHeader eyebrow="Posição" title={position?.asset ?? "BTC"} icon={<Wallet />} />
          <CompactList>
            <InfoRow label="Lado" value={position?.side ?? "-"} />
            <InfoRow label="Quantidade" value={formatQuantity(position?.quantity)} />
            <InfoRow label="Custo médio" value={formatMoney(position?.average_cost)} />
            <InfoRow label="Reconciliado" value={formatDateTime(position?.last_reconciled_at)} />
          </CompactList>
        </Panel>
      </section>
    </AppShell>
  );
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}
