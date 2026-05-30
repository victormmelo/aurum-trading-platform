import { formatMoney, type Decision } from "@/lib/api";

export const decisionFilters = ["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"] as const;

export type DecisionValue = (typeof decisionFilters)[number];
export type DecisionTone = "positive" | "warning" | "neutral";
export type RuleStatus = "pass" | "fail" | "missing";
export type RuleCheck = {
  label: string;
  status: RuleStatus;
  detail: string;
};
export type DecisionDiagnostic = {
  title: string;
  explanation: string;
  orderExplanation: string;
  missingText: string;
  tone: DecisionTone;
};

export const decisionCopy: Record<
  DecisionValue,
  { label: string; shortLabel: string; description: string; tone: DecisionTone }
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

export function explainDecision(item: Decision) {
  const checks = decisionRuleChecks(item);
  const meta = decisionMeta(item.decision);

  return {
    meta,
    checks,
    diagnostic: decisionDiagnostic(item, checks),
    execution: executionSummary(item),
  };
}

export function decisionMeta(value: Decision["decision"] | undefined) {
  return value ? decisionCopy[value] ?? decisionCopy.NAO_OPERAR : {
    label: "sem decisão",
    shortLabel: "Sem decisão",
    description: "Aguardando ciclo auditável.",
    tone: "warning" as const,
  };
}

export function countByDecision(decisions: Decision[]) {
  return decisions.reduce<Record<DecisionValue, number>>(
    (acc, item) => {
      acc[item.decision] += 1;
      return acc;
    },
    { COMPRA: 0, VENDA: 0, MANTER_POSICAO: 0, NAO_OPERAR: 0 },
  );
}

export function executionSummary(item: Decision): { label: string; tone: DecisionTone | "danger" } {
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

export function decisionDiagnostic(item: Decision, checks: RuleCheck[]): DecisionDiagnostic {
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

  const meta = decisionMeta(item.decision);
  return {
    title: item.reason,
    explanation: meta.description,
    orderExplanation: hasEntries(item.intended_order)
      ? "Existe uma ordem pretendida associada a este ciclo."
      : "Nenhuma ordem pretendida foi registrada neste ciclo.",
    missingText,
    tone: item.decision === "NAO_OPERAR" ? "neutral" : meta.tone,
  };
}

export function decisionRuleChecks(item: Decision): RuleCheck[] {
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

export function readSignal(item: Decision, key: string) {
  const reasonValue = stringValue(item.reason_payload[key]);
  if (reasonValue) return reasonValue;

  const signal = recordValue(item.indicators.signal);
  const signalValue = stringValue(signal[key]);
  if (signalValue) return signalValue;

  const regime = recordValue(item.indicators.regime);
  return stringValue(regime[key]);
}

export function readReason(item: Decision, key: string) {
  return stringValue(item.reason_payload[key]);
}

export function readPortfolio(item: Decision, key: string) {
  return stringValue(item.portfolio_state[key]);
}

export function stringValue(value: unknown) {
  if (value == null || value === "") return "";
  return String(value);
}

export function plainValue(value: string | null | undefined) {
  return value == null || value === "" ? "-" : value;
}

export function percentValue(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

export function hasEntries(value: Record<string, unknown>) {
  return Object.keys(value).length > 0;
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

function numberValue(value: string | null | undefined) {
  if (value == null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function recordValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}
