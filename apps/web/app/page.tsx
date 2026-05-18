import {
  Activity,
  AlertTriangle,
  Bot,
  CirclePause,
  Database,
  LineChart,
  Settings2,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import Link from "next/link";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CompactList,
  EmptyState,
  InfoRow,
  MetricCard,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  StatPill,
  StatusCluster,
  StatusPill,
} from "@/components/ui";
import {
  apiUrl,
  appEnv,
  formatDateTime,
  formatMoney,
  formatQuantity,
  getDashboardData,
} from "@/lib/api";

export default async function DashboardPage() {
  const data = await getDashboardData();
  const bot = data.bot.ok ? data.bot.data : null;
  const market = data.market.ok ? data.market.data.snapshot : null;
  const portfolio = data.portfolio.ok ? data.portfolio.data : null;
  const portfolioSnapshot = portfolio?.snapshot ?? null;
  const orders = data.orders.ok ? data.orders.data.orders : [];
  const fills = data.fills.ok ? data.fills.data.fills : [];
  const decisions = data.decisions.ok ? data.decisions.data.decisions : [];
  const strategy = data.strategyConfig.ok ? data.strategyConfig.data : null;
  const risk = data.riskConfig.ok ? data.riskConfig.data : null;
  const marketPrice = formatMoney(market?.last_price, "USDT");
  const apiHealthy = [
    data.bot,
    data.market,
    data.portfolio,
    data.orders,
    data.fills,
    data.decisions,
  ].every((result) => result.ok);

  return (
    <AppShell navItems={navItems} activeLabel="Dashboard">
      <PageHeader
        eyebrow={`Ambiente ${bot?.environment ?? appEnv}`}
        title="Aurum operacional"
        description="Controle do robô BTCUSDT em Testnet, com mercado, carteira, risco, operações e decisões auditáveis em uma única visão."
        trailing={
          <StatusCluster>
            <StatusPill tone={apiHealthy ? "positive" : "danger"}>
              <Database size={16} aria-hidden="true" />
              API {apiHealthy ? "online" : "indisponível"}
            </StatusPill>
            <StatusPill>
              <ShieldCheck size={16} aria-hidden="true" />
              {bot?.trading_mode ?? "testnet"} · {bot?.symbol ?? "BTCUSDT"}
            </StatusPill>
            <StatusPill tone={bot?.status === "running" ? "positive" : "warning"}>
              <CirclePause size={16} aria-hidden="true" />
              {bot?.status ?? "sem estado"}
            </StatusPill>
          </StatusCluster>
        }
      />

      {!apiHealthy ? (
        <Notice icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API {apiUrl} sem resposta completa.
        </Notice>
      ) : null}

      <section className="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-md:grid-cols-1" aria-label="Indicadores principais">
        <MetricCard
          label="Preço BTCUSDT"
          value={marketPrice}
          detail={`24h ${percentLabel(market?.price_change_pct_24h)} · ${formatDateTime(market?.captured_at)}`}
          tone={marketChangeTone(market?.price_change_pct_24h)}
        />
        <MetricCard
          label="Robô"
          value={bot?.status ?? "sem estado"}
          detail={`Último ciclo ${formatDateTime(bot?.last_cycle_at)}`}
          tone={bot?.status === "running" ? "positive" : "warning"}
        />
        <MetricCard
          label="Patrimônio"
          value={formatMoney(portfolioSnapshot?.total_equity)}
          detail={`Exposição ${portfolioSnapshot?.exposure_pct ?? "0"}%`}
          tone="neutral"
        />
        <MetricCard
          label="Última decisão"
          value={decisions[0]?.decision ?? "sem decisão"}
          detail={shortText(decisions[0]?.reason ?? "Aguardando ciclo auditável")}
          tone={decisionTone(decisions[0]?.decision)}
        />
      </section>

      <section className="grid grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)] gap-4 max-xl:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Mercado" title="BTCUSDT operacional" icon={<LineChart />} />
          <div className="grid gap-5" aria-label="Indicadores de mercado">
            <div className="flex items-start justify-between gap-5 max-md:flex-col">
              <div className="min-w-0">
                <span className="text-sm leading-[1.43] tracking-[-0.224px] text-ink-muted-48">Último preço</span>
                <strong className="mt-2 block break-words font-display text-[40px] font-semibold leading-[1.08] tracking-[-0.28px] md:text-[56px]">
                  {marketPrice === "-" ? "Sem preço" : marketPrice}
                </strong>
                <p className="m-0 mt-3 max-w-[520px] text-[17px] leading-[1.47] tracking-[-0.374px] text-ink-muted-48">
                  Snapshot de mercado capturado em {formatDateTime(market?.captured_at)}.
                </p>
              </div>
              <StatusPill tone={marketChangeTone(market?.price_change_pct_24h)}>
                24h {percentLabel(market?.price_change_pct_24h)}
              </StatusPill>
            </div>
            <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
              <InfoRow label="Máxima 24h" value={formatMoney(market?.high_price_24h)} />
              <InfoRow label="Mínima 24h" value={formatMoney(market?.low_price_24h)} />
              <InfoRow label="Volume 24h" value={market?.volume_24h ?? "-"} />
              <InfoRow label="Spread" value={market?.spread_bps == null ? "-" : `${market.spread_bps} bps`} />
              <InfoRow label="Volatilidade" value={percentLabel(market?.volatility_pct)} />
              <InfoRow label="Origem" value={sourceLabel(market?.source_payload)} />
            </div>
            <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
              <StatPill label="Tendência 1h" value={market?.trend_1h ?? "sem dado"} />
              <StatPill label="Tendência 4h" value={market?.trend_4h ?? "sem dado"} />
              <StatPill label="Tendência 1d" value={market?.trend_1d ?? "sem dado"} />
            </div>
          </div>
        </Panel>

        <div className="grid gap-4">
          <Panel>
            <PanelHeader eyebrow="Carteira" title="Saldo e posição" icon={<Wallet />} />
            <CompactList>
              <InfoRow label="USDT" value={formatMoney(portfolioSnapshot?.usdt_balance)} />
              <InfoRow label="BTC" value={formatQuantity(portfolioSnapshot?.btc_balance)} />
              <InfoRow label="Custo médio" value={formatMoney(portfolioSnapshot?.average_cost)} />
              <InfoRow label="PnL não realizado" value={formatMoney(portfolioSnapshot?.unrealized_pnl)} />
            </CompactList>
          </Panel>

          <Panel>
            <PanelHeader eyebrow="Risco" title="Bloqueios e limites" icon={<ShieldCheck />} />
            <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
              <StatPill label="Risco/trade" value={percentLabel(risk?.risk_per_trade_pct)} />
              <StatPill label="Perda diária" value={percentLabel(risk?.daily_loss_limit_pct)} />
              <StatPill label="Exposição máx." value={percentLabel(risk?.max_exposure_pct)} />
              <StatPill label="Config" value={risk ? `v${risk.version}` : "sem config"} />
            </div>
          </Panel>
        </div>
      </section>

      <section className="grid grid-cols-3 gap-4 max-xl:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Decisões" title="Últimos ciclos" icon={<Bot />} />
          <CompactList>
            {decisions.length === 0 ? (
              <EmptyState>Sem decisões registradas.</EmptyState>
            ) : (
              decisions.slice(0, 4).map((decision) => (
                <div
                  className="grid min-h-12 grid-cols-[128px_126px_minmax(0,1fr)_54px] items-center gap-3 border-b border-hairline pb-3 max-md:grid-cols-1"
                  key={decision.id}
                >
                  <time className="text-[13px] leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{formatDateTime(decision.decided_at)}</time>
                  <strong className="text-[13px] font-semibold leading-[1.29] tracking-[-0.224px] text-primary">{decision.decision}</strong>
                  <span className="text-[13px] leading-[1.43] tracking-[-0.224px] text-ink-muted-48">{shortText(decision.reason)}</span>
                  <Link className="text-[13px] font-semibold text-primary" href={`/decisions?decision=${decision.decision}`}>
                    Abrir
                  </Link>
                </div>
              ))
            )}
          </CompactList>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Operações" title="Ordens e fills" icon={<Activity />} />
          <CompactList>
            <InfoRow label="Ordens recentes" value={String(orders.length)} />
            <InfoRow label="Fills recentes" value={String(fills.length)} />
            <InfoRow label="Última ordem" value={orders[0]?.status ?? "sem ordem"} />
            <InfoRow label="Último fill" value={formatDateTime(fills[0]?.filled_at)} />
          </CompactList>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Estratégia" title="Config ativa" icon={<Settings2 />} />
          <CompactList>
            <InfoRow label="Nome" value={strategy?.name ?? "sem config"} />
            <InfoRow label="Versão" value={strategy ? `v${strategy.version}` : "-"} />
            <InfoRow label="Sinal" value={strategy?.signal_timeframe ?? "-"} />
            <InfoRow label="Regime" value={strategy?.regime_timeframe_primary ?? "-"} />
          </CompactList>
        </Panel>
      </section>
    </AppShell>
  );
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

function sourceLabel(source: Record<string, unknown> | undefined) {
  if (!source) return "sem dado";
  const value = source.source;
  return typeof value === "string" ? value : "persistido";
}

function marketChangeTone(value: string | null | undefined): "positive" | "warning" | "neutral" {
  const parsed = value == null ? Number.NaN : Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return "neutral";
  return parsed > 0 ? "positive" : "warning";
}

function decisionTone(value: string | undefined): "positive" | "warning" | "neutral" {
  if (value === "COMPRA") return "positive";
  if (value === "VENDA") return "warning";
  if (value === "MANTER_POSICAO" || value === "NAO_OPERAR") return "neutral";
  return "warning";
}

function shortText(value: string) {
  return value.length > 88 ? `${value.slice(0, 85)}...` : value;
}
