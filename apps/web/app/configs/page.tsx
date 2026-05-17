import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  CirclePlay,
  FileJson,
  ListChecks,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import {
  activateRiskConfig,
  activateStrategyConfig,
  createRiskConfig,
  createStrategyConfig,
} from "@/app/configs/actions";
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
    <main className="detailShell">
      <header className="detailHeader">
        <Link className="backLink" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          Dashboard
        </Link>
        <div>
          <p className="eyebrow">Configurações {environment}</p>
          <h1>Estratégia e risco</h1>
        </div>
        <span className="statusPill">
          <ShieldCheck size={16} aria-hidden="true" />
          {symbol} long-only
        </span>
      </header>

      {success ? (
        <section className="noticePanel success">
          <CheckCircle2 size={18} aria-hidden="true" />
          <span>{success}</span>
        </section>
      ) : null}
      {error ? (
        <section className="noticePanel danger">
          <CircleAlert size={18} aria-hidden="true" />
          <span>{error}</span>
        </section>
      ) : null}
      {!strategyResult.ok || !riskResult.ok ? (
        <section className="noticePanel danger">
          <CircleAlert size={18} aria-hidden="true" />
          <span>
            API sem resposta completa:{" "}
            {[strategyResult, riskResult]
              .filter((result) => !result.ok)
              .map((result) => (result.ok ? "" : result.error))
              .join(" / ")}
          </span>
        </section>
      ) : null}

      <section className="configHeroGrid" aria-label="Configurações ativas">
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

      <section className="configGrid">
        <ConfigPanel
          eyebrow="Estratégia"
          title="Versões"
          icon={<ListChecks />}
          emptyText="Sem versões de estratégia."
        >
          <div className="configList">
            {strategyConfigs.length === 0 ? (
              <div className="emptyState">Sem versões de estratégia.</div>
            ) : (
              strategyConfigs.map((config) => (
                <StrategyConfigRow config={config} key={config.id} />
              ))
            )}
          </div>
        </ConfigPanel>

        <ConfigPanel
          eyebrow="Risco"
          title="Versões"
          icon={<ShieldCheck />}
          emptyText="Sem versões de risco."
        >
          <div className="configList">
            {riskConfigs.length === 0 ? (
              <div className="emptyState">Sem versões de risco.</div>
            ) : (
              riskConfigs.map((config) => <RiskConfigRow config={config} key={config.id} />)
            )}
          </div>
        </ConfigPanel>
      </section>

      <section className="configGrid">
        <ConfigPanel
          eyebrow="Nova versão"
          title="Estratégia"
          icon={<FileJson />}
          emptyText=""
        >
          <form action={createStrategyConfig} className="configForm">
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
            <button className="primaryButton" type="submit">
              Criar estratégia
            </button>
          </form>
        </ConfigPanel>

        <ConfigPanel eyebrow="Nova versão" title="Risco" icon={<FileJson />} emptyText="">
          <form action={createRiskConfig} className="configForm">
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
            <button className="primaryButton" type="submit">
              Criar risco
            </button>
          </form>
        </ConfigPanel>
      </section>
    </main>
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
    <article className="panel activeConfigCard">
      <PanelHeader eyebrow="Ativa" title={title} icon={icon} />
      {rows.length === 0 ? (
        <div className="emptyState">{emptyText}</div>
      ) : (
        <div className="tableList">
          {rows.map(([label, value]) => (
            <InfoRow label={label} value={value} key={label} />
          ))}
        </div>
      )}
    </article>
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
  emptyText: string;
  children: ReactNode;
}) {
  return (
    <article className="panel">
      <PanelHeader eyebrow={eyebrow} title={title} icon={icon} />
      {children}
    </article>
  );
}

function StrategyConfigRow({ config }: { config: StrategyConfigItem }) {
  return (
    <article className={config.is_active ? "configRow active" : "configRow"}>
      <ConfigRowHeader config={config} action={activateStrategyConfig} />
      <div className="configMetaGrid">
        <InfoRow label="Sinal" value={config.signal_timeframe} />
        <InfoRow label="Regime" value={`${config.regime_timeframe_primary} / ${config.regime_timeframe_secondary}`} />
        <InfoRow label="Criado" value={formatDateTime(config.created_at)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonPreview value={config.parameters} />
    </article>
  );
}

function RiskConfigRow({ config }: { config: RiskConfigItem }) {
  return (
    <article className={config.is_active ? "configRow active" : "configRow"}>
      <ConfigRowHeader config={config} action={activateRiskConfig} />
      <div className="configMetaGrid">
        <InfoRow label="Risco/trade" value={percentLabel(config.risk_per_trade_pct)} />
        <InfoRow label="Perda diária" value={percentLabel(config.daily_loss_limit_pct)} />
        <InfoRow label="Exposição máx." value={percentLabel(config.max_exposure_pct)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonPreview value={config.parameters} />
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
    <div className="configRowHeader">
      <div>
        <p className="eyebrow">v{config.version}</p>
        <h2>{config.name}</h2>
      </div>
      {config.is_active ? (
        <span className="statusPill ok">
          <CheckCircle2 size={16} aria-hidden="true" />
          Ativa
        </span>
      ) : (
        <form action={action}>
          <input type="hidden" name="id" value={config.id} />
          <button className="iconTextButton" type="submit">
            <CirclePlay size={16} aria-hidden="true" />
            Ativar
          </button>
        </form>
      )}
    </div>
  );
}

function PanelHeader({
  eyebrow,
  title,
  icon,
}: {
  eyebrow: string;
  title: string;
  icon: ReactNode;
}) {
  return (
    <div className="panelHeader">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      <span className="iconOrbit">{icon}</span>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="tableRow">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function JsonPreview({ value }: { value: Record<string, unknown> }) {
  return (
    <details className="jsonDetails">
      <summary>
        <FileJson size={16} aria-hidden="true" />
        Parâmetros
      </summary>
      <pre>{compactJson(value)}</pre>
    </details>
  );
}

function LabeledInput({
  label,
  name,
  type = "text",
  defaultValue,
  placeholder,
  min,
  required,
}: {
  label: string;
  name: string;
  type?: string;
  defaultValue?: string;
  placeholder?: string;
  min?: string;
  required?: boolean;
}) {
  return (
    <label className="fieldGroup">
      <span>{label}</span>
      <input
        name={name}
        type={type}
        defaultValue={defaultValue}
        placeholder={placeholder}
        min={min}
        required={required}
      />
    </label>
  );
}

function LabeledTextarea({
  label,
  name,
  placeholder,
}: {
  label: string;
  name: string;
  placeholder: string;
}) {
  return (
    <label className="fieldGroup wide">
      <span>{label}</span>
      <textarea name={name} placeholder={placeholder} rows={5} />
    </label>
  );
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
