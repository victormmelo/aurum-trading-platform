import {
  Activity,
  AlertTriangle,
  BarChart3,
  CalendarRange,
  CheckCircle2,
  ReceiptText,
  TrendingUp,
} from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CompactList,
  EmptyState,
  FilterChip,
  InfoRow,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  StatusCluster,
  StatusPill,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  cx,
} from "@/components/ui";
import {
  fetchApi,
  formatDateTime,
  formatMoney,
  formatQuantity,
  type PerformanceDailyPoint,
  type PerformancePeriod,
  type PerformanceSummary,
  type PerformanceTradesResponse,
  type PerformanceTrade,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

const periods: Array<{ value: PerformancePeriod; label: string }> = [
  { value: "7d", label: "7 dias" },
  { value: "30d", label: "30 dias" },
  { value: "90d", label: "90 dias" },
  { value: "mtd", label: "Mês" },
  { value: "ytd", label: "Ano" },
  { value: "all", label: "Desde o início" },
];

export default async function PerformancePage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const period = parsePeriod(single(params.period));
  const [summaryResult, tradesResult] = await Promise.all([
    fetchApi<PerformanceSummary>(`/performance/summary?period=${period}`),
    fetchApi<PerformanceTradesResponse>(`/performance/trades?period=${period}`),
  ]);
  const summary = summaryResult.ok ? summaryResult.data : null;
  const trades = tradesResult.ok ? tradesResult.data.trades : [];
  const environment = summary?.environment ?? (tradesResult.ok ? tradesResult.data.environment : "testnet");
  const symbol = summary?.symbol ?? (tradesResult.ok ? tradesResult.data.symbol : "BTCUSDT");

  return (
    <AppShell navItems={navItems} activeLabel="Performance">
      <PageHeader
        eyebrow={`Performance ${environment}`}
        title="Resultado financeiro"
        description="Apuração por custo médio: compras formam posição e custo; vendas realizam lucro ou prejuízo proporcional."
        trailing={
          <StatusCluster>
            <StatusPill>
              <ReceiptText size={16} aria-hidden="true" />
              {periodLabel(period)}
            </StatusPill>
            <StatusPill>
              <Activity size={16} aria-hidden="true" />
              {symbol}
            </StatusPill>
          </StatusCluster>
        }
      />

      {!summaryResult.ok ? (
        <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API de performance indisponível: {summaryResult.error}
        </Notice>
      ) : null}
      {!tradesResult.ok ? (
        <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API de operações realizadas indisponível: {tradesResult.error}
        </Notice>
      ) : null}

      <section className="flex flex-wrap gap-2" aria-label="Filtro de período">
        {periods.map((item) => (
          <FilterChip active={period === item.value} href={`/performance?period=${item.value}`} key={item.value}>
            {item.label}
          </FilterChip>
        ))}
      </section>

      <MetricCardGroup aria-label="Indicadores de performance">
        <MetricCard
          label="Resultado realizado"
          value={formatMoney(summary?.realized_pnl)}
          detail={`${summary?.sell_count ?? 0} venda(s) · acerto ${percentLabel(summary?.win_rate_pct)}`}
          tone={moneyTone(summary?.realized_pnl)}
        />
        <MetricCard
          label="Resultado aberto"
          value={formatMoney(summary?.unrealized_pnl)}
          detail="PnL não realizado da posição atual"
          tone={moneyTone(summary?.unrealized_pnl)}
        />
        <MetricCard
          label="Resultado total"
          value={formatMoney(summary?.total_pnl)}
          detail={`Taxas ${formatMoney(summary?.total_fees_usdt)}`}
          tone={moneyTone(summary?.total_pnl)}
        />
        <MetricCard
          label="Status"
          value={performanceStatusLabel(summary)}
          detail={`Retorno ${percentLabel(summary?.return_pct)} · DD ${percentLabel(summary?.max_drawdown_pct)}`}
          tone={performanceStatusTone(summary)}
        />
      </MetricCardGroup>

      <section className="grid grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)] gap-[18px] max-xl:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Evolução" title="Patrimônio e PnL realizado" icon={<BarChart3 />} />
          <PerformanceTrend points={summary?.daily ?? []} />
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Diagnóstico" title="Qualidade das vendas" icon={<CheckCircle2 />} />
          <CompactList>
            <InfoRow label="Lucro médio" value={formatMoney(summary?.average_win_usdt)} />
            <InfoRow label="Prejuízo médio" value={formatMoney(summary?.average_loss_usdt)} />
            <InfoRow label="Maior ganho" value={formatMoney(summary?.largest_win_usdt)} />
            <InfoRow label="Maior perda" value={formatMoney(summary?.largest_loss_usdt)} />
            <InfoRow label="Patrimônio inicial" value={formatMoney(summary?.initial_equity)} />
            <InfoRow label="Patrimônio final" value={formatMoney(summary?.final_equity)} />
          </CompactList>
        </Panel>
      </section>

      <Panel>
        <PanelHeader eyebrow="Vendas realizadas" title="Apuração por operação" icon={<ReceiptText />} />
        <TradesTable trades={trades} />
      </Panel>
    </AppShell>
  );
}

function PerformanceTrend({ points }: { points: PerformanceDailyPoint[] }) {
  if (points.length === 0) {
    return <EmptyState>Sem pontos de patrimônio ou vendas realizadas no período selecionado.</EmptyState>;
  }

  const equityValues = points.map((point) => Number(point.equity)).filter(Number.isFinite);
  const pnlValues = points.map((point) => Number(point.realized_pnl)).filter(Number.isFinite);
  const minEquity = equityValues.length > 0 ? Math.min(...equityValues) : 0;
  const maxEquity = equityValues.length > 0 ? Math.max(...equityValues) : 1;
  const maxAbsPnl = Math.max(1, ...pnlValues.map((value) => Math.abs(value)));
  const linePoints = points
    .map((point, index) => {
      const equity = Number(point.equity);
      if (!Number.isFinite(equity)) return null;
      const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
      const range = maxEquity - minEquity || 1;
      const y = 88 - ((equity - minEquity) / range) * 76;
      return `${x},${y}`;
    })
    .filter(Boolean)
    .join(" ");

  return (
    <div className="grid gap-4">
      <div className="h-[220px] rounded-lg border border-border bg-background p-4">
        <svg className="h-full w-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 100" role="img" aria-label="Curva de patrimônio">
          <line className="stroke-border" x1="0" x2="100" y1="88" y2="88" vectorEffect="non-scaling-stroke" />
          {linePoints ? (
            <polyline
              className="fill-none stroke-primary"
              points={linePoints}
              strokeWidth="2.5"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
        </svg>
      </div>

      <div className="grid grid-cols-[repeat(auto-fit,minmax(28px,1fr))] items-end gap-2" aria-label="PnL realizado por dia">
        {points.map((point) => {
          const pnl = Number(point.realized_pnl);
          const height = Math.max(8, Math.min(84, (Math.abs(pnl) / maxAbsPnl) * 84));
          return (
            <div className="grid min-w-0 gap-2" key={point.date}>
              <div className="flex h-24 items-end rounded-md bg-muted px-1">
                <div
                  className={cx("w-full rounded-sm", pnl >= 0 ? "bg-primary" : "bg-destructive")}
                  style={{ height: `${height}px` }}
                  title={`${point.date}: ${formatMoney(point.realized_pnl)}`}
                />
              </div>
              <span className="truncate text-center text-[11px] font-medium leading-4 text-muted-foreground">
                {shortDate(point.date)}
              </span>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-2">
        <StatusPill tone="positive">
          <TrendingUp size={14} aria-hidden="true" />
          Patrimônio
        </StatusPill>
        <StatusPill tone="neutral">
          <CalendarRange size={14} aria-hidden="true" />
          Barras por dia com venda
        </StatusPill>
      </div>
    </div>
  );
}

function TradesTable({ trades }: { trades: PerformanceTrade[] }) {
  if (trades.length === 0) {
    return <EmptyState>Sem vendas realizadas no período. Compras ainda podem estar formando custo médio e PnL aberto.</EmptyState>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Venda</TableHead>
          <TableHead>Origem</TableHead>
          <TableHead className="text-right">Quantidade</TableHead>
          <TableHead className="text-right">Preço venda</TableHead>
          <TableHead className="text-right">Custo médio</TableHead>
          <TableHead className="text-right">Receita</TableHead>
          <TableHead className="text-right">Custo baixado</TableHead>
          <TableHead className="text-right">Taxas</TableHead>
          <TableHead className="text-right">Resultado</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {trades.map((trade) => (
          <TableRow key={trade.id}>
            <TableCell>
              <div className="grid gap-1">
                <span className="font-semibold text-foreground">{formatDateTime(trade.sold_at)}</span>
                <span className="text-xs text-muted-foreground">{trade.status}</span>
              </div>
            </TableCell>
            <TableCell>
              <StatusPill tone={trade.source === "robô" ? "positive" : "neutral"}>{trade.source}</StatusPill>
            </TableCell>
            <TableCell className="text-right tabular-nums">{formatQuantity(trade.quantity)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatMoney(trade.average_sell_price)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatMoney(trade.average_cost)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatMoney(trade.gross_proceeds)}</TableCell>
            <TableCell className="text-right tabular-nums">{formatMoney(trade.cost_basis_reduced)}</TableCell>
            <TableCell className="text-right tabular-nums">
              {formatMoney(trade.fees_usdt)}
              {trade.fee_estimated ? <span className="ml-1 text-xs text-muted-foreground">est.</span> : null}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              <strong className={cx("block", Number(trade.pnl_usdt) >= 0 ? "text-primary" : "text-destructive")}>
                {formatMoney(trade.pnl_usdt)}
              </strong>
              <span className="text-xs text-muted-foreground">{percentLabel(trade.pnl_pct)}</span>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function parsePeriod(value: string | undefined): PerformancePeriod {
  return periods.some((item) => item.value === value) ? (value as PerformancePeriod) : "30d";
}

function periodLabel(value: PerformancePeriod) {
  return periods.find((item) => item.value === value)?.label ?? value;
}

function percentLabel(value: string | null | undefined) {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value}%`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 2 })}%`;
}

function moneyTone(value: string | null | undefined): "positive" | "warning" | "neutral" {
  const parsed = value == null ? Number.NaN : Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return "neutral";
  return parsed > 0 ? "positive" : "warning";
}

function performanceStatusLabel(value: PerformanceSummary | null) {
  if (!value) return "sem dados";
  if (value.status === "lucrando") return "Lucrando";
  if (value.status === "perdendo") return "Perdendo";
  if (value.status === "sem_amostra_suficiente") return "Sem amostra";
  return "Atenção";
}

function performanceStatusTone(
  value: PerformanceSummary | null,
): "positive" | "warning" | "danger" | "neutral" {
  if (!value) return "neutral";
  if (value.status === "lucrando") return "positive";
  if (value.status === "perdendo") return "danger";
  if (value.status === "sem_amostra_suficiente") return "warning";
  return "warning";
}

function shortDate(value: string) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    timeZone: "America/Sao_Paulo",
  }).format(date);
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
