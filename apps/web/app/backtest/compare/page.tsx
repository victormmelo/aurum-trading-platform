import { BarChart2, TrendingUp } from "lucide-react";
import Link from "next/link";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { BacktestCompareChart } from "@/components/backtest-compare-chart";
import {
  EmptyState,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  StatusPill,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui";
import {
  fetchApi,
  formatMoney,
  type BacktestCompare,
  type BacktestCompareItem,
  type BacktestRunsList,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

function single(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function fmtPct(v: string | null | undefined, sign = true): string {
  if (!v) return "-";
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  const prefix = sign && n >= 0 ? "+" : "";
  return `${prefix}${n.toFixed(2)}%`;
}

function metricTone(v: string | null | undefined): "positive" | "danger" | "neutral" {
  if (!v) return "neutral";
  const n = Number(v);
  if (n > 0) return "positive";
  if (n < 0) return "danger";
  return "neutral";
}

const SERIES_COLORS = ["#107e59", "#2563eb", "#dc2626", "#d97706", "#7c3aed"];

function bestIdx(values: (string | null | undefined)[], higher = true): number {
  let best = -1;
  let bestVal = higher ? -Infinity : Infinity;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (!v) continue;
    const n = Number(v);
    if (!Number.isFinite(n)) continue;
    if (higher ? n > bestVal : n < bestVal) {
      bestVal = n;
      best = i;
    }
  }
  return best;
}

function rankByRisk(runs: BacktestCompareItem[]): BacktestCompareItem[] {
  return [...runs].sort((a, b) => {
    const sa = Number(a.metrics?.sharpe_ratio ?? 0);
    const sb = Number(b.metrics?.sharpe_ratio ?? 0);
    return sb - sa;
  });
}

export default async function BacktestComparePage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const sp = searchParams ? await searchParams : {};
  const rawIds = single(sp.ids) ?? "";
  const selectedIds = rawIds
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const [runsResult, compareResult] = await Promise.all([
    fetchApi<BacktestRunsList>("/backtest/"),
    selectedIds.length >= 2
      ? fetchApi<BacktestCompare>(`/backtest/compare?ids=${selectedIds.join(",")}`)
      : Promise.resolve(null),
  ]);

  const allRuns = runsResult.ok ? runsResult.data.runs : [];
  const compareRuns: BacktestCompareItem[] =
    compareResult && compareResult.ok ? compareResult.data.runs : [];

  const ranked = rankByRisk(compareRuns);

  const metricRows: {
    label: string;
    key: keyof NonNullable<BacktestCompareItem["metrics"]>;
    format: (v: string | null | undefined) => string;
    higherIsBetter: boolean;
  }[] = [
    {
      label: "Retorno Total",
      key: "total_return_pct",
      format: (v) => fmtPct(v),
      higherIsBetter: true,
    },
    {
      label: "Capital Final",
      key: "final_capital",
      format: (v) => formatMoney(v),
      higherIsBetter: true,
    },
    {
      label: "Drawdown Máx",
      key: "max_drawdown_pct",
      format: (v) => fmtPct(v, false),
      higherIsBetter: false,
    },
    {
      label: "Win Rate",
      key: "win_rate_pct",
      format: (v) => (v ? `${Number(v).toFixed(1)}%` : "-"),
      higherIsBetter: true,
    },
    {
      label: "Profit Factor",
      key: "profit_factor",
      format: (v) => (v ? Number(v).toFixed(2) : "-"),
      higherIsBetter: true,
    },
    {
      label: "Sharpe Ratio",
      key: "sharpe_ratio",
      format: (v) => (v ? Number(v).toFixed(2) : "-"),
      higherIsBetter: true,
    },
    {
      label: "Total de Trades",
      key: "total_trades",
      format: (v) => (v ? String(v) : "-"),
      higherIsBetter: true,
    },
    {
      label: "BTC Buy & Hold",
      key: "btc_buy_hold_return_pct",
      format: (v) => fmtPct(v),
      higherIsBetter: true,
    },
  ];

  return (
    <AppShell navItems={navItems} activeLabel="Backtest">
      <PageHeader
        eyebrow="Backtest"
        title="Comparar Simulações"
        description="Selecione duas ou mais simulações para comparar métricas e equity curves lado a lado."
        trailing={
          <Link
            href="/backtest"
            className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-4 text-sm font-medium text-muted-foreground hover:bg-muted"
          >
            ← Voltar
          </Link>
        }
      />

      {!runsResult.ok && (
        <Notice tone="danger">Erro ao carregar simulações: {runsResult.error}</Notice>
      )}

      <Panel>
        <PanelHeader eyebrow="Seleção" title="Selecionar Simulações" icon={<BarChart2 size={16} />} />
        {allRuns.filter((r) => r.status === "completed").length < 2 ? (
          <EmptyState>
            Você precisa de ao menos duas simulações concluídas para comparar.
          </EmptyState>
        ) : (
          <form method="GET" action="/backtest/compare" className="grid gap-4">
            <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
              {allRuns
                .filter((r) => r.status === "completed")
                .map((run) => (
                  <label
                    key={run.id}
                    className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-background p-3 hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      name="ids"
                      value={run.id}
                      defaultChecked={selectedIds.includes(run.id)}
                      className="size-4 accent-primary"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">
                        {run.name}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {run.metrics ? fmtPct(run.metrics.total_return_pct) : "—"} •{" "}
                        {new Date(run.start_date).toLocaleDateString("pt-BR")} →{" "}
                        {new Date(run.end_date).toLocaleDateString("pt-BR")}
                      </p>
                    </div>
                  </label>
                ))}
            </div>
            <div>
              <button
                type="submit"
                className="inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Comparar
              </button>
            </div>
          </form>
        )}
      </Panel>

      {selectedIds.length >= 2 && compareResult && !compareResult.ok && (
        <Notice tone="danger">
          Erro ao carregar comparativo: {compareResult.error}
        </Notice>
      )}

      {compareRuns.length >= 2 && (
        <>
          <MetricCardGroup>
            {compareRuns.map((run, i) => (
              <MetricCard
                key={run.id}
                label={run.name}
                value={fmtPct(run.metrics?.total_return_pct)}
                tone={metricTone(run.metrics?.total_return_pct)}
                detail={`Sharpe: ${run.metrics?.sharpe_ratio ? Number(run.metrics.sharpe_ratio).toFixed(2) : "N/A"} • DD: ${fmtPct(run.metrics?.max_drawdown_pct, false)}`}
              />
            ))}
          </MetricCardGroup>

          <Panel>
            <PanelHeader eyebrow="Comparativo" title="Métricas Comparativas" icon={<BarChart2 size={16} />} />
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 pr-4 text-left font-medium text-muted-foreground">
                      Métrica
                    </th>
                    {compareRuns.map((run, i) => (
                      <th
                        key={run.id}
                        className="py-2 px-3 text-right font-medium"
                        style={{ color: SERIES_COLORS[i % SERIES_COLORS.length] }}
                      >
                        {run.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metricRows.map((row) => {
                    const values = compareRuns.map((r) =>
                      r.metrics ? String(r.metrics[row.key] ?? "") : null,
                    );
                    const best = bestIdx(values, row.higherIsBetter);
                    return (
                      <tr key={row.key} className="border-b border-border/50">
                        <td className="py-2 pr-4 text-muted-foreground">{row.label}</td>
                        {compareRuns.map((run, i) => {
                          const val = run.metrics
                            ? row.format(String(run.metrics[row.key] ?? ""))
                            : "-";
                          const isBest = i === best;
                          return (
                            <td
                              key={run.id}
                              className={`py-2 px-3 text-right tabular-nums ${
                                isBest
                                  ? "font-semibold text-[var(--color-success)]"
                                  : "text-foreground"
                              }`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel>
            <PanelHeader eyebrow="Análise" title="Equity Curves" icon={<TrendingUp size={16} />} />
            <BacktestCompareChart runs={compareRuns} />
          </Panel>

          <Panel>
            <PanelHeader eyebrow="Ranking" title="Ranking por Risco Ajustado" icon={<BarChart2 size={16} />} />
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Posição</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead className="text-right">Retorno</TableHead>
                  <TableHead className="text-right">Sharpe</TableHead>
                  <TableHead className="text-right">Drawdown</TableHead>
                  <TableHead className="text-right">Win Rate</TableHead>
                  <TableHead className="text-right">Trades</TableHead>
                  <TableHead>Resultado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ranked.map((run, position) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-semibold tabular-nums text-muted-foreground">
                      #{position + 1}
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/backtest/${run.id}`}
                        className="font-medium text-foreground hover:text-primary hover:underline"
                      >
                        {run.name}
                      </Link>
                    </TableCell>
                    <TableCell
                      className={`text-right tabular-nums font-medium ${
                        metricTone(run.metrics?.total_return_pct) === "positive"
                          ? "text-[var(--color-success)]"
                          : metricTone(run.metrics?.total_return_pct) === "danger"
                            ? "text-[var(--color-destructive)]"
                            : ""
                      }`}
                    >
                      {fmtPct(run.metrics?.total_return_pct)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {run.metrics?.sharpe_ratio
                        ? Number(run.metrics.sharpe_ratio).toFixed(2)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-[var(--color-warning)]">
                      {fmtPct(run.metrics?.max_drawdown_pct, false)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {run.metrics
                        ? `${Number(run.metrics.win_rate_pct).toFixed(1)}%`
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {run.metrics?.total_trades ?? "-"}
                    </TableCell>
                    <TableCell>
                      <StatusPill
                        tone={
                          metricTone(run.metrics?.total_return_pct) === "positive"
                            ? "positive"
                            : metricTone(run.metrics?.total_return_pct) === "danger"
                              ? "danger"
                              : "neutral"
                        }
                      >
                        {fmtPct(run.metrics?.total_return_pct)}
                      </StatusPill>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Panel>
        </>
      )}

      {selectedIds.length >= 2 &&
        compareResult &&
        compareResult.ok &&
        compareRuns.length < 2 && (
          <Notice tone="warning">
            Nenhuma simulação encontrada para os IDs selecionados.
          </Notice>
        )}
    </AppShell>
  );
}
