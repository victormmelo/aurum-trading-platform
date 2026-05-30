import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  CirclePause,
  CirclePlay,
  Database,
  OctagonAlert,
  Pause,
  Power,
  Settings2,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import Link from "next/link";

import {
  emergencyStopBot,
  initializeBot,
  pauseBot,
  resumeBot,
} from "@/app/bot/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { LiveMarketDashboardPanel } from "@/components/live-market";
import {
  ActionItem,
  CompactList,
  EmptyState,
  InfoRow,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PrimaryButton,
  StatPill,
  StatusCluster,
  StatusPill,
  IconTextButton,
  cx,
} from "@/components/ui";
import {
  appEnv,
  formatDateTime,
  formatMoney,
  formatQuantity,
  getDashboardData,
  publicApiUrl,
  type BotStatus,
  type MarketSummary,
  type PortfolioStatus,
  type RiskConfig,
  type StrategyConfig,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;
type AttentionTone = "positive" | "warning" | "danger";
type OperationalAttention = {
  tone: AttentionTone;
  title: string;
  description: string;
};

export default async function DashboardPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
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
  const environment =
    bot?.environment ??
    (data.market.ok ? data.market.data.environment : null) ??
    (data.portfolio.ok ? data.portfolio.data.environment : null) ??
    (data.decisions.ok ? data.decisions.data.environment : null) ??
    appEnv;
  const symbol =
    bot?.symbol ??
    (data.market.ok ? data.market.data.symbol : null) ??
    (data.portfolio.ok ? data.portfolio.data.symbol : null) ??
    (data.decisions.ok ? data.decisions.data.symbol : null) ??
    "BTCUSDT";
  const marketPrice = formatMoney(market?.last_price, "USDT");
  const apiHealthy = data.health.ok;
  const operationalDataComplete = [
    data.bot,
    data.market,
    data.portfolio,
    data.orders,
    data.fills,
    data.decisions,
  ].every((result) => result.ok);
  const operationalAttention = getOperationalAttention({
    apiHealthy,
    bot,
    market,
    portfolioSnapshot,
    strategy,
    risk,
    historyComplete: data.orders.ok && data.fills.ok && data.decisions.ok,
  });

  return (
    <AppShell navItems={navItems} activeLabel="Dashboard">
      <PageHeader
        eyebrow={environmentLabel(environment)}
        title="Aurum operacional"
        description="Supervisão do robô BTCUSDT em Testnet com foco em estado operacional, risco, carteira, sinais e próximos pontos de atenção."
        trailing={
          <StatusCluster>
            <StatusPill tone={apiHealthy ? "positive" : "danger"}>
              <Database size={16} aria-hidden="true" />
              API {apiHealthy ? "online" : "indisponível"}
            </StatusPill>
            <StatusPill>
              <ShieldCheck size={16} aria-hidden="true" />
              {environmentLabel(bot?.trading_mode ?? environment)}
            </StatusPill>
            <StatusPill>
              <Activity size={16} aria-hidden="true" />
              {symbol}
            </StatusPill>
          </StatusCluster>
        }
      />

      {success ? (
        <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>
          {success}
        </Notice>
      ) : null}
      {error ? (
        <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>
          {error}
        </Notice>
      ) : null}
      {!apiHealthy ? (
        <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API {publicApiUrl} indisponível.
        </Notice>
      ) : !data.bot.ok ? (
        <Notice icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API online, mas o estado operacional do robô ainda não foi cadastrado.
        </Notice>
      ) : !operationalDataComplete ? (
        <Notice icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API online, mas alguns dados operacionais ainda estão incompletos.
        </Notice>
      ) : null}

      <Panel>
        <PanelHeader eyebrow="Estado operacional" title="Robô e prontidão" icon={<Power />} />
        <div className="grid grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)] gap-5 max-xl:grid-cols-1">
          <div className="grid content-start gap-5">
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill tone={botStatusTone(bot?.status)}>
                <CirclePause size={16} aria-hidden="true" />
                {botStatusLabel(bot?.status)}
              </StatusPill>
              <StatusPill>
                <ShieldCheck size={16} aria-hidden="true" />
                Binance Spot Testnet
              </StatusPill>
              <StatusPill>BTCUSDT</StatusPill>
              <StatusPill>Long-only</StatusPill>
              <StatusPill>Sem alavancagem</StatusPill>
            </div>

            <div className="grid gap-2">
              <span className="text-xs font-medium leading-5 text-muted-foreground">Estado do robô</span>
              <strong className={cx("text-3xl font-semibold leading-tight tracking-tight md:text-4xl", botStatusTextClass(bot?.status))}>
                {botStatusLabel(bot?.status)}
              </strong>
              <p className="m-0 max-w-[780px] text-sm leading-6 text-muted-foreground">
                {botStatusDescription(bot?.status)}
              </p>
            </div>

            <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
              <StatPill label="API" value={apiHealthy ? "online" : "indisponível"} />
              <StatPill label="Último ciclo" value={formatDateTime(bot?.last_cycle_at)} />
              <StatPill label="Pausa/parada" value={formatDateTime(bot?.emergency_stopped_at ?? bot?.paused_at)} />
              <StatPill label="Motivo" value={shortText(bot?.reason ?? "sem motivo registrado")} />
            </div>

            <div className="flex flex-wrap gap-2">
              {!bot ? (
                <form action={initializeBot}>
                  <PrimaryButton>
                    <CirclePlay size={16} aria-hidden="true" />
                    Inicializar robô
                  </PrimaryButton>
                </form>
              ) : null}
              {bot?.status === "paused" ? (
                <form action={resumeBot}>
                  <PrimaryButton>
                    <CirclePlay size={16} aria-hidden="true" />
                    Retomar
                  </PrimaryButton>
                </form>
              ) : null}
              {bot?.status === "running" ? (
                <form action={pauseBot}>
                  <IconTextButton>
                    <Pause size={16} aria-hidden="true" />
                    Pausar
                  </IconTextButton>
                </form>
              ) : null}
            </div>
          </div>

          <div className="grid content-start gap-4">
            <ActionItem
              tone={operationalAttention.tone}
              title={operationalAttention.title}
              description={operationalAttention.description}
            />

            <form
              action={emergencyStopBot}
              className="grid content-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4"
            >
              <div className="flex items-center gap-2 text-sm font-semibold text-destructive">
                <OctagonAlert size={18} aria-hidden="true" />
                Parada de emergência
              </div>
              <p className="m-0 text-sm leading-6 text-muted-foreground">
                Interrompe novas operações e bloqueia retomada automática. Digite PARAR para confirmar.
              </p>
              <input
                className="min-h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-5 text-foreground outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!bot || bot.status === "emergency_stop"}
                name="confirmation"
                placeholder="PARAR"
              />
              <input name="reason" type="hidden" value="Parada de emergência acionada pelo dashboard" />
              <button
                className={cx(
                  "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-destructive/40 bg-background px-4 text-sm font-medium leading-none text-destructive transition-colors hover:bg-destructive/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  (!bot || bot.status === "emergency_stop") && "cursor-not-allowed opacity-50",
                )}
                disabled={!bot || bot.status === "emergency_stop"}
                type="submit"
              >
                <OctagonAlert size={16} aria-hidden="true" />
                Acionar parada
              </button>
            </form>
          </div>
        </div>
      </Panel>

      <MetricCardGroup aria-label="Indicadores principais">
        <MetricCard
          label="Preço BTCUSDT"
          value={marketPrice}
          detail={`24h ${percentLabel(market?.price_change_pct_24h)} · ${formatDateTime(market?.captured_at)}`}
          tone={marketChangeTone(market?.price_change_pct_24h)}
        />
        <MetricCard
          label="Patrimônio"
          value={formatMoney(portfolioSnapshot?.total_equity)}
          detail={`Exposição ${portfolioSnapshot?.exposure_pct ?? "0"}%`}
          tone="neutral"
        />
        <MetricCard
          label="PnL não realizado"
          value={formatMoney(portfolioSnapshot?.unrealized_pnl)}
          detail={`Realizado ${formatMoney(portfolioSnapshot?.realized_pnl)} · Taxas ${formatMoney(portfolioSnapshot?.total_fees_usdt)}`}
          tone={moneyTone(portfolioSnapshot?.unrealized_pnl)}
        />
        <MetricCard
          label="Última decisão"
          value={decisionLabel(decisions[0]?.decision)}
          detail={decisions[0] ? `${formatDateTime(decisions[0].decided_at)} · ${shortText(decisions[0].reason)}` : "Aguardando ciclo auditável"}
          tone={decisionTone(decisions[0]?.decision)}
        />
      </MetricCardGroup>

      <section className="grid grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)] gap-4 max-xl:grid-cols-1">
        <LiveMarketDashboardPanel
          initial={data.market.ok ? data.market.data : { environment, symbol, snapshot: null }}
        />

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
            <div className="grid gap-4">
              <ActionItem
                tone={risk ? "positive" : "warning"}
                title={risk ? "Configuração de risco ativa" : "Risco sem configuração ativa"}
                description={
                  risk
                    ? `Versão v${risk.version} aplicada ao robô ${symbol}.`
                    : "Crie e ative uma configuração antes de liberar ciclos operacionais."
                }
              />
              <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
                <StatPill label="Risco/trade" value={percentLabel(risk?.risk_per_trade_pct)} />
                <StatPill label="Perda diária" value={percentLabel(risk?.daily_loss_limit_pct)} />
                <StatPill label="Exposição máx." value={percentLabel(risk?.max_exposure_pct)} />
                <StatPill label="Config" value={risk ? `v${risk.version}` : "sem config"} />
              </div>
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
                <article
                  className="grid gap-3 rounded-lg border border-border bg-background p-4"
                  key={decision.id}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <StatusPill tone={decisionTone(decision.decision)}>{decisionLabel(decision.decision)}</StatusPill>
                    <Link className="inline-flex items-center gap-1 text-sm font-semibold text-primary" href={`/decisions?decision=${decision.decision}`}>
                      Abrir
                      <ArrowRight size={14} aria-hidden="true" />
                    </Link>
                  </div>
                  <time className="text-xs font-medium leading-5 text-muted-foreground">{formatDateTime(decision.decided_at)}</time>
                  <p className="m-0 text-sm leading-6 text-muted-foreground">{shortText(decision.reason)}</p>
                </article>
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
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value}%`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 4 })}%`;
}

function marketChangeTone(value: string | null | undefined): "positive" | "warning" | "neutral" {
  const parsed = value == null ? Number.NaN : Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return "neutral";
  return parsed > 0 ? "positive" : "warning";
}

function moneyTone(value: string | null | undefined): "positive" | "warning" | "neutral" {
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

function decisionLabel(value: string | undefined) {
  if (value === "COMPRA") return "Compra";
  if (value === "VENDA") return "Venda";
  if (value === "MANTER_POSICAO") return "Manter posição";
  if (value === "NAO_OPERAR") return "Não operar";
  return "sem decisão";
}

function shortText(value: string) {
  return value.length > 88 ? `${value.slice(0, 85)}...` : value;
}

function botStatusLabel(value: string | undefined) {
  if (value === "running") return "Em execução";
  if (value === "paused") return "Pausado";
  if (value === "emergency_stop") return "Parada de emergência";
  return "Não inicializado";
}

function botStatusDescription(value: string | undefined) {
  if (value === "running") return "Ciclos operacionais liberados para o ambiente Testnet.";
  if (value === "paused") return "Robô cadastrado e pausado. Retome apenas depois de validar configurações, mercado e carteira.";
  if (value === "emergency_stop") return "Operação bloqueada por parada de emergência. A retomada precisa de intervenção técnica.";
  return "Crie o estado operacional inicial para controlar pausa, retomada e parada de emergência pela interface.";
}

function botStatusTone(value: string | undefined): "positive" | "warning" | "danger" | "neutral" {
  if (value === "running") return "positive";
  if (value === "paused") return "warning";
  if (value === "emergency_stop") return "danger";
  return "neutral";
}

function botStatusTextClass(value: string | undefined) {
  if (value === "running") return "text-primary";
  if (value === "emergency_stop") return "text-destructive";
  return "text-foreground";
}

function environmentLabel(value: string | null | undefined) {
  if (!value) return "Binance Spot Testnet";
  const normalized = value.toLowerCase();
  return normalized === "testnet" || normalized === "development" ? "Binance Spot Testnet" : value;
}

function getOperationalAttention({
  apiHealthy,
  bot,
  market,
  portfolioSnapshot,
  strategy,
  risk,
  historyComplete,
}: {
  apiHealthy: boolean;
  bot: BotStatus | null;
  market: MarketSummary["snapshot"];
  portfolioSnapshot: PortfolioStatus["snapshot"];
  strategy: StrategyConfig;
  risk: RiskConfig;
  historyComplete: boolean;
}): OperationalAttention {
  if (!apiHealthy) {
    return {
      tone: "danger",
      title: "Próximo ponto de atenção: API indisponível",
      description: `Confirme a disponibilidade de ${publicApiUrl} antes de avaliar mercado, carteira ou comandos do robô.`,
    };
  }
  if (!bot) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: inicializar robô",
      description: "Crie o estado operacional inicial para liberar os comandos de pausa, retomada e parada de emergência.",
    };
  }
  if (bot.status === "emergency_stop") {
    return {
      tone: "danger",
      title: "Próximo ponto de atenção: parada de emergência",
      description: "A operação está bloqueada. Revise o motivo registrado e faça a retomada apenas por intervenção técnica controlada.",
    };
  }
  if (!strategy) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: estratégia sem config",
      description: "Ative uma configuração de estratégia antes de considerar ciclos operacionais do robô.",
    };
  }
  if (!risk) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: risco sem config",
      description: "Ative limites de risco antes de considerar ciclos operacionais do robô.",
    };
  }
  if (!market) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: mercado sem snapshot",
      description: "Aguarde ou reconcilie dados de mercado BTCUSDT antes de avaliar sinais e execução.",
    };
  }
  if (!portfolioSnapshot) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: carteira sem snapshot",
      description: "Reconcilie a carteira Binance Spot Testnet antes de avaliar exposição, saldo e PnL.",
    };
  }
  if (!historyComplete) {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: histórico parcial",
      description: "Algumas listas de ordens, fills ou decisões não carregaram. Revise a API antes de concluir a leitura operacional.",
    };
  }
  if (bot.status === "paused") {
    return {
      tone: "warning",
      title: "Próximo ponto de atenção: robô pausado",
      description: "Valide estratégia, risco, mercado e carteira antes de retomar ciclos em Testnet.",
    };
  }
  return {
    tone: "positive",
    title: "Próximo ponto de atenção: monitorar ciclo",
    description: "Robô, estratégia, risco, mercado e carteira têm dados para supervisão. Acompanhe a próxima decisão auditável.",
  };
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
