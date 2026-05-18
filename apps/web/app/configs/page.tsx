import {
  CheckCircle2,
  CircleAlert,
  CirclePlay,
  FileJson,
  ListChecks,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import type { ReactNode } from "react";

import {
  activateRiskConfig,
  activateStrategyConfig,
  createRiskConfig,
  createStrategyConfig,
} from "@/app/configs/actions";
import { navItems } from "@/app/nav";
import { AppShell } from "@/components/app-shell";
import {
  CompactList,
  EmptyState,
  IconTextButton,
  InfoRow,
  JsonDetails,
  LabeledInput,
  LabeledTextarea,
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PrimaryButton,
  StatusPill,
  cx,
} from "@/components/ui";
import {
  compactJson,
  formatDateTime,
  getConfigsData,
  type RiskConfigItem,
  type StrategyConfigItem,
} from "@/lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

export default async function ConfigsPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const params = searchParams ? await searchParams : {};
  const success = single(params.success);
  const error = single(params.error);
  const data = await getConfigsData();
  const strategyResult = data.strategyConfigs;
  const riskResult = data.riskConfigs;
  const activeStrategy = data.activeStrategy.ok ? data.activeStrategy.data : null;
  const activeRisk = data.activeRisk.ok ? data.activeRisk.data : null;
  const strategyConfigs = strategyResult.ok ? strategyResult.data.configs : [];
  const riskConfigs = riskResult.ok ? riskResult.data.configs : [];
  const environment =
    (strategyResult.ok ? strategyResult.data.environment : null) ??
    (riskResult.ok ? riskResult.data.environment : null) ??
    "testnet";
  const symbol =
    (strategyResult.ok ? strategyResult.data.symbol : null) ??
    (riskResult.ok ? riskResult.data.symbol : null) ??
    "BTCUSDT";

  return (
    <AppShell navItems={navItems} activeLabel="Estratégias">
      <PageHeader
        eyebrow={`Configurações ${environment}`}
        title="Estratégia e risco"
        description="Versões autorizadas de estratégia e risco, sempre aplicadas de forma versionada e auditável."
        trailing={
          <StatusPill>
            <ShieldCheck size={16} aria-hidden="true" />
            {symbol} long-only
          </StatusPill>
        }
      />

      {success ? (
        <Notice tone="positive" icon={<CheckCircle2 size={18} aria-hidden="true" />}>
          {success}
        </Notice>
      ) : null}
      {error ? (
        <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>
          {error}
        </Notice>
      ) : null}
      {!strategyResult.ok || !riskResult.ok ? (
        <Notice tone="danger" icon={<CircleAlert size={18} aria-hidden="true" />}>
          API sem resposta completa:{" "}
          {[strategyResult, riskResult]
            .filter((result) => !result.ok)
            .map((result) => (result.ok ? "" : result.error))
            .join(" / ")}
        </Notice>
      ) : null}

      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1" aria-label="Configurações ativas">
        <ActiveConfigCard
          title="Estratégia ativa"
          icon={<SlidersHorizontal />}
          emptyText="Nenhuma estratégia ativa."
          rows={
            activeStrategy
              ? [
                  ["Versão", `v${activeStrategy.version}`],
                  ["Nome", activeStrategy.name],
                  ["Sinal", activeStrategy.signal_timeframe],
                  [
                    "Regime",
                    `${activeStrategy.regime_timeframe_primary} / ${activeStrategy.regime_timeframe_secondary}`,
                  ],
                  ["Ativada", formatDateTime(activeStrategy.activated_at)],
                ]
              : []
          }
        />
        <ActiveConfigCard
          title="Risco ativo"
          icon={<ShieldCheck />}
          emptyText="Nenhuma configuração de risco ativa."
          rows={
            activeRisk
              ? [
                  ["Versão", `v${activeRisk.version}`],
                  ["Nome", activeRisk.name],
                  ["Risco/trade", percentLabel(activeRisk.risk_per_trade_pct)],
                  ["Perda diária", percentLabel(activeRisk.daily_loss_limit_pct)],
                  ["Exposição máx.", percentLabel(activeRisk.max_exposure_pct)],
                ]
              : []
          }
        />
      </section>

      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <ConfigPanel eyebrow="Estratégia" title="Versões" icon={<ListChecks />}>
          <div className="grid gap-3.5">
            {strategyConfigs.length === 0 ? (
              <EmptyState>Sem versões de estratégia.</EmptyState>
            ) : (
              strategyConfigs.map((config) => (
                <StrategyConfigRow config={config} key={config.id} />
              ))
            )}
          </div>
        </ConfigPanel>

        <ConfigPanel eyebrow="Risco" title="Versões" icon={<ShieldCheck />}>
          <div className="grid gap-3.5">
            {riskConfigs.length === 0 ? (
              <EmptyState>Sem versões de risco.</EmptyState>
            ) : (
              riskConfigs.map((config) => <RiskConfigRow config={config} key={config.id} />)
            )}
          </div>
        </ConfigPanel>
      </section>

      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <ConfigPanel eyebrow="Nova versão" title="Estratégia" icon={<FileJson />}>
          <form action={createStrategyConfig} className="grid grid-cols-2 gap-3.5 max-md:grid-cols-1">
            <LabeledInput label="Versão" name="version" type="number" min="1" required />
            <LabeledInput label="Nome" name="name" defaultValue="breakout_trend_v1" />
            <LabeledInput label="Timeframe sinal" name="signal_timeframe" defaultValue="1h" />
            <LabeledInput label="Regime primário" name="regime_timeframe_primary" defaultValue="4h" />
            <LabeledInput label="Regime secundário" name="regime_timeframe_secondary" defaultValue="1d" />
            <LabeledTextarea
              label="Parâmetros JSON"
              name="parameters"
              placeholder='{"breakout_window":20,"rsi_min":50,"rsi_max":75}'
            />
            <LabeledInput label="Criado por" name="created_by" defaultValue="operator" />
            <div className="col-span-full">
              <PrimaryButton>Criar estratégia</PrimaryButton>
            </div>
          </form>
        </ConfigPanel>

        <ConfigPanel eyebrow="Nova versão" title="Risco" icon={<FileJson />}>
          <form action={createRiskConfig} className="grid grid-cols-2 gap-3.5 max-md:grid-cols-1">
            <LabeledInput label="Versão" name="version" type="number" min="1" required />
            <LabeledInput label="Nome" name="name" defaultValue="mvp_risk_v1" />
            <LabeledInput label="Risco/trade %" name="risk_per_trade_pct" placeholder="1.0" />
            <LabeledInput label="Perda diária %" name="daily_loss_limit_pct" placeholder="3.0" />
            <LabeledInput label="Exposição máx. %" name="max_exposure_pct" placeholder="50.0" />
            <LabeledTextarea
              label="Parâmetros JSON"
              name="parameters"
              placeholder='{"atr_stop_multiplier":2,"trailing_stop_pct":5}'
            />
            <LabeledInput label="Criado por" name="created_by" defaultValue="operator" />
            <div className="col-span-full">
              <PrimaryButton>Criar risco</PrimaryButton>
            </div>
          </form>
        </ConfigPanel>
      </section>
    </AppShell>
  );
}

function ActiveConfigCard({
  title,
  icon,
  rows,
  emptyText,
}: {
  title: string;
  icon: ReactNode;
  rows: Array<[string, string]>;
  emptyText: string;
}) {
  return (
    <Panel className="min-h-[318px]">
      <PanelHeader eyebrow="Ativa" title={title} icon={icon} />
      {rows.length === 0 ? (
        <EmptyState>{emptyText}</EmptyState>
      ) : (
        <CompactList>
          {rows.map(([label, value]) => (
            <InfoRow label={label} value={value} key={label} />
          ))}
        </CompactList>
      )}
    </Panel>
  );
}

function ConfigPanel({
  eyebrow,
  title,
  icon,
  children,
}: {
  eyebrow: string;
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <Panel>
      <PanelHeader eyebrow={eyebrow} title={title} icon={icon} />
      {children}
    </Panel>
  );
}

function StrategyConfigRow({ config }: { config: StrategyConfigItem }) {
  return (
    <article className={configRowClass(config.is_active)}>
      <ConfigRowHeader config={config} action={activateStrategyConfig} />
      <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <InfoRow label="Sinal" value={config.signal_timeframe} />
        <InfoRow label="Regime" value={`${config.regime_timeframe_primary} / ${config.regime_timeframe_secondary}`} />
        <InfoRow label="Criado" value={formatDateTime(config.created_at)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonDetails label="Parâmetros" value={compactJson(config.parameters)} icon={<FileJson size={16} aria-hidden="true" />} />
    </article>
  );
}

function RiskConfigRow({ config }: { config: RiskConfigItem }) {
  return (
    <article className={configRowClass(config.is_active)}>
      <ConfigRowHeader config={config} action={activateRiskConfig} />
      <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <InfoRow label="Risco/trade" value={percentLabel(config.risk_per_trade_pct)} />
        <InfoRow label="Perda diária" value={percentLabel(config.daily_loss_limit_pct)} />
        <InfoRow label="Exposição máx." value={percentLabel(config.max_exposure_pct)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonDetails label="Parâmetros" value={compactJson(config.parameters)} icon={<FileJson size={16} aria-hidden="true" />} />
    </article>
  );
}

function ConfigRowHeader({
  config,
  action,
}: {
  config: StrategyConfigItem | RiskConfigItem;
  action: (formData: FormData) => Promise<void>;
}) {
  return (
    <div className="flex items-start justify-between gap-4 max-md:flex-col max-md:items-stretch">
      <div>
        <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase leading-none tracking-[0.24px] text-ink-muted-48 before:block before:size-1.5 before:rounded-full before:bg-primary before:content-['']">
          v{config.version}
        </p>
        <h2 className="m-0 text-2xl font-medium leading-tight tracking-[-0.02em]">{config.name}</h2>
      </div>
      {config.is_active ? (
        <StatusPill tone="positive">
          <CheckCircle2 size={16} aria-hidden="true" />
          Ativa
        </StatusPill>
      ) : (
        <form action={action}>
          <input type="hidden" name="id" value={config.id} />
          <IconTextButton>
            <CirclePlay size={16} aria-hidden="true" />
            Ativar
          </IconTextButton>
        </form>
      )}
    </div>
  );
}

function configRowClass(isActive: boolean) {
  return cx(
    "grid gap-4 rounded-[18px] border border-hairline bg-canvas p-[18px]",
    isActive && "border-primary/45 bg-surface-pearl",
  );
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
