import {
  BadgeCheck,
  Bot,
  Braces,
  CircleAlert,
  CircleCheck,
  CircleHelp,
  Clock3,
  Gauge,
  ListFilter,
  PackageCheck,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  EmptyState,
  FilterChip,
  JsonDetails,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  PagerLink,
  Panel,
  StatPill,
  StatusCluster,
  StatusPill,
} from "@/components/ui";
import {
  fetchApi,
  formatDateTime,
  formatMoney,
  formatQuantity,
  type Decision,
  type DecisionsResponse,
} from "@/lib/api";
import {
  countByDecision,
  decisionFilters,
  decisionMeta,
  explainDecision,
  hasEntries,
  percentValue,
  plainValue,
  readPortfolio,
  readReason,
  readSignal,
  stringValue,
  type DecisionDiagnostic,
  type DecisionValue,
  type RuleCheck,
  type RuleStatus,
} from "@/lib/decision-explain";

const pageSize = 20;

type SearchParams = Record<string, string | string[] | undefined>;

export default async function DecisionsPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const decision = single(params.decision);
  const activeDecision = isDecisionFilter(decision) ? decision : undefined;
  const offset = numericOffset(single(params.offset));
  const query = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
  if (activeDecision) query.set("decision", activeDecision);

  const result = await fetchApi<DecisionsResponse>(`/decisions?${query.toString()}`);
  const decisions = result.ok ? result.data.decisions : [];
  const environment = result.ok ? result.data.environment : "testnet";
  const symbol = result.ok ? result.data.symbol : "BTCUSDT";
  const latest = decisions[0];
  const counts = countByDecision(decisions);

  return (
    <AppShell navItems={navItems} activeLabel="Decisões">
      <PageHeader
        eyebrow={`Auditoria ${environment}`}
        title="Decisões do robô"
        description="Entenda o que o robô decidiu em cada ciclo e quais fatores bloquearam ou liberaram operação."
        trailing={
          <StatusCluster>
            <StatusPill>
              <Bot size={16} aria-hidden="true" />
              {environment} · {symbol}
            </StatusPill>
            <StatusPill tone={latest ? decisionMeta(latest.decision).tone : "neutral"}>
              <BadgeCheck size={16} aria-hidden="true" />
              {latest ? decisionMeta(latest.decision).label : "Sem decisão"}
            </StatusPill>
          </StatusCluster>
        }
      />

      <section className="grid grid-cols-3 gap-4 max-lg:grid-cols-1" aria-label="Resumo das decisões carregadas">
        <MetricCardGroup className="lg:col-span-2" aria-label="Indicadores de decisões">
          <MetricCard
            label="Última decisão"
            value={latest ? decisionMeta(latest.decision).label : "sem decisão"}
            detail={latest ? `${formatDateTime(latest.decided_at)} · ${latest.reason}` : "Aguardando ciclo auditável"}
            tone={latest ? decisionMeta(latest.decision).tone : "warning"}
          />
          <MetricCard
            label="Ciclos carregados"
            value={String(decisions.length)}
            detail={activeDecision ? `Filtro ${decisionMeta(activeDecision).label}` : "Filtro atual: todas as decisões"}
            tone="neutral"
          />
        </MetricCardGroup>
        <Panel className="grid content-between gap-3">
          <span className="text-sm font-medium leading-tight text-muted-foreground">Distribuição do lote</span>
          <div className="grid grid-cols-2 gap-2">
            {decisionFilters.map((item) => (
              <StatusPill className="justify-between" key={item} tone={decisionMeta(item).tone}>
                {decisionMeta(item).shortLabel}
                <strong>{counts[item]}</strong>
              </StatusPill>
            ))}
          </div>
        </Panel>
      </section>

      <section className="flex flex-wrap items-center gap-2.5" aria-label="Filtros de decisão">
        <ListFilter size={18} aria-hidden="true" />
        <FilterChip active={!activeDecision} href="/decisions">
          Todas
        </FilterChip>
        {decisionFilters.map((item) => (
          <FilterChip active={activeDecision === item} href={`/decisions?decision=${item}`} key={item}>
            {decisionMeta(item).shortLabel}
          </FilterChip>
        ))}
      </section>

      {!result.ok ? <Notice tone="danger">API sem resposta: {result.error}</Notice> : null}

      <section className="grid gap-3" aria-label="Lista de decisões">
        {decisions.length === 0 ? (
          <EmptyState>Sem decisões para o filtro atual.</EmptyState>
        ) : (
          decisions.map((item) => <DecisionTimelineItem item={item} key={item.id} />)
        )}
      </section>

      <footer className="flex items-center justify-between gap-2.5 max-md:flex-col">
        <PagerLink disabled={offset === 0} href={pageHref(activeDecision, offset - pageSize)}>
          Anterior
        </PagerLink>
        <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Gauge size={16} aria-hidden="true" />
          {decisions.length === 0 ? "0" : `${offset + 1}-${offset + decisions.length}`}
        </span>
        <PagerLink disabled={decisions.length < pageSize} href={pageHref(activeDecision, offset + pageSize)}>
          Próxima
        </PagerLink>
      </footer>
    </AppShell>
  );
}

function DecisionTimelineItem({ item }: { item: Decision }) {
  const { meta, execution, checks, diagnostic } = explainDecision(item);
  const order = orderSummary(item.intended_order);

  return (
    <article className="rounded-xl border border-border bg-card p-5 shadow-sm md:p-6">
      <div className="grid gap-5">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-4 max-md:grid-cols-1">
          <div className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <StatusPill tone={meta.tone}>{meta.label}</StatusPill>
              <StatusPill tone={execution.tone}>
                <PackageCheck size={16} aria-hidden="true" />
                {execution.label}
              </StatusPill>
            </div>
            <h2 className="m-0 text-xl font-semibold leading-tight tracking-tight">{item.reason}</h2>
            <p className="m-0 mt-2 text-sm leading-6 text-muted-foreground">{meta.description}</p>
          </div>
          <div className="flex items-start justify-end max-md:justify-start">
            <StatusPill>
              <Clock3 size={16} aria-hidden="true" />
              {formatDateTime(item.decided_at)}
            </StatusPill>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-md:grid-cols-1">
          <StatPill label="Preço" value={formatMoney(readSignal(item, "close_price"))} />
          <StatPill label="RSI" value={plainValue(readSignal(item, "rsi"))} />
          <StatPill label="Exposição" value={percentValue(readPortfolio(item, "exposure_pct"))} />
          <StatPill label="Patrimônio" value={formatMoney(readPortfolio(item, "total_equity"))} />
        </div>

        <DecisionDiagnosticPanel diagnostic={diagnostic} checks={checks} />

        <details className="rounded-lg border border-border bg-muted/45 p-4">
          <summary className="flex cursor-pointer items-center justify-between gap-3 text-sm font-semibold text-foreground">
            <span>Ver dados técnicos e auditoria</span>
            <span className="text-xs font-medium text-muted-foreground">Detalhes</span>
          </summary>

          <div className="mt-4 grid gap-4">
            <section className="grid gap-3">
              <SectionTitle icon={<TrendingUp size={18} aria-hidden="true" />} title="Sinais de mercado" />
              <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-md:grid-cols-1">
                <StatPill label="Preço de fechamento" value={formatMoney(readSignal(item, "close_price"))} />
                <StatPill label="Breakout 20 candles" value={formatMoney(readSignal(item, "breakout_high_20"))} />
                <StatPill label="Volume atual" value={plainValue(readSignal(item, "current_volume"))} />
                <StatPill label="Volume médio" value={plainValue(readSignal(item, "average_volume"))} />
                <StatPill label="SMA 50" value={formatMoney(readSignal(item, "sma_50"))} />
                <StatPill label="SMA 200" value={formatMoney(readSignal(item, "sma_200"))} />
                <StatPill label="RSI" value={plainValue(readSignal(item, "rsi"))} />
                <StatPill label="ATR" value={plainValue(readSignal(item, "atr"))} />
              </div>
            </section>

            <section className="grid gap-3">
              <SectionTitle icon={<ShieldCheck size={18} aria-hidden="true" />} title="Risco e carteira" />
              <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-md:grid-cols-1">
                <StatPill label="Patrimônio total" value={formatMoney(readPortfolio(item, "total_equity"))} />
                <StatPill label="Exposição atual" value={percentValue(readPortfolio(item, "exposure_pct"))} />
                <StatPill label="Saldo USDT" value={formatMoney(readPortfolio(item, "usdt_balance"))} />
                <StatPill label="Saldo BTC" value={formatQuantity(readPortfolio(item, "btc_balance"))} />
                <StatPill label="Posição BTC" value={formatQuantity(readPortfolio(item, "position_quantity"))} />
                <StatPill label="Custo médio" value={formatMoney(readPortfolio(item, "position_average_cost"))} />
                <StatPill label="Exposição projetada" value={percentValue(readReason(item, "projected_exposure_pct"))} />
                <StatPill label="Limite de exposição" value={percentValue(readReason(item, "max_exposure_pct"))} />
              </div>
            </section>

            <section className="grid gap-3">
              <SectionTitle icon={<Wallet size={18} aria-hidden="true" />} title="Ordem" />
              {order.hasOrder ? (
                <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-md:grid-cols-1">
                  <StatPill label="Lado" value={order.side} />
                  <StatPill label="Tipo" value={order.type} />
                  <StatPill label="Quantidade BTC" value={formatQuantity(order.quantity)} />
                  <StatPill label="Valor USDT" value={formatMoney(order.quoteQuantity)} />
                  <StatPill label="Modo" value={order.mode} />
                  <StatPill label="Resultado" value={execution.label} />
                </div>
              ) : (
                <EmptyState>Nenhuma ordem pretendida neste ciclo.</EmptyState>
              )}
            </section>

            <section className="grid gap-3">
              <SectionTitle icon={<Bot size={18} aria-hidden="true" />} title="Auditoria" />
              <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
                <StatPill label="Bot run" value={shortId(item.bot_run_id)} />
                <StatPill label="Strategy" value={shortId(item.strategy_config_id)} />
                <StatPill label="Risk" value={shortId(item.risk_config_id)} />
                <StatPill label="Market" value={shortId(item.market_snapshot_id)} />
              </div>
              <JsonDetails
                icon={<Braces size={14} aria-hidden="true" />}
                label="Detalhes técnicos"
                value={JSON.stringify(
                  {
                    reason_payload: item.reason_payload,
                    indicators: item.indicators,
                    intended_order: item.intended_order,
                    execution_result: item.execution_result,
                    portfolio_state: item.portfolio_state,
                  },
                  null,
                  2,
                )}
              />
            </section>
          </div>
        </details>
      </div>
    </article>
  );
}

function DecisionDiagnosticPanel({
  diagnostic,
  checks,
}: {
  diagnostic: DecisionDiagnostic;
  checks: RuleCheck[];
}) {
  return (
    <section className="grid gap-4 rounded-lg border border-border bg-muted/45 p-4">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(280px,0.42fr)]">
        <div className="min-w-0">
          <StatusPill tone={diagnostic.tone}>{diagnostic.title}</StatusPill>
          <p className="m-0 mt-3 text-sm leading-6 text-foreground">{diagnostic.explanation}</p>
          <p className="m-0 mt-1 text-sm leading-6 text-muted-foreground">{diagnostic.orderExplanation}</p>
        </div>
        <div className="rounded-lg border border-border bg-background p-4">
          <span className="text-xs font-medium leading-5 text-muted-foreground">O que faltou para operar</span>
          <p className="m-0 mt-1 text-sm font-medium leading-6 text-foreground">{diagnostic.missingText}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2.5 max-xl:grid-cols-2 max-md:grid-cols-1" aria-label="Checklist de regras operacionais">
        {checks.map((check) => (
          <RuleCheckItem check={check} key={check.label} />
        ))}
      </div>
    </section>
  );
}

function RuleCheckItem({ check }: { check: RuleCheck }) {
  const meta = ruleStatusMeta(check.status);

  return (
    <div className="grid min-h-[92px] gap-2 rounded-lg border border-border bg-background p-3.5">
      <div className="flex items-start justify-between gap-2">
        <strong className="text-sm font-semibold leading-5 text-foreground">{check.label}</strong>
        <StatusPill className="min-h-7 px-2.5" tone={meta.tone}>
          {meta.icon}
          {meta.label}
        </StatusPill>
      </div>
      <p className="m-0 text-xs leading-5 text-muted-foreground">{check.detail}</p>
    </div>
  );
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <h3 className="m-0 flex items-center gap-2 text-sm font-semibold leading-6 text-foreground">
      <span className="inline-flex size-8 items-center justify-center rounded-md bg-primary/10 text-primary">
        {icon}
      </span>
      {title}
    </h3>
  );
}

function orderSummary(order: Record<string, unknown>) {
  return {
    hasOrder: hasEntries(order),
    side: order.side === "BUY" ? "Compra" : order.side === "SELL" ? "Venda" : plainValue(stringValue(order.side)),
    type: plainValue(stringValue(order.type)),
    quantity: stringValue(order.quantity),
    quoteQuantity: stringValue(order.quote_quantity),
    mode: [stringValue(order.execution_mode), stringValue(order.trading_mode)].filter(Boolean).join(" / ") || "-",
  };
}

function ruleStatusMeta(status: RuleStatus) {
  if (status === "pass") {
    return {
      label: "Passou",
      tone: "positive" as const,
      icon: <CircleCheck size={14} aria-hidden="true" />,
    };
  }
  if (status === "fail") {
    return {
      label: "Falhou",
      tone: "warning" as const,
      icon: <CircleAlert size={14} aria-hidden="true" />,
    };
  }
  return {
    label: "Sem dados",
    tone: "neutral" as const,
    icon: <CircleHelp size={14} aria-hidden="true" />,
  };
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function numericOffset(value: string | undefined) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 0;
}

function isDecisionFilter(value: string | undefined): value is DecisionValue {
  return decisionFilters.some((item) => item === value);
}

function shortId(value: string | null) {
  return value ? value.slice(0, 8) : "-";
}

function pageHref(decision: string | undefined, offset: number) {
  const query = new URLSearchParams();
  if (isDecisionFilter(decision)) query.set("decision", decision);
  if (offset > 0) query.set("offset", String(offset));
  const suffix = query.toString();
  return suffix ? `/decisions?${suffix}` : "/decisions";
}
