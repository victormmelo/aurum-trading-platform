"use server";

import { redirect } from "next/navigation";

import { postApi, type BacktestRun } from "@/lib/api";

export async function createBacktestRun(formData: FormData) {
  const name = formData.get("name")?.toString().trim();
  const start_date = formData.get("start_date")?.toString().trim();
  const end_date = formData.get("end_date")?.toString().trim();
  const initial_capital = formData.get("initial_capital")?.toString().trim();
  const fee_rate = formData.get("fee_rate")?.toString().trim() ?? "0.001";

  if (!name || !start_date || !end_date || !initial_capital) {
    redirect("/backtest?form=1&error=Preencha+todos+os+campos");
  }

  const payload = {
    name,
    start_date: new Date(start_date).toISOString(),
    end_date: new Date(end_date).toISOString(),
    initial_capital: Number(initial_capital),
    fee_rate: Number(fee_rate),
    signal_interval: "1h",
  };

  const result = await postApi<BacktestRun>("/backtest/run", payload);

  if (!result.ok) {
    redirect(`/backtest?form=1&error=${encodeURIComponent(result.error)}`);
  }

  redirect(`/backtest/${result.data.id}`);
}
