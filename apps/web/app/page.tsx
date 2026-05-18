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
        title="Dashboard operacional"
        trailing={
          <StatusCluster>
            <StatusPill tone={apiHealthy ? "positive" : "danger"}>
              <Database size={16} aria-hidden="true" />
              API {apiHealthy ? "online" : "indisponível"}
            </StatusPill>
            <StatusPill>
              <ShieldCheck size={16} aria-hidden="true" />
              {bot?.trading_mode ?? "testnet"} / {bot?.symbol ?? "BTCUSDT"}
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
          label="BTCUSDT"
          value={formatMoney(market?.last_price, "USDT")}
          detail={`Captura ${formatDateTime(market?.captured_at)}`}
          tone={market ? "positive" : "neutral"}
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
          detail={decisions[0]?.reason ?? "Aguardando ciclo auditável"}
          tone={decisions[0]?.decision === "COMPRA" ? "positive" : "warning"}
        />
      </section>

      <section className="grid grid-cols-[minmax(0,1.25fr)_minmax(330px,0.75fr)] gap-[18px] max-lg:grid-cols-2 max-md:grid-cols-1">
        <Panel className="row-span-2 max-lg:row-auto">
          <PanelHeader eyebrow="Mercado" title="BTCUSDT 1h / 4h / 1d" icon={<LineChart />} />
          <div
            className="grid h-[318px] grid-cols-6 items-end gap-3 rounded-[40px] border border-line bg-[linear-gradient(180deg,rgba(243,115,56,0.12),rgba(243,115,56,0)),repeating-linear-gradient(0deg,transparent,transparent_47px,rgba(20,20,19,0.07)_48px)] p-6"
            aria-label="Indicadores de mercado"
          >
            {["1h", "4h", "1d", "ATR", "RSI", "VOL"].map((label, index) => (
              <span
                className="relative min-h-[34px] rounded-t-full rounded-b-[10px] bg-ink after:absolute after:-top-[18px] after:left-1/2 after:size-2.5 after:-translate-x-1/2 after:rounded-full after:bg-signal-light after:content-['']"
                key={label}
                style={{ height: `${32 + index * 9}%` }}
                title={label}
              />
            ))}
          </div>
          <div className="mt-4 grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
            <StatPill label="Tendência 1h" value={market?.trend_1h ?? "sem dado"} />
            <StatPill label="Tendência 4h" value={market?.trend_4h ?? "sem dado"} />
            <StatPill label="Tendência 1d" value={market?.trend_1d ?? "sem dado"} />
            <StatPill label="Origem" value={sourceLabel(market?.source_payload)} />
          </div>
        </Panel>

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
          <PanelHeader eyebrow="Decisões" title="Últimos ciclos" icon={<Bot />} />
          <CompactList>
            {decisions.length === 0 ? (
              <EmptyState>Sem decisões registradas.</EmptyState>
            ) : (
              decisions.map((decision) => (
                <div
                  className="grid min-h-12 grid-cols-[130px_128px_minmax(0,1fr)_70px] items-center gap-3 border-b border-line pb-3 max-md:grid-cols-1"
                  key={decision.id}
                >
                  <time className="text-[13px] text-muted">{formatDateTime(decision.decided_at)}</time>
                  <strong className="text-[13px] text-link">{decision.decision}</strong>
                  <span className="text-[13px] text-muted">{decision.reason}</span>
                  <Link className="font-bold text-signal" href={`/decisions?decision=${decision.decision}`}>
                    Abrir
                  </Link>
                </div>
              ))
            )}
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
  return value ? `${value}%` : "-";
}

function sourceLabel(source: Record<string, unknown> | undefined) {
  if (!source) return "sem dado";
  const value = source.source;
  return typeof value === "string" ? value : "persistido";
}
