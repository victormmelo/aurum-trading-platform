import { BarChart2, Play, X } from "lucide-react";
import Link from "next/link";

import { createBacktestRun } from "@/app/backtest/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  EmptyState,
  LabeledInput,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PrimaryButton,
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
  formatDateTime,
  formatMoney,
  type BacktestRunsList,
  type BacktestRun,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

function single(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function fmtPct(v: string | null | undefined): string {
  if (!v) return "-";
  const n = Number(v);
  if (!Number.isFinite(n)) return "-";
  const sign = n >= 0 ? "+" : "";
  return `${sign}${n.toFixed(2)}%`;
}

function returnTone(v: string | null | undefined): "positive" | "danger" | "neutral" {
  if (!v) return "neutral";
  const n = Number(v);
  if (n > 0) return "positive";
  if (n < 0) return "danger";
  return "neutral";
}

function statusTone(status: BacktestRun["status"]): "positive" | "warning" | "neutral" | "danger" {
  if (status === "completed") return "positive";
  if (status === "failed") return "danger";
  if (status === "running") return "warning";
  return "neutral";
}

function statusLabel(status: BacktestRun["status"]): string {
  const map: Record<string, string> = {
    pending: "Aguardando",
    running: "Executando",
    completed: "Concluído",
    failed: "Falhou",
  };
  return map[status] ?? status;
}

export default async function BacktestPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const showForm = single(params.form) === "1";
  const errorMsg = single(params.error);

  const runsResult = await fetchApi<BacktestRunsList>("/backtest/");
  const runs = runsResult.ok ? runsResult.data.runs : [];

  return (
    <AppShell navItems={navItems} activeLabel="Backtest">
      <PageHeader
        eyebrow="Backtest"
        title="Simulações de Backtest"
        description="Simule a estratégia sobre dados históricos do BTCUSDT e compare resultados."
        trailing={
          showForm ? (
            <Link
              href="/backtest"
              className="inline-flex h-10 items-center gap-2 rounded-md border border-border px-4 text-sm font-medium text-muted-foreground hover:bg-muted"
            >
              <X size={14} />
              Cancelar
            </Link>
          ) : (
            <Link
              href="/backtest?form=1"
              className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Play size={14} />
              Nova Simulação
            </Link>
          )
        }
      />

      {!runsResult.ok && (
        <Notice tone="danger">Erro ao carregar simulações: {runsResult.error}</Notice>
      )}

      {showForm && (
        <Panel>
          <PanelHeader eyebrow="Nova simulação" title="Configurar Simulação" icon={<BarChart2 size={16} />} />
          {errorMsg && <Notice tone="danger">{decodeURIComponent(errorMsg)}</Notice>}
          <form action={createBacktestRun} className="grid gap-4 md:grid-cols-2">
            <LabeledInput
              label="Nome da simulação"
              name="name"
              placeholder="Ex: Breakout 2024-2025 taxa 0.1%"
              required
            />
            <LabeledInput
              label="Taxa de corretagem"
              name="fee_rate"
              type="number"
              step="0.0001"
              min="0"
              max="1"
              defaultValue="0.001"
              placeholder="0.001"
            />
            <LabeledInput
              label="Data de início"
              name="start_date"
              type="date"
              required
            />
            <LabeledInput
              label="Data de fim"
              name="end_date"
              type="date"
              required
            />
            <div className="md:col-span-2">
              <LabeledInput
                label="Capital inicial (USDT)"
                name="initial_capital"
                type="number"
                min="10"
                step="0.01"
                defaultValue="10000"
                placeholder="10000"
                required
              />
            </div>
            <div className="flex gap-3 md:col-span-2">
              <PrimaryButton type="submit">
                <Play size={14} />
                Executar Simulação
              </PrimaryButton>
            </div>
          </form>
        </Panel>
      )}

      <Panel>
        <PanelHeader
          eyebrow="Histórico"
          title={`${runs.length} simulação${runs.length !== 1 ? "ões" : ""}`}
          icon={<BarChart2 size={16} />}
        />
        {runs.length === 0 ? (
          <EmptyState>
            Nenhuma simulação — clique em &quot;Nova Simulação&quot; para criar sua primeira simulação de backtest.
          </EmptyState>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nome</TableHead>
                <TableHead>Período</TableHead>
                <TableHead className="text-right">Capital Inicial</TableHead>
                <TableHead className="text-right">Retorno</TableHead>
                <TableHead className="text-right">Capital Final</TableHead>
                <TableHead className="text-right">Drawdown Máx</TableHead>
                <TableHead className="text-right">Win Rate</TableHead>
                <TableHead className="text-right">Trades</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>
                    <Link
                      href={`/backtest/${run.id}`}
                      className="font-medium text-foreground hover:text-primary hover:underline"
                    >
                      {run.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDateTime(run.start_date)} →{" "}
                    {formatDateTime(run.end_date)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(run.initial_capital)}
                  </TableCell>
                  <TableCell
                    className={`text-right tabular-nums font-medium ${
                      run.metrics
                        ? returnTone(run.metrics.total_return_pct) === "positive"
                          ? "text-[var(--color-success)]"
                          : returnTone(run.metrics.total_return_pct) === "danger"
                            ? "text-[var(--color-destructive)]"
                            : ""
                        : ""
                    }`}
                  >
                    {fmtPct(run.metrics?.total_return_pct)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(run.metrics?.final_capital)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-[var(--color-warning)]">
                    {fmtPct(run.metrics?.max_drawdown_pct)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {run.metrics ? `${Number(run.metrics.win_rate_pct).toFixed(1)}%` : "-"}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {run.metrics?.total_trades ?? "-"}
                  </TableCell>
                  <TableCell>
                    <StatusPill tone={statusTone(run.status)}>
                      {statusLabel(run.status)}
                    </StatusPill>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Panel>

      {runs.length >= 2 && (
        <div className="flex justify-end">
          <Link
            href={`/backtest/compare?ids=${runs
              .slice(0, 5)
              .map((r) => r.id)
              .join(",")}`}
            className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-4 text-sm font-medium text-muted-foreground hover:bg-muted"
          >
            Comparar simulações
          </Link>
        </div>
      )}
    </AppShell>
  );
}
