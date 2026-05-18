import { Activity, AlertTriangle } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { CompactList, EmptyState, InfoRow, Notice, PageHeader, Panel, PanelHeader, StatusPill } from "@/components/ui";
import { fetchApi, formatDateTime, formatMoney, formatQuantity, type FillsResponse, type OrdersResponse } from "@/lib/api";

export default async function OperationsPage() {
  const [ordersResult, fillsResult] = await Promise.all([
    fetchApi<OrdersResponse>("/operations/orders?limit=25"),
    fetchApi<FillsResponse>("/operations/fills?limit=25"),
  ]);
  const orders = ordersResult.ok ? ordersResult.data.orders : [];
  const fills = fillsResult.ok ? fillsResult.data.fills : [];
  const environment = ordersResult.ok ? ordersResult.data.environment : fillsResult.ok ? fillsResult.data.environment : "testnet";
  const symbol = ordersResult.ok ? ordersResult.data.symbol : fillsResult.ok ? fillsResult.data.symbol : "BTCUSDT";

  return (
    <AppShell navItems={navItems} activeLabel="Operações">
      <PageHeader eyebrow={`Operações ${environment}`} title="Ordens e fills" trailing={<StatusPill><Activity size={16} aria-hidden="true" />{symbol}</StatusPill>} />
      {!ordersResult.ok || !fillsResult.ok ? <Notice tone="danger" icon={<AlertTriangle size={18} aria-hidden="true" />}>API sem resposta completa.</Notice> : null}
      <section className="grid grid-cols-2 gap-[18px] max-lg:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Ordens" title="Histórico recente" icon={<Activity />} />
          <CompactList>
            {orders.length === 0 ? <EmptyState>Sem ordens registradas.</EmptyState> : orders.map((order) => (
              <article className="grid gap-3 rounded-[18px] border border-hairline bg-canvas p-4" key={order.id}>
                <div className="flex items-center justify-between gap-3">
                  <strong>{order.side}</strong>
                  <StatusPill>{order.status}</StatusPill>
                </div>
                <InfoRow label="Quantidade" value={formatQuantity(order.executed_quantity)} />
                <InfoRow label="Preço médio" value={formatMoney(order.average_price)} />
                <InfoRow label="Enviada" value={formatDateTime(order.submitted_at)} />
              </article>
            ))}
          </CompactList>
        </Panel>
        <Panel>
          <PanelHeader eyebrow="Fills" title="Execuções" icon={<Activity />} />
          <CompactList>
            {fills.length === 0 ? <EmptyState>Sem fills registrados.</EmptyState> : fills.map((fill) => (
              <article className="grid gap-3 rounded-[18px] border border-hairline bg-canvas p-4" key={fill.id}>
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
