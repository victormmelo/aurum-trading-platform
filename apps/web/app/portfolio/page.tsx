import { AlertTriangle, CheckCircle2, RefreshCw, Wallet } from "lucide-react";

import { reconcilePortfolio } from "@/app/portfolio/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CompactList,
  IconTextButton,
  InfoRow,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  StatusPill,
} from "@/components/ui";
import { fetchApi, formatDateTime, formatMoney, formatQuantity, type PortfolioStatus } from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

export default async function PortfolioPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
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
        trailing={
          <div className="flex flex-wrap items-center gap-2">
            <form action={reconcilePortfolio}>
              <IconTextButton>
                <RefreshCw size={16} aria-hidden="true" />
                Reconciliar
              </IconTextButton>
            </form>
            <StatusPill>
              <Wallet size={16} aria-hidden="true" />
              {symbol}
            </StatusPill>
          </div>
        }
      />
      {success ? <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>{success}</Notice> : null}
      {error ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>{error}</Notice> : null}
      {!result.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>API sem resposta: {result.error}</Notice> : null}
      <MetricCardGroup aria-label="Indicadores da carteira">
        <MetricCard label="Patrimônio" value={formatMoney(snapshot?.total_equity)} detail={`Captura ${formatDateTime(snapshot?.captured_at)}`} tone="neutral" />
        <MetricCard label="USDT" value={formatMoney(snapshot?.usdt_balance)} detail="Saldo disponível" tone="neutral" />
        <MetricCard label="BTC" value={formatQuantity(snapshot?.btc_balance)} detail={formatMoney(snapshot?.btc_market_value)} tone="positive" />
        <MetricCard label="Exposição" value={percentLabel(snapshot?.exposure_pct)} detail="Long-only" tone="warning" />
      </MetricCardGroup>
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

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
