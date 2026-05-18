import { Bot, Gauge, ListFilter } from "lucide-react";

import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  EmptyState,
  Eyebrow,
  FilterChip,
  JsonBlock,
  Notice,
  PageHeader,
  PagerLink,
  StatusPill,
} from "@/components/ui";
import { fetchApi, formatDateTime, type DecisionsResponse } from "@/lib/api";

const decisionFilters = ["COMPRA", "VENDA", "MANTER_POSICAO", "NAO_OPERAR"] as const;
const pageSize = 20;

type SearchParams = Record<string, string | string[] | undefined>;

export default async function DecisionsPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const decision = single(params.decision);
  const offset = numericOffset(single(params.offset));
  const query = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
  if (isDecisionFilter(decision)) query.set("decision", decision);

  const result = await fetchApi<DecisionsResponse>(`/decisions?${query.toString()}`);
  const decisions = result.ok ? result.data.decisions : [];
  const environment = result.ok ? result.data.environment : "testnet";
  const symbol = result.ok ? result.data.symbol : "BTCUSDT";

  return (
    <AppShell navItems={navItems} activeLabel="Decisões">
      <PageHeader
        eyebrow={`Auditoria ${environment}`}
        title="Decisões do robô"
        description="Histórico auditável dos ciclos, motivos, indicadores e resultado de execução do robô."
        trailing={
          <StatusPill>
            <Bot size={16} aria-hidden="true" />
            {symbol}
          </StatusPill>
        }
      />

      <section className="flex flex-wrap items-center gap-2.5" aria-label="Filtros de decisão">
        <ListFilter size={18} aria-hidden="true" />
        <FilterChip active={!decision} href="/decisions">
          Todas
        </FilterChip>
        {decisionFilters.map((item) => (
          <FilterChip active={decision === item} href={`/decisions?decision=${item}`} key={item}>
            {item}
          </FilterChip>
        ))}
      </section>

      {!result.ok ? <Notice tone="danger">API sem resposta: {result.error}</Notice> : null}

      <section className="grid gap-3">
        {decisions.length === 0 ? (
          <EmptyState>Sem decisões para o filtro atual.</EmptyState>
        ) : (
          decisions.map((item) => (
            <article
              className="grid gap-[18px] rounded-[32px] border border-ink/10 bg-surface p-5 shadow-[0_18px_42px_rgba(20,20,19,0.055)]"
              key={item.id}
            >
              <div className="mb-0 flex items-start justify-between gap-4 max-md:flex-col">
                <div>
                  <Eyebrow>{formatDateTime(item.decided_at)}</Eyebrow>
                  <h2 className="m-0 text-2xl font-medium leading-tight tracking-[-0.02em]">{item.decision}</h2>
                </div>
                <StatusPill>{item.environment}</StatusPill>
              </div>
              <p className="m-0 text-lg leading-relaxed text-charcoal">{item.reason}</p>
              <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
                <MetaItem label="Bot run" value={shortId(item.bot_run_id)} />
                <MetaItem label="Strategy" value={shortId(item.strategy_config_id)} />
                <MetaItem label="Risk" value={shortId(item.risk_config_id)} />
                <MetaItem label="Market" value={shortId(item.market_snapshot_id)} />
              </div>
              <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
                <JsonBlock label="Motivo" value={item.reason_payload} />
                <JsonBlock label="Indicadores" value={item.indicators} />
                <JsonBlock label="Ordem pretendida" value={item.intended_order} />
                <JsonBlock label="Execução" value={item.execution_result} />
                <JsonBlock label="Carteira" value={item.portfolio_state} />
              </div>
            </article>
          ))
        )}
      </section>

      <footer className="flex items-center justify-between gap-2.5 max-md:flex-col">
        <PagerLink disabled={offset === 0} href={pageHref(decision, offset - pageSize)}>
          Anterior
        </PagerLink>
        <span className="inline-flex items-center gap-2 text-muted">
          <Gauge size={16} aria-hidden="true" />
          {offset + 1}-{offset + decisions.length}
        </span>
        <PagerLink disabled={decisions.length < pageSize} href={pageHref(decision, offset + pageSize)}>
          Próxima
        </PagerLink>
      </footer>
    </AppShell>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-0.5 rounded-full bg-aurum-white px-4 py-3">
      <span className="text-[13px] text-muted">{label}</span>
      <strong className="text-[13px] font-bold">{value}</strong>
    </div>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function numericOffset(value: string | undefined) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 0;
}

function isDecisionFilter(value: string | undefined): value is (typeof decisionFilters)[number] {
  return decisionFilters.some((item) => item === value);
}

function shortId(value: string | null) {
  return value ? value.slice(0, 8) : "-";
}

function pageHref(decision: string | undefined, offset: number) {
  const query = new URLSearchParams();
  if (isDecisionFilter(decision)) query.set("decision", decision);
  if (offset > 0) query.set("offset", String(offset));
  const suffix = query.toString();
  return suffix ? `/decisions?${suffix}` : "/decisions";
}
