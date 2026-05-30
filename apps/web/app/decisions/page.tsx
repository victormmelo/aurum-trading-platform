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

const decisionFilters = ["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"] as const;
const pageSize = 20;

type DecisionValue = (typeof decisionFilters)[number];
type SearchParams = Record<string, string | string[] | undefined>;
type RuleStatus = "pass" | "fail" | "missing";
type RuleCheck = {
  label: string;
  status: RuleStatus;
  detail: string;
};
type DecisionDiagnostic = {
  title: string;
  explanation: string;
  orderExplanation: string;
  missingText: string;
  tone: "positive" | "warning" | "neutral";
};

const decisionCopy: Record<
  DecisionValue,
  { label: string; shortLabel: string; description: string; tone: "positive" | "warning" | "neutral" }
> = {
  COMPRA: {
    label: "Comprar BTC",
    shortLabel: "Comprar",
    description: "O ciclo encontrou entrada válida e pretende abrir ou aumentar exposição.",
    tone: "positive",
  },
  VENDA: {
    label: "Vender posição",
    shortLabel: "Vender",
    description: "O ciclo encontrou saída válida para reduzir ou encerrar a posição.",
    tone: "warning",
  },
  MANTER_POSICAO: {
    label: "Manter posição",
    shortLabel: "Manter",
    description: "Existe posição aberta, mas as condições de saída ainda não foram atingidas.",
    tone: "neutral",
  },
  NAO_OPERAR: {
    label: "Não operar",
    shortLabel: "Não operar",
    description: "O ciclo não encontrou condições suficientes ou foi bloqueado por regra operacional.",
    tone: "neutral",
  },
};

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
  const meta = decisionMeta(item.decision);
  const execution = executionSummary(item);
  const order = orderSummary(item.intended_order);
  const checks = decisionRuleChecks(item);
  const diagnostic = decisionDiagnostic(item, checks);

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

function decisionMeta(value: Decision["decision"]) {
  return decisionCopy[value] ?? decisionCopy.NAO_OPERAR;
}

function countByDecision(decisions: Decision[]) {
  return decisions.reduce<Record<DecisionValue, number>>(
    (acc, item) => {
      acc[item.decision] += 1;
      return acc;
    },
    { COMPRA: 0, VENDA: 0, MANTER_POSICAO: 0, NAO_OPERAR: 0 },
  );
}

function executionSummary(item: Decision): { label: string; tone: "positive" | "warning" | "danger" | "neutral" } {
  const result = item.execution_result;
  const status = stringValue(result.status);
  const mode = stringValue(result.execution_mode);

  if (status === "error" || status === "failed" || result.error) return { label: "Erro na execução", tone: "danger" };
  if (status === "sent" || status === "filled" || status === "accepted") return { label: "Ordem enviada", tone: "positive" };
  if (hasEntries(item.intended_order)) {
    return {
      label: mode === "dry_run" ? "Ordem simulada" : "Ordem pretendida",
      tone: "warning",
    };
  }
  return { label: "Sem ordem", tone: "neutral" };
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

function decisionDiagnostic(item: Decision, checks: RuleCheck[]): DecisionDiagnostic {
  const code = stringValue(item.reason_payload.code);
  const failedChecks = checks.filter((check) => check.status === "fail");
  const missingChecks = checks.filter((check) => check.status === "missing");
  const gaps = failedChecks.length > 0 ? failedChecks : missingChecks;
  const missingText = gaps.length > 0
    ? `Para considerar compra, ${gaps.map((check) => check.detail).join(", ")}.`
    : "As regras principais estavam satisfeitas neste ciclo.";

  if (item.decision === "COMPRA") {
    return {
      title: "Entrada liberada",
      explanation: "O ciclo encontrou uma configuração válida para compra de BTC no escopo long-only.",
      orderExplanation: hasEntries(item.intended_order)
        ? "Uma ordem foi preparada para a etapa de execução."
        : "A decisão de compra foi registrada sem ordem pretendida neste retorno.",
      missingText,
      tone: "positive",
    };
  }

  if (code === "regime_blocked" || code === "price_below_sma_200" || code === "sma_50_below_sma_200") {
    return {
      title: "Regime bloqueou novas entradas",
      explanation: regimeExplanation(item),
      orderExplanation: "Nenhuma ordem foi criada porque a decisão foi bloqueada antes da etapa de execução.",
      missingText,
      tone: "warning",
    };
  }

  if (code === "no_breakout") {
    return {
      title: "Rompimento ainda não confirmado",
      explanation: `O ${item.symbol} ainda não fechou acima da máxima dos últimos 20 candles.`,
      orderExplanation: "Sem rompimento confirmado, o robô não cria ordem de compra.",
      missingText,
      tone: "warning",
    };
  }

  if (code === "weak_volume") {
    return {
      title: "Volume insuficiente",
      explanation: "O rompimento não teve volume acima da média recente, então a entrada foi descartada.",
      orderExplanation: "Sem confirmação por volume, nenhuma ordem foi criada neste ciclo.",
      missingText,
      tone: "warning",
    };
  }

  if (code === "rsi_out_of_range") {
    return {
      title: "RSI fora da faixa operacional",
      explanation: "O RSI ficou fora da faixa configurada para novas entradas.",
      orderExplanation: "A regra de momentum bloqueou a criação de ordem neste ciclo.",
      missingText,
      tone: "warning",
    };
  }

  if (code === "bot_not_running") {
    return {
      title: "Robô sem execução ativa",
      explanation: "O ciclo foi registrado, mas o robô não estava em estado operacional para enviar decisões ao mercado.",
      orderExplanation: "Nenhuma ordem é criada enquanto o robô estiver pausado ou em parada operacional.",
      missingText,
      tone: "neutral",
    };
  }

  if (code === "missing_active_config") {
    return {
      title: "Configuração ativa ausente",
      explanation: "O ciclo não encontrou configuração ativa de estratégia ou risco para avaliar uma operação.",
      orderExplanation: "Sem configuração ativa, a etapa de ordem permanece bloqueada.",
      missingText,
      tone: "neutral",
    };
  }

  return {
    title: item.reason,
    explanation: decisionMeta(item.decision).description,
    orderExplanation: hasEntries(item.intended_order)
      ? "Existe uma ordem pretendida associada a este ciclo."
      : "Nenhuma ordem pretendida foi registrada neste ciclo.",
    missingText,
    tone: item.decision === "NAO_OPERAR" ? "neutral" : decisionMeta(item.decision).tone,
  };
}

function regimeExplanation(item: Decision) {
  const close = readSignal(item, "close_price");
  const sma200 = readSignal(item, "sma_200");
  const sma50 = readSignal(item, "sma_50");
  const closeValue = numberValue(close);
  const sma200Value = numberValue(sma200);
  const sma50Value = numberValue(sma50);

  if (closeValue != null && sma200Value != null && closeValue <= sma200Value) {
    return `O ${item.symbol} fechou em ${formatMoney(close)}, abaixo da SMA 200 de ${formatMoney(sma200)}, então o robô não abriu nova posição.`;
  }

  if (sma50Value != null && sma200Value != null && sma50Value <= sma200Value) {
    return `A SMA 50 está em ${formatMoney(sma50)}, abaixo da SMA 200 de ${formatMoney(sma200)}, indicando tendência insuficiente para novas entradas.`;
  }

  return "O regime de mercado não atendeu às regras long-only configuradas, então novas entradas foram bloqueadas.";
}

function decisionRuleChecks(item: Decision): RuleCheck[] {
  const close = readSignal(item, "close_price");
  const sma200 = readSignal(item, "sma_200");
  const sma50 = readSignal(item, "sma_50");
  const breakout = readSignal(item, "breakout_high_20");
  const currentVolume = readSignal(item, "current_volume");
  const averageVolume = readSignal(item, "average_volume");
  const rsi = readSignal(item, "rsi");
  const minRsi = stringValue(item.reason_payload.min_rsi) || "50";
  const maxRsi = stringValue(item.reason_payload.max_rsi) || "75";

  const priceAboveSma = compareRule(close, sma200, (left, right) => left > right);
  const smaTrend = compareRule(sma50, sma200, (left, right) => left > right);
  const breakoutRule = compareRule(close, breakout, (left, right) => left > right);
  const volumeRule = compareRule(currentVolume, averageVolume, (left, right) => left > right);
  const rsiRule = rangeRule(rsi, minRsi, maxRsi);
  const regimeRule = compositeRule([priceAboveSma, smaTrend]);

  return [
    {
      label: "Regime long-only",
      status: regimeRule,
      detail: ruleDetail(
        regimeRule,
        "o regime precisaria ficar positivo para novas entradas",
        "preço e tendência permitem avaliar entrada long-only",
        "faltam médias para validar o regime",
      ),
    },
    {
      label: "Preço acima da SMA 200",
      status: priceAboveSma,
      detail: ruleDetail(
        priceAboveSma,
        `o preço precisaria voltar acima da SMA 200 de ${formatMoney(sma200)}`,
        `preço ${formatMoney(close)} acima da SMA 200 de ${formatMoney(sma200)}`,
        "faltam preço ou SMA 200 para validar a regra",
      ),
    },
    {
      label: "SMA 50 acima da SMA 200",
      status: smaTrend,
      detail: ruleDetail(
        smaTrend,
        `a SMA 50 precisaria superar a SMA 200 de ${formatMoney(sma200)}`,
        `SMA 50 ${formatMoney(sma50)} acima da SMA 200 de ${formatMoney(sma200)}`,
        "faltam médias para validar a tendência",
      ),
    },
    {
      label: "Rompimento 20 candles",
      status: breakoutRule,
      detail: ruleDetail(
        breakoutRule,
        `o preço precisaria romper ${formatMoney(breakout)}`,
        `preço ${formatMoney(close)} acima do rompimento de ${formatMoney(breakout)}`,
        "falta a máxima de 20 candles para validar rompimento",
      ),
    },
    {
      label: "Volume acima da média",
      status: volumeRule,
      detail: ruleDetail(
        volumeRule,
        "o volume atual precisaria ficar acima da média recente",
        "volume atual acima da média recente",
        "faltam dados de volume para validar confirmação",
      ),
    },
    {
      label: "RSI dentro da faixa",
      status: rsiRule,
      detail: ruleDetail(
        rsiRule,
        `o RSI precisaria ficar entre ${minRsi} e ${maxRsi}`,
        `RSI ${plainValue(rsi)} dentro da faixa ${minRsi}-${maxRsi}`,
        "falta RSI para validar momentum",
      ),
    },
  ];
}

function compareRule(left: string, right: string, predicate: (left: number, right: number) => boolean): RuleStatus {
  const leftValue = numberValue(left);
  const rightValue = numberValue(right);
  if (leftValue == null || rightValue == null) return "missing";
  return predicate(leftValue, rightValue) ? "pass" : "fail";
}

function rangeRule(value: string, min: string, max: string): RuleStatus {
  const parsed = numberValue(value);
  const parsedMin = numberValue(min);
  const parsedMax = numberValue(max);
  if (parsed == null || parsedMin == null || parsedMax == null) return "missing";
  return parsed >= parsedMin && parsed <= parsedMax ? "pass" : "fail";
}

function compositeRule(statuses: RuleStatus[]): RuleStatus {
  if (statuses.some((status) => status === "fail")) return "fail";
  if (statuses.some((status) => status === "missing")) return "missing";
  return "pass";
}

function ruleDetail(status: RuleStatus, fail: string, pass: string, missing: string) {
  if (status === "pass") return pass;
  if (status === "fail") return fail;
  return missing;
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

function numberValue(value: string | null | undefined) {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function readSignal(item: Decision, key: string) {
  const reasonValue = stringValue(item.reason_payload[key]);
  if (reasonValue) return reasonValue;

  const signal = recordValue(item.indicators.signal);
  const signalValue = stringValue(signal[key]);
  if (signalValue) return signalValue;

  const regime = recordValue(item.indicators.regime);
  return stringValue(regime[key]);
}

function readReason(item: Decision, key: string) {
  return stringValue(item.reason_payload[key]);
}

function readPortfolio(item: Decision, key: string) {
  return stringValue(item.portfolio_state[key]);
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function stringValue(value: unknown) {
  if (value == null || value === "") return "";
  return String(value);
}

function plainValue(value: string | null | undefined) {
  return value == null || value === "" ? "-" : value;
}

function percentValue(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

function hasEntries(value: Record<string, unknown>) {
  return Object.keys(value).length > 0;
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
