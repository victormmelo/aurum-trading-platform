"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  postApi,
  type McpScope,
  type McpToken,
  type McpTokenCreateResponse,
} from "@/lib/api";

const allowedScopes = [
  "read:market",
  "read:portfolio",
  "read:trades",
  "read:decisions",
  "read:config",
  "read:reports",
] as const satisfies readonly McpScope[];

export async function createMcpToken(formData: FormData) {
  const scopes = formData
    .getAll("scopes")
    .filter((scope): scope is McpScope => typeof scope === "string" && isMcpScope(scope));
  if (scopes.length === 0) redirectWithError("selecione ao menos um escopo");

  const payload = {
    name: textValue(formData, "name", "Aurum agent"),
    agent_name: nullableText(formData, "agent_name"),
    scopes,
    expires_at: nullableText(formData, "expires_at"),
  };

  const result = await postApi<McpTokenCreateResponse>("/mcp/tokens", payload);
  if (!result.ok) redirectWithError(result.error);
  revalidatePath("/mcp");
  redirect(`/mcp?success=token criado&token=${encodeURIComponent(result.data.token)}`);
}

export async function revokeMcpToken(formData: FormData) {
  const id = textValue(formData, "id", "");
  if (!id) redirectWithError("token invalido");
  const result = await postApi<McpToken>(`/mcp/tokens/${id}/revoke`);
  if (!result.ok) redirectWithError(result.error);
  revalidatePath("/mcp");
  redirect("/mcp?success=token revogado");
}

function isMcpScope(value: string): value is McpScope {
  return allowedScopes.some((scope) => scope === value);
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
  redirect(`/mcp?error=${encodeURIComponent(message)}`);
}
