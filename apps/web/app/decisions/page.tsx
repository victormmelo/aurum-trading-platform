import { ArrowLeft, Bot, Braces, Gauge, ListFilter } from "lucide-react";
import Link from "next/link";

import { compactJson, fetchApi, formatDateTime, type DecisionsResponse } from "@/lib/api";

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
    <main className="detailShell">
      <header className="detailHeader">
        <Link className="backLink" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          Dashboard
        </Link>
        <div>
          <p className="eyebrow">Auditoria {environment}</p>
          <h1>Decisões do robô</h1>
        </div>
        <span className="statusPill">
          <Bot size={16} aria-hidden="true" />
          {symbol}
        </span>
      </header>

      <section className="filterBand" aria-label="Filtros de decisão">
        <ListFilter size={18} aria-hidden="true" />
        <Link className={!decision ? "filterChip active" : "filterChip"} href="/decisions">
          Todas
        </Link>
        {decisionFilters.map((item) => (
          <Link
            className={decision === item ? "filterChip active" : "filterChip"}
            href={`/decisions?decision=${item}`}
            key={item}
          >
            {item}
          </Link>
        ))}
      </section>

      {!result.ok ? (
        <section className="noticePanel danger">
          <span>API sem resposta: {result.error}</span>
        </section>
      ) : null}

      <section className="decisionAuditList">
        {decisions.length === 0 ? (
          <div className="emptyState">Sem decisões para o filtro atual.</div>
        ) : (
          decisions.map((item) => (
            <article className="auditCard" key={item.id}>
              <div className="auditSummary">
                <div>
                  <p className="eyebrow">{formatDateTime(item.decided_at)}</p>
                  <h2>{item.decision}</h2>
                </div>
                <span className="statusPill">{item.environment}</span>
              </div>
              <p className="reasonText">{item.reason}</p>
              <div className="auditMeta">
                <MetaItem label="Bot run" value={shortId(item.bot_run_id)} />
                <MetaItem label="Strategy" value={shortId(item.strategy_config_id)} />
                <MetaItem label="Risk" value={shortId(item.risk_config_id)} />
                <MetaItem label="Market" value={shortId(item.market_snapshot_id)} />
              </div>
              <div className="jsonGrid">
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

      <footer className="pager">
        <Link className={offset === 0 ? "pagerButton disabled" : "pagerButton"} href={pageHref(decision, offset - pageSize)}>
          Anterior
        </Link>
        <span>
          <Gauge size={16} aria-hidden="true" />
          {offset + 1}-{offset + decisions.length}
        </span>
        <Link
          className={decisions.length < pageSize ? "pagerButton disabled" : "pagerButton"}
          href={pageHref(decision, offset + pageSize)}
        >
          Próxima
        </Link>
      </footer>
    </main>
  );
}

function JsonBlock({ label, value }: { label: string; value: Record<string, unknown> }) {
  return (
    <section className="jsonBlock">
      <h3>
        <Braces size={14} aria-hidden="true" />
        {label}
      </h3>
      <pre>{compactJson(value)}</pre>
    </section>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
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
