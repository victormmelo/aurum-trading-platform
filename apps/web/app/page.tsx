import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Database,
  LineChart,
  Power,
  Settings2,
  ShieldCheck,
  Wallet,
} from "lucide-react";
import Link from "next/link";

import { OperationalControls } from "@/app/bot/operational-controls";
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
  StatPill,
  StatusCluster,
  StatusPill,
} from "@/components/ui";
import {
  appEnv,
  formatDateTime,
  formatMoney,
  formatQuantity,
  getDashboardData,
  publicApiUrl,
  type BotStatus,
  type Decision,
  type MarketSummary,
  type PortfolioStatus,
  type PerformanceSummary,
  type RiskConfig,
  type StrategyConfig,
} from "@/lib/api";
import {
  explainDecision,
  type RuleCheck,
  type RuleStatus,
} from "@/lib/decision-explain";

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
  const latestDecision = decisions[0] ?? null;
  const latestDecisionExplanation = latestDecision ? explainDecision(latestDecision) : null;
  const strategy = data.strategyConfig.ok ? data.strategyConfig.data : null;
  const risk = data.riskConfig.ok ? data.riskConfig.data : null;
  const performance = data.performance.ok ? data.performance.data : null;
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
    <AppShell navItems={navItems} activeLabel="Dashboard" topbarActions={<OperationalControls bot={bot} />}>
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
        <div className="grid grid-cols-[minmax(0,0.85fr)_minmax(320px,1.15fr)] gap-5 max-xl:grid-cols-1">
          <CompactList>
            <InfoRow label="Status" value={botStatusLabel(bot?.status)} />
            <InfoRow label="Último ciclo" value={formatDateTime(bot?.last_cycle_at)} />
            <InfoRow label="Pausa/parada" value={formatDateTime(bot?.emergency_stopped_at ?? bot?.paused_at)} />
            <InfoRow label="Motivo" value={shortText(bot?.reason ?? "sem motivo registrado")} />
          </CompactList>

          <div className="grid content-start gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusPill tone={botStatusTone(bot?.status)}>{botStatusLabel(bot?.status)}</StatusPill>
              <StatusPill>Binance Spot Testnet</StatusPill>
              <StatusPill>BTCUSDT</StatusPill>
              <StatusPill>Long-only</StatusPill>
              <StatusPill>Sem alavancagem</StatusPill>
            </div>
            <ActionItem
              tone={operationalAttention.tone}
              title={operationalAttention.title}
              description={operationalAttention.description}
            />
          </div>
        </div>
      </Panel>

      <section className="grid gap-4">
        <PanelHeader eyebrow="Performance 30d" title="Resultado financeiro da estratégia" icon={<LineChart />} />
        {!data.performance.ok ? (
          <Notice tone="warning" icon={<AlertTriangle size={18} aria-hidden="true" />}>
            Não foi possível carregar a apuração de performance.
          </Notice>
        ) : null}
        <MetricCardGroup aria-label="Resultado financeiro">
          <MetricCard
            label="Realizado no período"
            value={formatMoney(performance?.realized_pnl)}
            detail={`${performance?.sell_count ?? 0} venda(s) · acerto ${percentLabel(performance?.win_rate_pct)}`}
            tone={moneyTone(performance?.realized_pnl)}
          />
          <MetricCard
            label="Aberto na posição"
            value={formatMoney(performance?.unrealized_pnl)}
            detail="PnL não realizado da carteira reconciliada"
            tone={moneyTone(performance?.unrealized_pnl)}
          />
          <MetricCard
            label="Resultado total"
            value={formatMoney(performance?.total_pnl)}
            detail={`Taxas ${formatMoney(performance?.total_fees_usdt)} · DD ${percentLabel(performance?.max_drawdown_pct)}`}
            tone={moneyTone(performance?.total_pnl)}
          />
          <MetricCard
            label="Status da estratégia"
            value={performanceStatusLabel(performance)}
            detail={`Retorno patrimonial ${percentLabel(performance?.return_pct)}`}
            tone={performanceStatusTone(performance)}
          />
        </MetricCardGroup>
        <Link className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary" href="/performance">
          Ver apuração por venda
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </section>

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
          value={latestDecisionExplanation?.meta.label ?? "sem decisão"}
          detail={latestDecision ? `${formatDateTime(latestDecision.decided_at)} · ${latestDecisionExplanation?.diagnostic.title}` : "Aguardando ciclo auditável"}
          tone={latestDecisionExplanation?.meta.tone ?? "warning"}
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
              <>
                {latestDecision ? <LatestDecisionSummary decision={latestDecision} /> : null}
                {decisions.slice(1, 4).map((decision) => (
                  <DashboardDecisionItem decision={decision} key={decision.id} />
                ))}
              </>
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

function LatestDecisionSummary({ decision }: { decision: Decision }) {
  const explanation = explainDecision(decision);
  const compactChecks = compactDashboardChecks(explanation.checks);

  return (
    <article className="grid gap-4 rounded-lg border border-primary/25 bg-primary/5 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <StatusPill tone={explanation.meta.tone}>{explanation.meta.label}</StatusPill>
            <StatusPill tone={explanation.diagnostic.tone}>{explanation.diagnostic.title}</StatusPill>
          </div>
          <time className="text-xs font-medium leading-5 text-muted-foreground">{formatDateTime(decision.decided_at)}</time>
          <p className="m-0 mt-2 text-sm leading-6 text-foreground">{explanation.diagnostic.explanation}</p>
          <p className="m-0 mt-1 text-xs leading-5 text-muted-foreground">{explanation.diagnostic.missingText}</p>
        </div>
        <Link className="inline-flex items-center gap-1 text-sm font-semibold text-primary" href={`/decisions?decision=${decision.decision}`}>
          Abrir
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-2 max-md:grid-cols-1" aria-label="Regras principais da última decisão">
        {compactChecks.map((check) => (
          <CompactDecisionRule check={check} key={check.label} />
        ))}
      </div>
    </article>
  );
}

function DashboardDecisionItem({ decision }: { decision: Decision }) {
  const explanation = explainDecision(decision);

  return (
    <article className="grid gap-3 rounded-lg border border-border bg-background p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <StatusPill tone={explanation.meta.tone}>{explanation.meta.shortLabel}</StatusPill>
        <Link className="inline-flex items-center gap-1 text-sm font-semibold text-primary" href={`/decisions?decision=${decision.decision}`}>
          Abrir
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>
      <div>
        <time className="text-xs font-medium leading-5 text-muted-foreground">{formatDateTime(decision.decided_at)}</time>
        <strong className="mt-1 block text-sm font-semibold leading-5 text-foreground">{explanation.diagnostic.title}</strong>
      </div>
      <p className="m-0 text-sm leading-6 text-muted-foreground">{shortText(explanation.diagnostic.explanation)}</p>
    </article>
  );
}

function CompactDecisionRule({ check }: { check: RuleCheck }) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-background px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold leading-5 text-foreground">{check.label}</span>
        <StatusPill className="min-h-7 px-2" tone={ruleStatusTone(check.status)}>
          {ruleStatusLabel(check.status)}
        </StatusPill>
      </div>
      <p className="m-0 text-xs leading-5 text-muted-foreground">{shortText(check.detail, 72)}</p>
    </div>
  );
}

function compactDashboardChecks(checks: RuleCheck[]) {
  const labels = new Set([
    "Regime long-only",
    "Preço acima da SMA 200",
    "Rompimento 20 candles",
    "Volume acima da média",
  ]);
  return checks.filter((check) => labels.has(check.label));
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

function performanceStatusLabel(value: PerformanceSummary | null) {
  if (!value) return "sem dados";
  if (value.status === "lucrando") return "Lucrando";
  if (value.status === "perdendo") return "Perdendo";
  if (value.status === "sem_amostra_suficiente") return "Sem amostra";
  return "Atenção";
}

function performanceStatusTone(
  value: PerformanceSummary | null,
): "positive" | "warning" | "danger" | "neutral" {
  if (!value) return "neutral";
  if (value.status === "lucrando") return "positive";
  if (value.status === "perdendo") return "danger";
  if (value.status === "sem_amostra_suficiente") return "warning";
  return "warning";
}

function ruleStatusTone(status: RuleStatus): "positive" | "warning" | "neutral" {
  if (status === "pass") return "positive";
  if (status === "fail") return "warning";
  return "neutral";
}

function ruleStatusLabel(status: RuleStatus) {
  if (status === "pass") return "Passou";
  if (status === "fail") return "Falhou";
  return "Sem dados";
}

function shortText(value: string, maxLength = 88) {
  return value.length > maxLength ? `${value.slice(0, maxLength - 3)}...` : value;
}

function botStatusLabel(value: string | undefined) {
  if (value === "running") return "Em execução";
  if (value === "paused") return "Pausado";
  if (value === "emergency_stop") return "Parada de emergência";
  return "Não inicializado";
}

function botStatusTone(value: string | undefined): "positive" | "warning" | "danger" | "neutral" {
  if (value === "running") return "positive";
  if (value === "paused") return "warning";
  if (value === "emergency_stop") return "danger";
  return "neutral";
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
