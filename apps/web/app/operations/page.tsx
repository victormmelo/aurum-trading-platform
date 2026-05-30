import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ListChecks,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { reconcileOrders } from "@/app/operations/actions";
import { ManualOrderPanel } from "@/app/operations/manual-order-panel";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  ActionItem,
  CompactList,
  EmptyState,
  IconTextButton,
  InfoRow,
  MetricCard,
  MetricCardGroup,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  StatusPill,
  cx,
} from "@/components/ui";
import {
  fetchApi,
  formatDateTime,
  formatMoney,
  formatQuantity,
  type FillsResponse,
  type Order,
  type OrdersResponse,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;
type Fill = FillsResponse["fills"][number];
type TimelineItem =
  | { id: string; kind: "order"; at: string | null; order: Order }
  | { id: string; kind: "fill"; at: string | null; fill: Fill };

const openStatuses = new Set(["NEW", "PARTIALLY_FILLED"]);
const attentionStatuses = new Set(["REJECTED", "EXPIRED"]);

export default async function OperationsPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
  const [ordersResult, fillsResult] = await Promise.all([
    fetchApi<OrdersResponse>("/operations/orders?limit=25"),
    fetchApi<FillsResponse>("/operations/fills?limit=25"),
  ]);
  const orders = ordersResult.ok ? ordersResult.data.orders : [];
  const fills = fillsResult.ok ? fillsResult.data.fills : [];
  const environment = ordersResult.ok ? ordersResult.data.environment : fillsResult.ok ? fillsResult.data.environment : "testnet";
  const symbol = ordersResult.ok ? ordersResult.data.symbol : fillsResult.ok ? fillsResult.data.symbol : "BTCUSDT";
  const openOrders = orders.filter((order) => openStatuses.has(order.status));
  const attentionOrders = orders.filter((order) => attentionStatuses.has(order.status));
  const lastOrder = orders[0];
  const lastFill = fills[0];
  const lastActivity = latestDate(lastOrder?.submitted_at, lastOrder?.closed_at, lastFill?.filled_at);
  const hasApiIssue = !ordersResult.ok || !fillsResult.ok;
  const timeline = buildTimeline(orders, fills);

  return (
    <AppShell navItems={navItems} activeLabel="Operações">
      <PageHeader
        eyebrow={`Operações ${environment}`}
        title="Centro de operações"
        description="Supervisione a execução do robô, confirme pendências e use intervenção manual apenas quando a validação Testnet exigir."
        trailing={
          <div className="flex flex-wrap items-center gap-2">
            <form action={reconcileOrders}>
              <IconTextButton>
                <RefreshCw size={16} aria-hidden="true" />
                Reconciliar
              </IconTextButton>
            </form>
            <StatusPill>
              <Activity size={16} aria-hidden="true" />
              {symbol}
            </StatusPill>
          </div>
        }
      />

      {success ? <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>{success}</Notice> : null}
      {error ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>{error}</Notice> : null}
      {hasApiIssue ? (
        <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>
          API sem resposta completa. Revise a disponibilidade antes de validar novas operações.
        </Notice>
      ) : null}

      <section className="grid gap-3 rounded-xl border border-border bg-card p-4 shadow-sm md:grid-cols-4 md:p-5">
        <ContextItem label="Ambiente" value={environmentLabel(environment)} />
        <ContextItem label="Ativo" value={symbol} />
        <ContextItem label="Escopo" value="Long-only, sem alavancagem" />
        <ContextItem label="Última atividade" value={formatDateTime(lastActivity)} />
      </section>

      <MetricCardGroup aria-label="Indicadores operacionais">
        <MetricCard
          label="Ordens pendentes"
          value={String(openOrders.length)}
          detail={openOrders.length > 0 ? "Requer acompanhamento ou reconciliação" : "Sem ordem aberta no histórico recente"}
          tone={openOrders.length > 0 ? "warning" : "positive"}
        />
        <MetricCard
          label="Última ordem"
          value={lastOrder ? orderStatusLabel(lastOrder.status) : "Sem ordem"}
          detail={lastOrder ? `${sideLabel(lastOrder.side)} · ${formatDateTime(lastOrder.submitted_at)}` : "Aguardando primeira execução"}
          tone={metricStatusTone(lastOrder?.status)}
        />
        <MetricCard
          label="Último fill"
          value={lastFill ? formatQuantity(lastFill.quantity) : "Sem fill"}
          detail={lastFill ? `${formatMoney(lastFill.price)} · ${formatDateTime(lastFill.filled_at)}` : "Nenhuma execução confirmada"}
          tone={lastFill ? "positive" : "neutral"}
        />
        <MetricCard
          label="Pendência operacional"
          value={pendingLabel(hasApiIssue, openOrders.length, attentionOrders.length)}
          detail={pendingDetail(hasApiIssue, openOrders.length, attentionOrders.length)}
          tone={pendingTone(hasApiIssue, openOrders.length, attentionOrders.length)}
        />
      </MetricCardGroup>

      <section className="grid grid-cols-[minmax(0,1.3fr)_minmax(320px,0.7fr)] gap-[18px] max-xl:grid-cols-1">
        <div className="grid gap-[18px]">
          <Panel>
            <PanelHeader eyebrow="Próxima ação" title="Pendências e recomendações" icon={<ListChecks />} />
            <CompactList>
              {hasApiIssue ? (
                <ActionItem tone="danger" title="API incompleta" description="Não envie nova ordem até confirmar backend e Binance Testnet." />
              ) : null}
              {openOrders.length > 0 ? (
                <ActionItem tone="warning" title="Ordens abertas" description="Reconcilie com a Binance Testnet para confirmar se houve fill, cancelamento ou rejeição." />
              ) : null}
              {attentionOrders.length > 0 ? (
                <ActionItem tone="danger" title="Ordens rejeitadas ou expiradas" description="Revise o motivo operacional antes de repetir uma validação manual." />
              ) : null}
              {!hasApiIssue && openOrders.length === 0 && attentionOrders.length === 0 ? (
                <ActionItem tone="positive" title="Sem bloqueio aparente" description="Acompanhe a linha do tempo e mantenha intervenções manuais restritas a validações controladas." />
              ) : null}
            </CompactList>
          </Panel>

          <Panel>
            <PanelHeader eyebrow="Linha do tempo" title="Eventos operacionais recentes" icon={<Clock3 />} />
            <OperationTimeline items={timeline} />
          </Panel>
        </div>

        <ManualOrderPanel />
      </section>

      <section className="grid grid-cols-2 gap-[18px] max-lg:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Detalhes técnicos" title="Ordens recentes" icon={<Activity />} />
          <CompactList>
            {orders.length === 0 ? <EmptyState>Sem ordens registradas.</EmptyState> : orders.map((order) => (
              <article className="grid gap-3 rounded-lg border border-border bg-background p-4" key={order.id}>
                <div className="flex items-center justify-between gap-3">
                  <strong className={cx("text-sm font-semibold", sideTextClass(order.side))}>{sideLabel(order.side)}</strong>
                  <StatusPill tone={orderStatusTone(order.status)}>{orderStatusLabel(order.status)}</StatusPill>
                </div>
                <InfoRow label="Quantidade executada" value={formatQuantity(order.executed_quantity)} />
                <InfoRow label="Preço médio" value={formatMoney(order.average_price)} />
                <InfoRow label="Enviada" value={formatDateTime(order.submitted_at)} />
              </article>
            ))}
          </CompactList>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Detalhes técnicos" title="Fills confirmados" icon={<ShieldCheck />} />
          <CompactList>
            {fills.length === 0 ? <EmptyState>Sem fills registrados.</EmptyState> : fills.map((fill) => (
              <article className="grid gap-3 rounded-lg border border-border bg-background p-4" key={fill.id}>
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-sm font-semibold text-primary">Execução confirmada</strong>
                  <StatusPill tone="positive">Fill</StatusPill>
                </div>
                <InfoRow label="Horário" value={formatDateTime(fill.filled_at)} />
                <InfoRow label="Preço" value={formatMoney(fill.price)} />
                <InfoRow label="Quantidade" value={formatQuantity(fill.quantity)} />
                <InfoRow label="Taxa" value={fill.fee_amount == null ? "-" : `${fill.fee_amount} ${fill.fee_asset ?? ""}`} />
              </article>
            ))}
          </CompactList>
        </Panel>
      </section>
    </AppShell>
  );
}

function ContextItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1.5">
      <span className="text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      <strong className="break-words text-sm font-semibold leading-5 text-foreground">{value}</strong>
    </div>
  );
}

function OperationTimeline({ items }: { items: TimelineItem[] }) {
  if (items.length === 0) return <EmptyState>Sem eventos operacionais recentes.</EmptyState>;

  return (
    <div className="grid gap-3">
      {items.map((item) => (
        <article className="grid gap-3 rounded-lg border border-border bg-background p-4" key={`${item.kind}-${item.id}`}>
          {item.kind === "order" ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <strong className={cx("block text-sm font-semibold leading-5", sideTextClass(item.order.side))}>
                    Ordem de {sideLabel(item.order.side).toLowerCase()}
                  </strong>
                  <span className="text-xs leading-5 text-muted-foreground">Origem {item.order.decision_id ? "robô" : "manual/dashboard"}</span>
                </div>
                <StatusPill tone={orderStatusTone(item.order.status)}>{orderStatusLabel(item.order.status)}</StatusPill>
              </div>
              <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
                <MiniFact label="Quantidade" value={formatQuantity(orderQuantity(item.order))} />
                <MiniFact label="Preço médio" value={formatMoney(item.order.average_price)} />
                <MiniFact label="Horário" value={formatDateTime(item.order.submitted_at)} />
              </div>
            </>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <strong className="block text-sm font-semibold leading-5 text-primary">Fill confirmado</strong>
                  <span className="text-xs leading-5 text-muted-foreground">Execução liquidada na Binance Spot Testnet</span>
                </div>
                <StatusPill tone="positive">Confirmado</StatusPill>
              </div>
              <div className="grid grid-cols-3 gap-3 max-md:grid-cols-1">
                <MiniFact label="Quantidade" value={formatQuantity(item.fill.quantity)} />
                <MiniFact label="Preço" value={formatMoney(item.fill.price)} />
                <MiniFact label="Horário" value={formatDateTime(item.fill.filled_at)} />
              </div>
            </>
          )}
        </article>
      ))}
    </div>
  );
}

function MiniFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 rounded-md border border-border bg-muted px-3 py-2">
      <span className="text-xs font-medium leading-5 text-muted-foreground">{label}</span>
      <strong className="break-words text-sm font-semibold leading-5">{value}</strong>
    </div>
  );
}

function buildTimeline(orders: Order[], fills: Fill[]) {
  return [
    ...orders.map((order) => ({ id: order.id, kind: "order" as const, at: order.submitted_at ?? order.closed_at, order })),
    ...fills.map((fill) => ({ id: fill.id, kind: "fill" as const, at: fill.filled_at, fill })),
  ]
    .sort((a, b) => timestamp(b.at) - timestamp(a.at))
    .slice(0, 12);
}

function orderQuantity(order: Order) {
  const executed = Number(order.executed_quantity);
  return Number.isFinite(executed) && executed > 0 ? order.executed_quantity : order.requested_quantity;
}

function orderStatusLabel(value: string | undefined) {
  if (value === "NEW") return "Aberta";
  if (value === "PARTIALLY_FILLED") return "Parcial";
  if (value === "FILLED") return "Executada";
  if (value === "CANCELED") return "Cancelada";
  if (value === "REJECTED") return "Rejeitada";
  if (value === "EXPIRED") return "Expirada";
  return value ?? "Sem ordem";
}

function orderStatusTone(value: string | undefined): "neutral" | "positive" | "warning" | "danger" {
  if (value === "FILLED") return "positive";
  if (value === "NEW" || value === "PARTIALLY_FILLED" || value === "CANCELED") return "warning";
  if (value === "REJECTED" || value === "EXPIRED") return "danger";
  return "neutral";
}

function metricStatusTone(value: string | undefined): "neutral" | "positive" | "warning" {
  const tone = orderStatusTone(value);
  return tone === "danger" ? "warning" : tone;
}

function sideLabel(value: string) {
  if (value === "BUY") return "Compra";
  if (value === "SELL") return "Venda";
  return value;
}

function sideTextClass(value: string) {
  if (value === "BUY") return "text-primary";
  if (value === "SELL") return "text-warning";
  return "text-foreground";
}

function pendingLabel(hasApiIssue: boolean, openCount: number, attentionCount: number) {
  if (hasApiIssue) return "API";
  if (attentionCount > 0) return "Revisar";
  if (openCount > 0) return "Reconciliar";
  return "OK";
}

function pendingDetail(hasApiIssue: boolean, openCount: number, attentionCount: number) {
  if (hasApiIssue) return "Resposta incompleta da API";
  if (attentionCount > 0) return `${attentionCount} ordem(ns) com atenção`;
  if (openCount > 0) return `${openCount} ordem(ns) aberta(s)`;
  return "Sem pendência crítica";
}

function pendingTone(hasApiIssue: boolean, openCount: number, attentionCount: number): "neutral" | "positive" | "warning" {
  if (hasApiIssue || attentionCount > 0 || openCount > 0) return "warning";
  return "positive";
}

function latestDate(...values: Array<string | null | undefined>) {
  const latest = values
    .map((value) => ({ value, time: timestamp(value) }))
    .filter((entry) => entry.value && entry.time > 0)
    .sort((a, b) => b.time - a.time)[0];
  return latest?.value ?? null;
}

function timestamp(value: string | null | undefined) {
  if (!value) return 0;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function environmentLabel(value: string) {
  return value.toLowerCase() === "testnet" ? "Binance Spot Testnet" : value;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
