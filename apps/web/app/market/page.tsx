import Link from "next/link";
import { AlertTriangle, CandlestickChart, Database, TableProperties } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { LiveMarketCards, LiveMarketPanel } from "@/components/live-market";
import { MarketHistoryChart } from "@/components/market-history-chart";
import {
  cx,
  EmptyState,
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
  formatDateTime,
  type MarketCandlesResponse,
  type MarketCandle,
  type MarketSummary,
} from "@/lib/api";

type MarketInterval = "1h" | "4h" | "1d";
type MarketWindow = "7d" | "30d" | "90d" | "250";

const intervals: MarketInterval[] = ["1h", "4h", "1d"];
const windows: Array<{ value: MarketWindow; label: string }> = [
  { value: "7d", label: "7d" },
  { value: "30d", label: "30d" },
  { value: "90d", label: "90d" },
  { value: "250", label: "250 candles" },
];

export default async function MarketPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = (await searchParams) ?? {};
  const interval = parseInterval(params.interval);
  const window = parseWindow(params.window);
  const limit = candleLimit(interval, window);
  const [result, candlesResult] = await Promise.all([
    fetchApi<MarketSummary>("/market/summary"),
    fetchApi<MarketCandlesResponse>(`/market/candles?interval=${interval}&limit=${limit}`),
  ]);
  const market = result.ok ? result.data.snapshot : null;
  const environment = result.ok ? result.data.environment : "testnet";
  const symbol = result.ok ? result.data.symbol : "BTCUSDT";
  const candles = candlesResult.ok ? candlesResult.data.candles : [];
  const latestCandle = candles.at(-1) ?? null;

  return (
    <AppShell navItems={navItems} activeLabel="Mercado">
      <PageHeader
        eyebrow={`Mercado ${environment}`}
        title={symbol}
        description="Leitura operacional do BTCUSDT com snapshot ao vivo, candles persistidos e histórico para inspeção."
        trailing={
          <StatusPill>
            <Database size={16} aria-hidden="true" />
            {formatDateTime(market?.captured_at)}
          </StatusPill>
        }
      />
      {!result.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>API sem resposta: {result.error}</Notice> : null}
      {!candlesResult.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>Histórico indisponível: {candlesResult.error}</Notice> : null}
      <LiveMarketCards initial={result.ok ? result.data : { environment, symbol, snapshot: null }} />
      <Panel>
        <PanelHeader eyebrow="Histórico persistido" title={`${interval} · ${windowLabel(window)}`} icon={<CandlestickChart />} />
        <div className="grid gap-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2" aria-label="Intervalo do candle">
              {intervals.map((item) => (
                <FilterLink
                  active={item === interval}
                  href={marketHref(item, window)}
                  key={item}
                >
                  {item}
                </FilterLink>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2" aria-label="Janela historica">
              {windows.map((item) => (
                <FilterLink
                  active={item.value === window}
                  href={marketHref(interval, item.value)}
                  key={item.value}
                >
                  {item.label}
                </FilterLink>
              ))}
            </div>
          </div>
          {candles.length > 0 ? (
            <div className="grid gap-4">
              <div className="grid gap-3 md:grid-cols-3">
                <HistoryFact label="Candles carregados" value={String(candles.length)} />
                <HistoryFact label="Primeiro candle" value={formatDateTime(candles[0]?.open_time)} />
                <HistoryFact label="Último candle" value={formatDateTime(latestCandle?.close_time)} />
              </div>
              <MarketHistoryChart candles={candles} interval={interval} />
              <p className="m-0 text-xs leading-5 text-muted-foreground">
                Gráfico financeiro renderizado com Lightweight Charts™, mantido pela TradingView.
              </p>
            </div>
          ) : (
            <EmptyState>
              Ainda não há candles persistidos para {symbol} em {interval}. Execute o worker ou o comando de importação histórica antes de avaliar o mercado por gráfico.
            </EmptyState>
          )}
        </div>
      </Panel>
      <MarketCandlesTable candles={candles.slice(-12).reverse()} />
      <LiveMarketPanel initial={result.ok ? result.data : { environment, symbol, snapshot: null }} />
    </AppShell>
  );
}

function FilterLink({
  active,
  children,
  href,
}: {
  active: boolean;
  children: string;
  href: string;
}) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      className={cx(
        "inline-flex min-h-10 items-center justify-center rounded-md border px-3 text-sm font-medium leading-none transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50",
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-input bg-background text-foreground hover:bg-accent",
      )}
      href={href}
    >
      {children}
    </Link>
  );
}

function HistoryFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted px-4 py-3">
      <span className="block text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      <strong className="mt-1 block break-words text-sm font-semibold leading-5 text-foreground">{value}</strong>
    </div>
  );
}

function MarketCandlesTable({ candles }: { candles: MarketCandle[] }) {
  return (
    <Panel>
      <PanelHeader eyebrow="Candles recentes" title="OHLCV persistido" icon={<TableProperties />} />
      {candles.length === 0 ? (
        <EmptyState>Sem candles recentes para listar.</EmptyState>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fechamento</TableHead>
              <TableHead className="text-right">Abertura</TableHead>
              <TableHead className="text-right">Máxima</TableHead>
              <TableHead className="text-right">Mínima</TableHead>
              <TableHead className="text-right">Fechamento</TableHead>
              <TableHead className="text-right">Volume</TableHead>
              <TableHead className="text-right">Trades</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {candles.map((candle) => (
              <TableRow key={candle.id}>
                <TableCell className="whitespace-nowrap">{formatDateTime(candle.close_time)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatMoney(candle.open_price)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatMoney(candle.high_price)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatMoney(candle.low_price)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatMoney(candle.close_price)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatNumber(candle.volume)}</TableCell>
                <TableCell className="text-right tabular-nums">{candle.trade_count ?? "-"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Panel>
  );
}

function parseInterval(value: string | string[] | undefined): MarketInterval {
  const candidate = Array.isArray(value) ? value[0] : value;
  return candidate === "4h" || candidate === "1d" ? candidate : "1h";
}

function parseWindow(value: string | string[] | undefined): MarketWindow {
  const candidate = Array.isArray(value) ? value[0] : value;
  return candidate === "30d" || candidate === "90d" || candidate === "250" ? candidate : "7d";
}

function candleLimit(interval: MarketInterval, window: MarketWindow) {
  if (window === "250") return 250;
  const days = window === "90d" ? 90 : window === "30d" ? 30 : 7;
  const candlesPerDay = interval === "1h" ? 24 : interval === "4h" ? 6 : 1;
  return Math.min(days * candlesPerDay, 500);
}

function windowLabel(window: MarketWindow) {
  return window === "250" ? "250 candles" : window;
}

function marketHref(interval: MarketInterval, window: MarketWindow) {
  return `/market?interval=${interval}&window=${window}`;
}

function formatMoney(value: string | null | undefined, currency = "USDT") {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value} ${currency}`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 2 })} ${currency}`;
}

function formatNumber(value: string | null | undefined) {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  return number.toLocaleString("en-US", { maximumFractionDigits: 4 });
}
