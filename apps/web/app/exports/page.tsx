import { CheckCircle2, CircleAlert, FileDown } from "lucide-react";

import { createExport } from "@/app/exports/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import { CompactList, InfoRow, LabeledInput, Notice, PageHeader, Panel, PanelHeader, PrimaryButton, StatusPill } from "@/components/ui";
import { fetchApi, formatDateTime, type ExportJob } from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

export default async function ExportsPage({ searchParams }: { searchParams?: Promise<SearchParams> }) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
  const exportId = single(params.id);
  const jobResult = exportId ? await fetchApi<ExportJob>(`/exports/${exportId}`) : null;
  const job = jobResult?.ok ? jobResult.data : null;

  return (
    <AppShell navItems={navItems} activeLabel="Exportações">
      <PageHeader eyebrow="Relatórios" title="Exportações operacionais" trailing={<StatusPill><FileDown size={16} aria-hidden="true" />PDF / TXT / CSV</StatusPill>} />
      {success ? <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>{success}</Notice> : null}
      {error ? <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>{error}</Notice> : null}
      {jobResult && !jobResult.ok ? <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>Exportação não encontrada: {jobResult.error}</Notice> : null}

      <section className="grid grid-cols-[minmax(0,0.8fr)_minmax(380px,1.2fr)] gap-[18px] max-lg:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Nova exportação" title="Escopo e formato" icon={<FileDown />} />
          <form action={createExport} className="grid gap-3.5">
            <label className="grid gap-[7px]">
              <span className="text-[13px] text-ink-muted-48">Formato</span>
              <select className="min-h-11 rounded-lg border border-hairline bg-canvas px-3.5" name="format" defaultValue="txt">
                <option value="txt">TXT</option>
                <option value="csv">CSV</option>
                <option value="pdf">PDF</option>
              </select>
            </label>
            <div className="grid grid-cols-2 gap-2 max-md:grid-cols-1">
              {["market", "portfolio", "operations", "decisions"].map((section) => (
                <label className="flex min-h-11 items-center gap-2 rounded-lg border border-hairline bg-canvas px-3.5 text-sm" key={section}>
                  <input name="sections" type="checkbox" value={section} defaultChecked />
                  {section}
                </label>
              ))}
            </div>
            <LabeledInput label="Início" name="period_start" type="datetime-local" />
            <LabeledInput label="Fim" name="period_end" type="datetime-local" />
            <PrimaryButton>Gerar exportação</PrimaryButton>
          </form>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Resultado" title={job?.filename ?? "Nenhuma exportação selecionada"} icon={<FileDown />} />
          {job ? (
            <CompactList>
              <InfoRow label="Formato" value={job.format} />
              <InfoRow label="Status" value={job.status} />
              <InfoRow label="Criada" value={formatDateTime(job.created_at)} />
              <InfoRow label="Seções" value={job.sections.join(", ")} />
              <pre className="m-0 max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-lg bg-ink p-4 font-mono text-xs leading-relaxed text-on-primary">{job.content}</pre>
            </CompactList>
          ) : (
            <p className="m-0 text-ink-muted-48">Gere uma exportação para visualizar o conteúdo retornado pela API.</p>
          )}
        </Panel>
      </section>
    </AppShell>
  );
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
