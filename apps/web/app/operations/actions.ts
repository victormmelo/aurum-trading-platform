"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  postApi,
  type ManualOrderResponse,
  type OrderReconciliationResponse,
} from "@/lib/api";

export async function submitManualOrder(formData: FormData) {
  const side = rawValue(formData, "side").toUpperCase();
  if (side !== "BUY" && side !== "SELL") redirectWithError("lado da ordem invalido");

  const payload = {
    side,
    quantity: nullableText(formData, "quantity"),
    quote_quantity: nullableText(formData, "quote_quantity"),
    reason: textValue(formData, "reason", "Ordem manual pelo dashboard"),
    actor_id: textValue(formData, "actor_id", "dashboard"),
  };

  const result = await postApi<ManualOrderResponse>("/operations/manual-order", payload);
  if (!result.ok) redirectWithError(result.error);

  revalidatePath("/");
  revalidatePath("/operations");
  redirect(`/operations?success=ordem ${result.data.order.status.toLowerCase()} registrada`);
}

export async function reconcileOrders() {
  const result = await postApi<OrderReconciliationResponse>("/operations/reconcile");
  if (!result.ok) redirectWithError(result.error);

  revalidatePath("/");
  revalidatePath("/operations");
  redirect(`/operations?success=${result.data.reconciled_orders.length} ordens reconciliadas`);
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

function redirectWithError(message: string): never {
  redirect(`/operations?error=${encodeURIComponent(message)}`);
}
