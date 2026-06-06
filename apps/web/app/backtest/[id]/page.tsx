import {
  BarChart2,
  Download,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { notFound } from "next/navigation";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { BacktestEquityChart } from "@/components/backtest-equity-chart";
import { BacktestPoller } from "@/components/backtest-poller";
import {
  EmptyState,
  FilterChip,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PagerLink,
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
  formatQuantity,
  publicApiUrl,
  type BacktestRunDetail,
  type BacktestTradesPage,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;
type TradeFilter = "all" | "winner" | "loser";

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

function exitReasonLabel(reason: string): string {
  const map: Record<string, string> = {
    atr_stop: "ATR Stop",
    trailing_stop: "Trailing Stop",
    trend_exit_price_below_sma_200: "Preço abaixo SMA-200",
    trend_exit_sma_cross: "Cruzamento SMA",
    end_of_period: "Fim do período",
  };
  return map[reason] ?? reason;
}

function buildMonthlyPerformance(trades: { exit_time: string; pnl_usd: string }[]) {
  const monthly: Record<string, number> = {};
  for (const t of trades) {
    const d = new Date(t.exit_time);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    monthly[key] = (monthly[key] ?? 0) + Number(t.pnl_usd);
  }
  return monthly;
}

function buildPnlBuckets(trades: { return_pct: string }[], buckets = 10) {
  const values = trades.map((t) => Number(t.return_pct)).filter(Number.isFinite);
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = range / buckets;
  const counts = Array.from({ length: buckets }, (_, i) => ({
    label: `${(min + i * step).toFixed(1)}%`,
    count: 0,
    start: min + i * step,
    end: min + (i + 1) * step,
  }));
  for (const v of values) {
    const idx = Math.min(Math.floor((v - min) / step), buckets - 1);
    counts[idx].count++;
  }
  const maxCount = Math.max(...counts.map((c) => c.count), 1);
  return counts.map((c) => ({ ...c, pct: (c.count / maxCount) * 100 }));
}

export default async function BacktestDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<SearchParams>;
}) {
  const { id } = await params;
  const sp = searchParams ? await searchParams : {};
  const page = Number(single(sp.page) ?? "1");
  const filter = (single(sp.filter) ?? "all") as TradeFilter;

  const [runResult, tradesResult] = await Promise.all([
    fetchApi<BacktestRunDetail>(`/backtest/${id}?page=${page}`),
    fetchApi<BacktestTradesPage>(
      `/backtest/${id}/trades?page=${page}&page_size=50&filter=${filter}`
    ),
  ]);

  if (!runResult.ok) {
    if (runResult.error.includes("404")) notFound();
    return (
      <AppShell navItems={navItems} activeLabel="Backtest">
        <Notice tone="danger">Erro ao carregar simulação: {runResult.error}</Notice>
      </AppShell>
    );
  }

  const run = runResult.data;
  const metrics = run.metrics;
  const trades = tradesResult.ok ? tradesResult.data.trades : run.trades;
  const tradesTotal = tradesResult.ok ? tradesResult.data.total : run.trades_total;
  const totalPages = Math.ceil(tradesTotal / 50);

  const monthlyPerf = buildMonthlyPerformance(run.trades);
  const pnlBuckets = buildPnlBuckets(run.trades);
  const months = Object.keys(monthlyPerf).sort();

  const exportBase = `${publicApiUrl}/backtest/${id}/export`;

  return (
    <AppShell navItems={navItems} activeLabel="Backtest">
      <BacktestPoller status={run.status} />

      <PageHeader
        eyebrow="Backtest"
        title={run.name}
        description={`${new Date(run.start_date).toLocaleDateString("pt-BR")} → ${new Date(run.end_date).toLocaleDateString("pt-BR")} • Capital inicial: ${formatMoney(run.initial_capital)}`}
        trailing={
          <div className="flex flex-wrap items-center gap-2">
            {run.status === "completed" && (
              <>
                <a
                  href={`${exportBase}?format=json`}
                  download
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm font-medium text-muted-foreground hover:bg-muted"
                >
                  <Download size={14} />
                  JSON
                </a>
                <a
                  href={`${exportBase}?format=csv`}
                  download
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm font-medium text-muted-foreground hover:bg-muted"
                >
                  <Download size={14} />
                  CSV
                </a>
              </>
            )}
          </div>
        }
      />

      {run.status === "pending" && (
        <Notice tone="warning">
          Aguardando início da simulação... atualizando automaticamente.
        </Notice>
      )}
      {run.status === "running" && (
        <Notice tone="warning">
          Simulação em andamento... atualizando automaticamente.
        </Notice>
      )}
      {run.status === "failed" && (
        <Notice tone="danger">
          Simulação falhou: {run.error_message ?? "Erro desconhecido"}
        </Notice>
      )}

      {metrics && (
        <MetricCardGroup>
          <MetricCard
            label="Retorno Total"
            value={fmtPct(metrics.total_return_pct)}
            tone={metricTone(metrics.total_return_pct)}
            detail={formatMoney(metrics.total_return_usd)}
          />
          <MetricCard
            label="Capital Final"
            value={formatMoney(metrics.final_capital)}
            tone="neutral"
            detail={`Inicial: ${formatMoney(run.initial_capital)}`}
          />
          <MetricCard
            label="Drawdown Máximo"
            value={fmtPct(metrics.max_drawdown_pct, false)}
            tone={Number(metrics.max_drawdown_pct) > 20 ? "danger" : "warning"}
            detail="Pior queda do pico"
          />
          <MetricCard
            label="Win Rate"
            value={`${Number(metrics.win_rate_pct).toFixed(1)}%`}
            tone={Number(metrics.win_rate_pct) >= 50 ? "positive" : "neutral"}
            detail={`${metrics.winning_trades}V / ${metrics.losing_trades}P`}
          />
          <MetricCard
            label="Total de Trades"
            value={String(metrics.total_trades)}
            tone="neutral"
            detail="Operações completas"
          />
          <MetricCard
            label="Profit Factor"
            value={metrics.profit_factor ? Number(metrics.profit_factor).toFixed(2) : "N/A"}
            tone={
              metrics.profit_factor && Number(metrics.profit_factor) >= 1.5
                ? "positive"
                : "neutral"
            }
            detail="Ganhos / Perdas"
          />
          <MetricCard
            label="Sharpe Ratio"
            value={metrics.sharpe_ratio ? Number(metrics.sharpe_ratio).toFixed(2) : "N/A"}
            tone={
              metrics.sharpe_ratio && Number(metrics.sharpe_ratio) >= 1
                ? "positive"
                : "neutral"
            }
            detail="Retorno ajustado ao risco"
          />
          <MetricCard
            label="BTC Buy & Hold"
            value={fmtPct(metrics.btc_buy_hold_return_pct)}
            tone={metricTone(metrics.btc_buy_hold_return_pct)}
            detail="Benchmark passivo"
          />
        </MetricCardGroup>
      )}

      <Panel>
        <PanelHeader eyebrow="Análise" title="Equity Curve" icon={<TrendingUp size={16} />} />
        <BacktestEquityChart points={run.equity_points} trades={run.trades} />
      </Panel>

      <Panel>
        <PanelHeader eyebrow="Histórico" title="Operações" icon={<BarChart2 size={16} />} />
        <div className="mb-4 flex items-center gap-1.5">
          <FilterChip
            href={`/backtest/${id}?filter=all`}
            active={filter === "all"}
          >
            Todas ({tradesTotal})
          </FilterChip>
          <FilterChip
            href={`/backtest/${id}?filter=winner`}
            active={filter === "winner"}
          >
            <TrendingUp size={12} />
            Vencedoras
          </FilterChip>
          <FilterChip
            href={`/backtest/${id}?filter=loser`}
            active={filter === "loser"}
          >
            <TrendingDown size={12} />
            Perdedoras
          </FilterChip>
        </div>
        {trades.length === 0 ? (
          <EmptyState>
            Nenhuma operação registrada nesta simulação.
          </EmptyState>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Saída</TableHead>
                  <TableHead className="text-right">Preço Entrada</TableHead>
                  <TableHead className="text-right">Preço Saída</TableHead>
                  <TableHead className="text-right">Qtd BTC</TableHead>
                  <TableHead className="text-right">P&L</TableHead>
                  <TableHead className="text-right">Retorno</TableHead>
                  <TableHead>Motivo</TableHead>
                  <TableHead>Resultado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell className="text-muted-foreground tabular-nums">
                      {t.trade_index + 1}
                    </TableCell>
                    <TableCell className="text-xs tabular-nums">
                      {formatDateTime(t.entry_time)}
                    </TableCell>
                    <TableCell className="text-xs tabular-nums">
                      {formatDateTime(t.exit_time)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(t.entry_price)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(t.exit_price)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatQuantity(t.quantity)}
                    </TableCell>
                    <TableCell
                      className={`text-right tabular-nums font-medium ${
                        t.is_winner
                          ? "text-[var(--color-success)]"
                          : "text-[var(--color-destructive)]"
                      }`}
                    >
                      {formatMoney(t.pnl_usd)}
                    </TableCell>
                    <TableCell
                      className={`text-right tabular-nums font-medium ${
                        t.is_winner
                          ? "text-[var(--color-success)]"
                          : "text-[var(--color-destructive)]"
                      }`}
                    >
                      {fmtPct(t.return_pct)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {exitReasonLabel(t.exit_reason)}
                    </TableCell>
                    <TableCell>
                      <StatusPill tone={t.is_winner ? "positive" : "danger"}>
                        {t.is_winner ? "Ganho" : "Perda"}
                      </StatusPill>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4">
                <span className="text-xs text-muted-foreground">
                  Página {page} de {totalPages}
                </span>
                <div className="flex gap-2">
                  {page > 1 && (
                    <PagerLink href={`/backtest/${id}?filter=${filter}&page=${page - 1}`}>
                      ← Anterior
                    </PagerLink>
                  )}
                  {page < totalPages && (
                    <PagerLink href={`/backtest/${id}?filter=${filter}&page=${page + 1}`}>
                      Próxima →
                    </PagerLink>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </Panel>

      {months.length > 0 && (
        <Panel>
          <PanelHeader eyebrow="Análise" title="Performance Mensal" icon={<BarChart2 size={16} />} />
          <div className="overflow-x-auto">
            <table className="w-full text-xs tabular-nums">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-2 pr-4 text-left font-medium text-muted-foreground">Mês</th>
                  <th className="py-2 text-right font-medium text-muted-foreground">P&L (USDT)</th>
                </tr>
              </thead>
              <tbody>
                {months.map((m) => {
                  const pnl = monthlyPerf[m] ?? 0;
                  const isPos = pnl >= 0;
                  return (
                    <tr key={m} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-muted-foreground">{m}</td>
                      <td
                        className={`py-2 text-right font-medium ${
                          isPos
                            ? "text-[var(--color-success)]"
                            : "text-[var(--color-destructive)]"
                        }`}
                      >
                        {isPos ? "+" : ""}
                        {pnl.toLocaleString("en-US", {
                          maximumFractionDigits: 2,
                          minimumFractionDigits: 2,
                        })}{" "}
                        USDT
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {pnlBuckets.length > 0 && (
        <Panel>
          <PanelHeader eyebrow="Análise" title="Distribuição de P&L por Trade" icon={<BarChart2 size={16} />} />
          <div className="flex items-end gap-1" style={{ height: "120px" }}>
            {pnlBuckets.map((bucket, i) => (
              <div
                key={i}
                className="flex flex-1 flex-col items-center justify-end gap-1"
                title={`${bucket.label}: ${bucket.count} trade${bucket.count !== 1 ? "s" : ""}`}
              >
                <div
                  className={`w-full rounded-t-sm transition-all ${
                    bucket.start >= 0 ? "bg-[var(--color-success)]/70" : "bg-[var(--color-destructive)]/70"
                  }`}
                  style={{ height: `${Math.max(bucket.pct, 2)}%` }}
                />
                <span className="text-[9px] text-muted-foreground">{bucket.label}</span>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </AppShell>
  );
}
