"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { postApi, type BotStatus } from "@/lib/api";

export async function initializeBot() {
  const result = await postApi<BotStatus>("/bot/initialize", {
    reason: "Estado inicial aguardando validação operacional",
  });
  finishBotCommand(result, "robô inicializado em modo pausado");
}

export async function pauseBot() {
  const result = await postApi<BotStatus>("/bot/pause", {
    reason: "Pausa manual pelo dashboard",
  });
  finishBotCommand(result, "robô pausado");
}

export async function resumeBot() {
  const result = await postApi<BotStatus>("/bot/resume", {
    reason: "Retomada manual pelo dashboard",
  });
  finishBotCommand(result, "robô retomado");
}

export async function emergencyStopBot(formData: FormData) {
  const confirmation = rawValue(formData, "confirmation").toUpperCase();
  if (confirmation !== "PARAR") {
    redirectWithError("digite PARAR para confirmar a parada de emergência");
  }

  const result = await postApi<BotStatus>("/bot/emergency-stop", {
    reason: textValue(formData, "reason", "Parada de emergência acionada pelo dashboard"),
  });
  finishBotCommand(result, "parada de emergência acionada");
}

function finishBotCommand<T>(result: Awaited<ReturnType<typeof postApi<T>>>, success: string) {
  if (!result.ok) redirectWithError(result.error);
  revalidatePath("/");
  redirect(`/?success=${encodeURIComponent(success)}`);
}

function rawValue(formData: FormData, field: string) {
  const value = formData.get(field);
  return typeof value === "string" ? value.trim() : "";
}

function textValue(formData: FormData, field: string, fallback: string) {
  return rawValue(formData, field) || fallback;
}

function redirectWithError(message: string): never {
  redirect(`/?error=${encodeURIComponent(message)}`);
}
