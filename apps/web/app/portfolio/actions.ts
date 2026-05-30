"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { postApi, type PortfolioReconciliationResponse } from "@/lib/api";

export async function reconcilePortfolio() {
  const result = await postApi<PortfolioReconciliationResponse>("/portfolio/reconcile");
  if (!result.ok) redirectWithError(result.error);

  revalidatePath("/");
  revalidatePath("/portfolio");
  redirect("/portfolio?success=carteira reconciliada pela Binance Testnet");
}

function redirectWithError(message: string): never {
  redirect(`/portfolio?error=${encodeURIComponent(message)}`);
}
