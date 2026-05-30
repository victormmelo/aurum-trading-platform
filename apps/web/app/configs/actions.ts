"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { postApi, type RiskConfigItem, type StrategyConfigItem } from "@/lib/api";

type ConfigKind = "strategy" | "risk";

export async function activateStrategyConfig(formData: FormData) {
  await activateConfig("strategy", formData);
}

export async function activateRiskConfig(formData: FormData) {
  await activateConfig("risk", formData);
}

export async function createStrategyConfig(formData: FormData) {
  const payload = {
    version: requiredInteger(formData, "version"),
    name: textValue(formData, "name", "breakout_trend_v1"),
    signal_timeframe: textValue(formData, "signal_timeframe", "1h"),
    regime_timeframe_primary: textValue(formData, "regime_timeframe_primary", "4h"),
    regime_timeframe_secondary: textValue(formData, "regime_timeframe_secondary", "1d"),
    parameters: parseJsonObject(formData, "parameters"),
    created_by: textValue(formData, "created_by", "operator"),
  };

  const result = await postApi<StrategyConfigItem>("/configs/strategy", payload);
  finishMutation(result, "configuracao de estrategia criada");
}

export async function createRiskConfig(formData: FormData) {
  const payload = {
    version: requiredInteger(formData, "version"),
    name: textValue(formData, "name", "mvp_risk_v1"),
    risk_per_trade_pct: nullableText(formData, "risk_per_trade_pct"),
    daily_loss_limit_pct: nullableText(formData, "daily_loss_limit_pct"),
    max_exposure_pct: nullableText(formData, "max_exposure_pct"),
    parameters: parseJsonObject(formData, "parameters"),
    created_by: textValue(formData, "created_by", "operator"),
  };

  const result = await postApi<RiskConfigItem>("/configs/risk", payload);
  finishMutation(result, "configuracao de risco criada");
}

export async function createGuidedRobotConfig(formData: FormData) {
  const strategyVersion = requiredInteger(formData, "strategy_version");
  const riskVersion = requiredInteger(formData, "risk_version");

  const strategyPayload = {
    version: strategyVersion,
    name: `Rompimento com tendencia v${strategyVersion}`,
    signal_timeframe: textValue(formData, "decision_period", "1h"),
    regime_timeframe_primary: textValue(formData, "trend_confirmation", "4h"),
    regime_timeframe_secondary: textValue(formData, "major_trend", "1d"),
    parameters: {},
    created_by: "operator",
  };
  const riskPayload = {
    version: riskVersion,
    name: `Risco conservador v${riskVersion}`,
    risk_per_trade_pct: nullableText(formData, "risk_per_trade_pct") ?? "1",
    daily_loss_limit_pct: nullableText(formData, "daily_loss_limit_pct") ?? "2",
    max_exposure_pct: nullableText(formData, "max_exposure_pct") ?? "50",
    parameters: {},
    created_by: "operator",
  };

  const strategyResult = await postApi<StrategyConfigItem>("/configs/strategy", strategyPayload);
  if (!strategyResult.ok) redirectWithError(strategyResult.error);

  const riskResult = await postApi<RiskConfigItem>("/configs/risk", riskPayload);
  if (!riskResult.ok) redirectWithError(riskResult.error);

  const strategyActivation = await postApi<StrategyConfigItem>(
    `/configs/strategy/${strategyResult.data.id}/activate`,
  );
  if (!strategyActivation.ok) redirectWithError(strategyActivation.error);

  const riskActivation = await postApi<RiskConfigItem>(
    `/configs/risk/${riskResult.data.id}/activate`,
  );
  finishMutation(riskActivation, "robo configurado com estrategia e risco ativos");
}

async function activateConfig(kind: ConfigKind, formData: FormData) {
  const id = textValue(formData, "id", "");
  if (!id) redirectWithError("configuracao invalida");

  const result = await postApi<StrategyConfigItem | RiskConfigItem>(`/configs/${kind}/${id}/activate`);
  finishMutation(result, "configuracao ativada");
}

function finishMutation<T>(result: Awaited<ReturnType<typeof postApi<T>>>, success: string) {
  if (!result.ok) redirectWithError(result.error);
  revalidatePath("/configs");
  redirect(`/configs?success=${encodeURIComponent(success)}`);
}

function redirectWithError(message: string): never {
  redirect(`/configs?error=${encodeURIComponent(message)}`);
}

function rawValue(formData: FormData, field: string) {
  const value = formData.get(field);
  return typeof value === "string" ? value.trim() : "";
}

function textValue(formData: FormData, field: string, fallback: string) {
  return rawValue(formData, field) || fallback;
}

function nullableText(formData: FormData, field: string) {
  return rawValue(formData, field) || null;
}

function requiredInteger(formData: FormData, field: string) {
  const value = Number(rawValue(formData, field));
  if (!Number.isInteger(value) || value < 1) redirectWithError(`${field} invalido`);
  return value;
}

function parseJsonObject(formData: FormData, field: string) {
  const raw = rawValue(formData, field);
  if (!raw) return {};

  try {
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
  } catch {
    redirectWithError(`${field} precisa ser um objeto JSON valido`);
  }

  redirectWithError(`${field} precisa ser um objeto JSON valido`);
}
