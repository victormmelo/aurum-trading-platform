import { CheckCircle2, CircleAlert, KeyRound, ShieldCheck, Trash2 } from "lucide-react";

import { createMcpToken, revokeMcpToken } from "@/app/mcp/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CompactList,
  EmptyState,
  IconTextButton,
  InfoRow,
  LabeledInput,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PrimaryButton,
  StatusPill,
} from "@/components/ui";
import { formatDateTime, getMcpData, type McpAccessLog, type McpToken } from "@/lib/api";

const scopeLabels = [
  "read:market",
  "read:portfolio",
  "read:trades",
  "read:decisions",
  "read:config",
  "read:reports",
] as const;

type SearchParams = Record<string, string | string[] | undefined>;

export default async function McpPage({ searchParams }: { searchParams?: Promise<SearchParams> }) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
  const tokenSecret = single(params.token);
  const data = await getMcpData();
  const status = data.status.ok ? data.status.data : null;
  const tokens = data.tokens.ok ? data.tokens.data.tokens : [];
  const logs = data.logs.ok ? data.logs.data.logs : [];
  const environment =
    status?.environment ??
    (data.tokens.ok ? data.tokens.data.environment : null) ??
    (data.logs.ok ? data.logs.data.environment : null) ??
    "testnet";

  return (
    <AppShell navItems={navItems} activeLabel="MCP">
      <PageHeader
        eyebrow={`MCP ${environment}`}
        title="Agentes e tokens"
        trailing={
          <StatusPill tone={status?.auth_enabled ? "positive" : "warning"}>
            <ShieldCheck size={16} aria-hidden="true" />
            Auth {status?.auth_enabled ? "ativo" : "indisponível"}
          </StatusPill>
        }
      />

      {success ? <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>{success}</Notice> : null}
      {error ? <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>{error}</Notice> : null}
      {tokenSecret ? (
        <Notice tone="warning" icon={<KeyRound size={18} aria-hidden="true" />}>
          Token criado: <code className="break-all font-mono">{tokenSecret}</code>
        </Notice>
      ) : null}
      {[data.status, data.tokens, data.logs].some((result) => !result.ok) ? (
        <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>
          API MCP sem resposta completa.
        </Notice>
      ) : null}

      <section className="grid grid-cols-[minmax(0,0.95fr)_minmax(360px,1.05fr)] gap-[18px] max-lg:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Novo token" title="Acesso read-only" icon={<KeyRound />} />
          <form action={createMcpToken} className="grid gap-3.5">
            <LabeledInput label="Nome" name="name" defaultValue="Codex" required />
            <LabeledInput label="Agente" name="agent_name" defaultValue="codex" />
            <LabeledInput label="Expira em" name="expires_at" type="datetime-local" />
            <div className="grid gap-2">
              <span className="text-[13px] text-muted">Escopos</span>
              <div className="grid grid-cols-2 gap-2 max-md:grid-cols-1">
                {scopeLabels.map((scope) => (
                  <label className="flex min-h-11 items-center gap-2 rounded-[14px] border border-line bg-canvas px-3.5 text-sm" key={scope}>
                    <input name="scopes" type="checkbox" value={scope} defaultChecked={scope !== "read:reports"} />
                    {scope}
                  </label>
                ))}
              </div>
            </div>
            <PrimaryButton>Criar token</PrimaryButton>
          </form>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Capabilities" title="Tools disponíveis" icon={<ShieldCheck />} />
          {status ? (
            <div className="grid gap-3">
              <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
                <InfoRow label="Ambiente" value={status.environment} />
                <InfoRow label="Escopos" value={String(status.allowed_scopes.length)} />
              </div>
              <div className="flex flex-wrap gap-2">
                {status.tools.map((tool) => (
                  <StatusPill key={tool}>{tool}</StatusPill>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState>Status MCP indisponível.</EmptyState>
          )}
        </Panel>
      </section>

      <section className="grid grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)] gap-[18px] max-lg:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Tokens" title="Acessos ativos e revogados" icon={<KeyRound />} />
          <div className="grid gap-3.5">
            {tokens.length === 0 ? <EmptyState>Nenhum token MCP criado.</EmptyState> : tokens.map((token) => <TokenRow token={token} key={token.id} />)}
          </div>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Auditoria" title="Chamadas recentes" icon={<ShieldCheck />} />
          <CompactList>
            {logs.length === 0 ? <EmptyState>Sem chamadas MCP auditadas.</EmptyState> : logs.map((log) => <LogRow log={log} key={log.id} />)}
          </CompactList>
        </Panel>
      </section>
    </AppShell>
  );
}

function TokenRow({ token }: { token: McpToken }) {
  return (
    <article className="grid gap-3 rounded-[18px] border border-line bg-canvas p-[18px]">
      <div className="flex items-start justify-between gap-4 max-md:flex-col">
        <div>
          <h2 className="m-0 text-2xl font-medium leading-tight tracking-[-0.02em]">{token.name}</h2>
          <p className="m-0 mt-1 text-sm text-muted">{token.agent_name ?? "sem agente"}</p>
        </div>
        <StatusPill tone={token.status === "active" ? "positive" : "warning"}>{token.status}</StatusPill>
      </div>
      <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <InfoRow label="Criado" value={formatDateTime(token.created_at)} />
        <InfoRow label="Último uso" value={formatDateTime(token.last_used_at)} />
        <InfoRow label="Expira" value={formatDateTime(token.expires_at)} />
        <InfoRow label="Revogado" value={formatDateTime(token.revoked_at)} />
      </div>
      <div className="flex flex-wrap gap-2">
        {token.scopes.map((scope) => <StatusPill key={scope}>{scope}</StatusPill>)}
      </div>
      {token.status === "active" ? (
        <form action={revokeMcpToken}>
          <input type="hidden" name="id" value={token.id} />
          <IconTextButton><Trash2 size={16} aria-hidden="true" />Revogar</IconTextButton>
        </form>
      ) : null}
    </article>
  );
}

function LogRow({ log }: { log: McpAccessLog }) {
  return (
    <article className="grid gap-2 rounded-[18px] border border-line bg-canvas p-4">
      <div className="flex items-center justify-between gap-3">
        <strong className="break-all text-sm">{log.resource}</strong>
        <StatusPill tone={log.status === "success" ? "positive" : "danger"}>{log.status}</StatusPill>
      </div>
      <InfoRow label="Horário" value={formatDateTime(log.occurred_at)} />
      <InfoRow label="Agente" value={log.agent_name ?? "-"} />
      <InfoRow label="Latência" value={log.latency_ms == null ? "-" : `${log.latency_ms}ms`} />
      {log.error_message ? <p className="m-0 text-sm text-danger">{log.error_message}</p> : null}
    </article>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
