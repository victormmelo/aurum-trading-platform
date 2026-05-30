import { CheckCircle2, CircleAlert, KeyRound, ShieldCheck, Trash2 } from "lucide-react";

import { createMcpToken, revokeMcpToken } from "@/app/mcp/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CheckboxCard,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
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
              <span className="text-xs font-medium leading-5 text-muted-foreground">Escopos</span>
              <div className="grid grid-cols-2 gap-2 max-md:grid-cols-1">
                {scopeLabels.map((scope) => (
                  <CheckboxCard name="scopes" value={scope} defaultChecked={scope !== "read:reports"} key={scope}>
                    {scope}
                  </CheckboxCard>
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
          <TokenTable tokens={tokens} />
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Auditoria" title="Chamadas recentes" icon={<ShieldCheck />} />
          <LogTable logs={logs} />
        </Panel>
      </section>
    </AppShell>
  );
}

function TokenTable({ tokens }: { tokens: McpToken[] }) {
  if (tokens.length === 0) return <EmptyState>Nenhum token MCP criado.</EmptyState>;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Token</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Último uso</TableHead>
          <TableHead>Expira</TableHead>
          <TableHead className="text-right">Ação</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tokens.map((token) => (
          <TableRow key={token.id}>
            <TableCell>
              <div className="grid gap-1">
                <strong className="break-words text-sm font-semibold leading-5">{token.name}</strong>
                <span className="text-xs leading-5 text-muted-foreground">{token.agent_name ?? "sem agente"}</span>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {token.scopes.map((scope) => <StatusPill className="min-h-7 px-2" key={scope}>{scope}</StatusPill>)}
                </div>
              </div>
            </TableCell>
            <TableCell><StatusPill tone={token.status === "active" ? "positive" : "warning"}>{token.status}</StatusPill></TableCell>
            <TableCell className="text-muted-foreground">{formatDateTime(token.last_used_at)}</TableCell>
            <TableCell className="text-muted-foreground">{formatDateTime(token.expires_at)}</TableCell>
            <TableCell className="text-right">
              {token.status === "active" ? (
                <form action={revokeMcpToken}>
                  <input type="hidden" name="id" value={token.id} />
                  <IconTextButton><Trash2 size={16} aria-hidden="true" />Revogar</IconTextButton>
                </form>
              ) : (
                <span className="text-xs text-muted-foreground">Revogado {formatDateTime(token.revoked_at)}</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function LogTable({ logs }: { logs: McpAccessLog[] }) {
  if (logs.length === 0) return <EmptyState>Sem chamadas MCP auditadas.</EmptyState>;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Recurso</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Agente</TableHead>
          <TableHead>Horário</TableHead>
          <TableHead className="text-right">Latência</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {logs.map((log) => (
          <TableRow key={log.id}>
            <TableCell>
              <strong className="break-all text-sm font-semibold">{log.resource}</strong>
              {log.error_message ? <p className="m-0 mt-1 text-xs leading-5 text-destructive">{log.error_message}</p> : null}
            </TableCell>
            <TableCell><StatusPill tone={log.status === "success" ? "positive" : "danger"}>{log.status}</StatusPill></TableCell>
            <TableCell className="text-muted-foreground">{log.agent_name ?? "-"}</TableCell>
            <TableCell className="text-muted-foreground">{formatDateTime(log.occurred_at)}</TableCell>
            <TableCell className="text-right tabular-nums">{log.latency_ms == null ? "-" : `${log.latency_ms}ms`}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
