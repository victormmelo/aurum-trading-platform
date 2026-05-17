import {
  Activity,
  AlertTriangle,
  Bot,
  CirclePause,
  Database,
  FileDown,
  Gauge,
  KeyRound,
  LineChart,
  Settings2,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import {
  apiUrl,
  appEnv,
  formatDateTime,
  formatMoney,
  formatQuantity,
  getDashboardData,
} from "@/lib/api";

const navItems = [
  { label: "Dashboard", href: "/", icon: Gauge, disabled: false },
  { label: "Mercado", href: "/", icon: LineChart, disabled: false },
  { label: "Carteira", href: "/", icon: Wallet, disabled: false },
  { label: "Operações", href: "/", icon: Activity, disabled: false },
  { label: "Decisões", href: "/decisions", icon: Bot, disabled: false },
  { label: "Estratégias", href: "/configs", icon: Settings2, disabled: false },
  { label: "MCP", href: "/", icon: KeyRound, disabled: true },
  { label: "Exportações", href: "/", icon: FileDown, disabled: false },
] as const;

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
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">
            <span />
            <span />
          </div>
          <div>
            <strong>Aurum</strong>
            <span>BTC Testnet</span>
          </div>
        </div>
        <nav className="nav" aria-label="Navegação principal">
          {navItems.map(({ label, href, icon: Icon, disabled }, index) => (
            <Link
              aria-disabled={disabled ? "true" : undefined}
              className={[
                "navItem",
                index === 0 ? "active" : "",
                disabled ? "disabled" : "",
              ].join(" ")}
              href={href}
              key={label}
              title={disabled ? "MCP será habilitado após VIC-33" : undefined}
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Ambiente {bot?.environment ?? appEnv}</p>
            <h1>Dashboard operacional</h1>
          </div>
          <div className="statusCluster" aria-label="Status do sistema">
            <span className={apiHealthy ? "statusPill ok" : "statusPill danger"}>
              <Database size={16} aria-hidden="true" />
              API {apiHealthy ? "online" : "indisponível"}
            </span>
            <span className="statusPill">
              <ShieldCheck size={16} aria-hidden="true" />
              {bot?.trading_mode ?? "testnet"} / {bot?.symbol ?? "BTCUSDT"}
            </span>
            <span className={bot?.status === "running" ? "statusPill ok" : "statusPill warning"}>
              <CirclePause size={16} aria-hidden="true" />
              {bot?.status ?? "sem estado"}
            </span>
          </div>
        </header>

        {!apiHealthy ? (
          <section className="noticePanel">
            <AlertTriangle size={18} aria-hidden="true" />
            <span>API {apiUrl} sem resposta completa.</span>
          </section>
        ) : null}

        <section className="metricsGrid" aria-label="Indicadores principais">
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

        <section className="contentGrid">
          <article className="panel marketPanel">
            <PanelHeader eyebrow="Mercado" title="BTCUSDT 1h / 4h / 1d" icon={<LineChart />} />
            <div className="chartMock" aria-label="Indicadores de mercado">
              {["1h", "4h", "1d", "ATR", "RSI", "VOL"].map((label, index) => (
                <span
                  className="signalBar"
                  key={label}
                  style={{ height: `${32 + index * 9}%` }}
                  title={label}
                />
              ))}
            </div>
            <div className="marketStats">
              <StatPill label="Tendência 1h" value={market?.trend_1h ?? "sem dado"} />
              <StatPill label="Tendência 4h" value={market?.trend_4h ?? "sem dado"} />
              <StatPill label="Tendência 1d" value={market?.trend_1d ?? "sem dado"} />
              <StatPill label="Origem" value={sourceLabel(market?.source_payload)} />
            </div>
          </article>

          <article className="panel">
            <PanelHeader eyebrow="Carteira" title="Saldo e posição" icon={<Wallet />} />
            <div className="tableList">
              <InfoRow label="USDT" value={formatMoney(portfolioSnapshot?.usdt_balance)} />
              <InfoRow label="BTC" value={formatQuantity(portfolioSnapshot?.btc_balance)} />
              <InfoRow label="Custo médio" value={formatMoney(portfolioSnapshot?.average_cost)} />
              <InfoRow label="PnL não realizado" value={formatMoney(portfolioSnapshot?.unrealized_pnl)} />
            </div>
          </article>

          <article className="panel">
            <PanelHeader eyebrow="Decisões" title="Últimos ciclos" icon={<Bot />} />
            <div className="decisionList">
              {decisions.length === 0 ? (
                <EmptyState text="Sem decisões registradas." />
              ) : (
                decisions.map((decision) => (
                  <div className="decisionRow" key={decision.id}>
                    <time>{formatDateTime(decision.decided_at)}</time>
                    <strong>{decision.decision}</strong>
                    <span>{decision.reason}</span>
                    <Link href={`/decisions?decision=${decision.decision}`}>Abrir</Link>
                  </div>
                ))
              )}
            </div>
          </article>

          <article className="panel">
            <PanelHeader eyebrow="Risco" title="Bloqueios e limites" icon={<ShieldCheck />} />
            <div className="riskGrid">
              <StatPill label="Risco/trade" value={percentLabel(risk?.risk_per_trade_pct)} />
              <StatPill label="Perda diária" value={percentLabel(risk?.daily_loss_limit_pct)} />
              <StatPill label="Exposição máx." value={percentLabel(risk?.max_exposure_pct)} />
              <StatPill label="Config" value={risk ? `v${risk.version}` : "sem config"} />
            </div>
          </article>

          <article className="panel">
            <PanelHeader eyebrow="Operações" title="Ordens e fills" icon={<Activity />} />
            <div className="tableList">
              <InfoRow label="Ordens recentes" value={String(orders.length)} />
              <InfoRow label="Fills recentes" value={String(fills.length)} />
              <InfoRow label="Última ordem" value={orders[0]?.status ?? "sem ordem"} />
              <InfoRow label="Último fill" value={formatDateTime(fills[0]?.filled_at)} />
            </div>
          </article>

          <article className="panel">
            <PanelHeader eyebrow="Estratégia" title="Config ativa" icon={<Settings2 />} />
            <div className="tableList">
              <InfoRow label="Nome" value={strategy?.name ?? "sem config"} />
              <InfoRow label="Versão" value={strategy ? `v${strategy.version}` : "-"} />
              <InfoRow label="Sinal" value={strategy?.signal_timeframe ?? "-"} />
              <InfoRow label="Regime" value={strategy?.regime_timeframe_primary ?? "-"} />
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}

function MetricCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: "positive" | "warning" | "neutral";
}) {
  return (
    <article className="metricCard">
      <span>{label}</span>
      <strong className={`metricValue ${tone}`}>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function PanelHeader({
  eyebrow,
  title,
  icon,
}: {
  eyebrow: string;
  title: string;
  icon: ReactNode;
}) {
  return (
    <div className="panelHeader">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      <span className="iconOrbit">{icon}</span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="tableRow">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="riskItem">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="emptyState">{text}</div>;
}

function percentLabel(value: string | null | undefined) {
  return value ? `${value}%` : "-";
}

function sourceLabel(source: Record<string, unknown> | undefined) {
  if (!source) return "sem dado";
  const value = source.source;
  return typeof value === "string" ? value : "persistido";
}
