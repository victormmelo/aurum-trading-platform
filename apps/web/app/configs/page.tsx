import {
  Bot,
  CheckCircle2,
  CircleAlert,
  CircleDot,
  CirclePlay,
  Database,
  FileJson,
  LineChart,
  ListChecks,
  ShieldCheck,
  SlidersHorizontal,
  Wallet,
} from "lucide-react";
import type { ReactNode } from "react";

import {
  activateRiskConfig,
  activateStrategyConfig,
  createGuidedRobotConfig,
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
  Notice,
  PageHeader,
  Panel,
  PanelHeader,
  PrimaryButton,
  StatPill,
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
type ReadinessTone = "positive" | "warning" | "neutral";

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
  const bot = data.bot.ok ? data.bot.data : null;
  const market = data.market.ok ? data.market.data.snapshot : null;
  const portfolio = data.portfolio.ok ? data.portfolio.data.snapshot : null;
  const environment =
    (strategyResult.ok ? strategyResult.data.environment : null) ??
    (riskResult.ok ? riskResult.data.environment : null) ??
    bot?.environment ??
    "testnet";
  const symbol =
    (strategyResult.ok ? strategyResult.data.symbol : null) ??
    (riskResult.ok ? riskResult.data.symbol : null) ??
    bot?.symbol ??
    "BTCUSDT";
  const nextStrategyVersion = nextVersion(strategyConfigs);
  const nextRiskVersion = nextVersion(riskConfigs);

  const readiness = [
    {
      label: "Estratégia ativa",
      detail: activeStrategy
        ? `${activeStrategy.name} esta ativa`
        : "Crie e ative uma estrategia para o robo saber quando comprar.",
      tone: activeStrategy ? "positive" : "neutral",
      icon: <SlidersHorizontal size={18} aria-hidden="true" />,
    },
    {
      label: "Risco ativo",
      detail: activeRisk
        ? `${percentLabel(activeRisk.risk_per_trade_pct)} por operacao, ${percentLabel(activeRisk.daily_loss_limit_pct)} no dia`
        : "Defina limites para tamanho de posicao, perda diaria e exposicao.",
      tone: activeRisk ? "positive" : "neutral",
      icon: <ShieldCheck size={18} aria-hidden="true" />,
    },
    {
      label: "Estado operacional do robo",
      detail: bot
        ? bot.status === "running"
          ? "Robo liberado para ciclos."
          : `Robo em ${bot.status}; ele nao abre novas operacoes assim.`
        : "Estado ainda nao cadastrado no ambiente.",
      tone: bot?.status === "running" ? "positive" : bot ? "warning" : "neutral",
      icon: <Bot size={18} aria-hidden="true" />,
    },
    {
      label: "Carteira disponivel",
      detail: portfolio
        ? `Snapshot de carteira capturado em ${formatDateTime(portfolio.captured_at)}.`
        : "O ciclo precisa de saldo/snapshot para calcular tamanho da compra.",
      tone: portfolio ? "positive" : "warning",
      icon: <Wallet size={18} aria-hidden="true" />,
    },
    {
      label: "Dados de mercado",
      detail: market
        ? `Ultimo snapshot em ${formatDateTime(market.captured_at)}.`
        : "Importe candles e gere snapshot antes de validar decisoes.",
      tone: market ? "positive" : "warning",
      icon: <Database size={18} aria-hidden="true" />,
    },
  ] satisfies Array<{
    label: string;
    detail: string;
    tone: ReadinessTone;
    icon: ReactNode;
  }>;

  return (
    <AppShell navItems={navItems} activeLabel="Estratégias">
      <PageHeader
        eyebrow={`Ambiente ${environment}`}
        title="Configurar robô"
        description="Prepare o robo BTCUSDT em Testnet com uma estrategia orientada e limites de risco claros, sem editar JSON ou campos tecnicos."
        trailing={
          <StatusPill>
            <ShieldCheck size={16} aria-hidden="true" />
            {symbol} · long-only · dry-run
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

      <section className="grid grid-cols-[minmax(0,1.35fr)_minmax(340px,0.65fr)] gap-4 max-xl:grid-cols-1">
        <Panel>
          <PanelHeader eyebrow="Assistente" title="Preparar estrategia e risco" icon={<Bot />} />
          <form action={createGuidedRobotConfig} className="grid gap-6">
            <input type="hidden" name="strategy_version" value={nextStrategyVersion} />
            <input type="hidden" name="risk_version" value={nextRiskVersion} />

            <GuidedStep
              number="1"
              title="Objetivo do robo"
              description="O robo observa BTCUSDT na Binance Spot Testnet. Ele compra apenas comprado, nao usa alavancagem e neste ciclo registra intencoes sem enviar ordem real."
            >
              <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
                <StatPill label="Mercado" value={symbol} />
                <StatPill label="Ambiente" value={environment} />
                <StatPill label="Direcao" value="Somente compra" />
                <StatPill label="Execucao" value="Dry-run" />
              </div>
            </GuidedStep>

            <GuidedStep
              number="2"
              title="Como o robo compra"
              description="Ele so compra quando houver rompimento com tendencia favoravel, volume forte e RSI dentro da faixa operacional."
            >
              <input type="hidden" name="major_trend" value="1d" />
              <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-1">
                <LabeledInput label="Periodo de decisao" name="decision_period" defaultValue="1h" />
                <LabeledInput label="Confirmacao de tendencia" name="trend_confirmation" defaultValue="4h" />
                <StatPill label="Tendencia maior" value="1d" />
              </div>
              <p className="m-0 text-sm leading-6 tracking-[-0.224px] text-ink-muted-48">
                A tendencia maior e salva para auditoria da configuracao. Hoje a decisao do worker usa o periodo de decisao e a confirmacao de tendencia.
              </p>
            </GuidedStep>

            <GuidedStep
              number="3"
              title="Quanto o robo pode arriscar"
              description="A perda diaria maxima bloqueia novas compras se o limite for atingido. A exposicao maxima evita concentrar demais a carteira em BTC."
            >
              <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-1">
                <LabeledInput label="Risco por operacao %" name="risk_per_trade_pct" defaultValue="1" />
                <LabeledInput label="Perda diaria maxima %" name="daily_loss_limit_pct" defaultValue="2" />
                <LabeledInput label="Exposicao maxima %" name="max_exposure_pct" defaultValue="50" />
              </div>
            </GuidedStep>

            <GuidedStep
              number="4"
              title="Revisar e ativar"
              description="Ao confirmar, o sistema cria novas versoes, ativa estrategia e risco, e deixa o restante da prontidao visivel no checklist."
            >
              <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
                <SummaryCard
                  title={`Rompimento com tendencia v${nextStrategyVersion}`}
                  lines={[
                    "Compra somente quando o preco rompe a maxima recente.",
                    "Confirma tendencia antes de abrir nova posicao.",
                    "Nao opera vendido e nao usa alavancagem.",
                  ]}
                />
                <SummaryCard
                  title={`Risco conservador v${nextRiskVersion}`}
                  lines={[
                    "Arrisca 1% por operacao por padrao.",
                    "Bloqueia novas compras ao atingir 2% de perda diaria.",
                    "Limita exposicao total em BTC a 50% da carteira.",
                  ]}
                />
              </div>
              <PrimaryButton>Criar e ativar configuracao</PrimaryButton>
            </GuidedStep>
          </form>
        </Panel>

        <Panel>
          <PanelHeader eyebrow="Prontidao" title="Antes de rodar" icon={<ListChecks />} />
          <div className="grid gap-3">
            {readiness.map((item) => (
              <ReadinessRow key={item.label} {...item} />
            ))}
          </div>
        </Panel>
      </section>

      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1" aria-label="Configurações ativas">
        <ActiveConfigCard
          title="Estratégia ativa"
          icon={<SlidersHorizontal />}
          emptyText="Nenhuma estrategia ativa."
          rows={
            activeStrategy
              ? [
                  ["Versao", `v${activeStrategy.version}`],
                  ["Nome", activeStrategy.name],
                  ["Periodo de decisao", activeStrategy.signal_timeframe],
                  ["Confirmacao", activeStrategy.regime_timeframe_primary],
                  ["Ativada", formatDateTime(activeStrategy.activated_at)],
                ]
              : []
          }
        />
        <ActiveConfigCard
          title="Risco ativo"
          icon={<ShieldCheck />}
          emptyText="Nenhuma configuracao de risco ativa."
          rows={
            activeRisk
              ? [
                  ["Versao", `v${activeRisk.version}`],
                  ["Nome", activeRisk.name],
                  ["Risco por operacao", percentLabel(activeRisk.risk_per_trade_pct)],
                  ["Perda diaria maxima", percentLabel(activeRisk.daily_loss_limit_pct)],
                  ["Exposicao maxima", percentLabel(activeRisk.max_exposure_pct)],
                ]
              : []
          }
        />
      </section>

      <section className="grid grid-cols-2 gap-[18px] max-md:grid-cols-1">
        <ConfigPanel eyebrow="Historico" title="Versoes de estrategia" icon={<LineChart />}>
          <div className="grid gap-3.5">
            {strategyConfigs.length === 0 ? (
              <EmptyState>Sem versoes de estrategia.</EmptyState>
            ) : (
              strategyConfigs.map((config) => (
                <StrategyConfigRow config={config} key={config.id} />
              ))
            )}
          </div>
        </ConfigPanel>

        <ConfigPanel eyebrow="Historico" title="Versoes de risco" icon={<ShieldCheck />}>
          <div className="grid gap-3.5">
            {riskConfigs.length === 0 ? (
              <EmptyState>Sem versoes de risco.</EmptyState>
            ) : (
              riskConfigs.map((config) => <RiskConfigRow config={config} key={config.id} />)
            )}
          </div>
        </ConfigPanel>
      </section>
    </AppShell>
  );
}

function GuidedStep({
  number,
  title,
  description,
  children,
}: {
  number: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="grid gap-4 rounded-lg border border-hairline bg-surface-pearl p-4">
      <div className="flex items-start gap-3">
        <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-semibold text-on-primary">
          {number}
        </span>
        <div className="min-w-0">
          <h3 className="m-0 text-[21px] font-semibold leading-[1.2] tracking-[-0.224px]">{title}</h3>
          <p className="m-0 mt-2 text-[15px] leading-6 tracking-[-0.224px] text-ink-muted-48">{description}</p>
        </div>
      </div>
      <div className="grid gap-3">{children}</div>
    </section>
  );
}

function SummaryCard({ title, lines }: { title: string; lines: string[] }) {
  return (
    <div className="grid gap-3 rounded-lg border border-hairline bg-canvas p-4">
      <h3 className="m-0 text-[17px] font-semibold leading-[1.24] tracking-[-0.374px]">{title}</h3>
      <ul className="m-0 grid gap-2 p-0 text-sm leading-6 tracking-[-0.224px] text-ink-muted-48">
        {lines.map((line) => (
          <li className="flex gap-2" key={line}>
            <CheckCircle2 className="mt-1 shrink-0 text-primary" size={15} aria-hidden="true" />
            <span>{line}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ReadinessRow({
  label,
  detail,
  tone,
  icon,
}: {
  label: string;
  detail: string;
  tone: ReadinessTone;
  icon: ReactNode;
}) {
  const statusIcon =
    tone === "positive" ? (
      <CheckCircle2 size={16} aria-hidden="true" />
    ) : tone === "warning" ? (
      <CircleAlert size={16} aria-hidden="true" />
    ) : (
      <CircleDot size={16} aria-hidden="true" />
    );

  return (
    <div
      className={cx(
        "grid gap-2 rounded-lg border bg-canvas p-4",
        tone === "positive" && "border-primary/35",
        tone === "warning" && "border-hairline bg-surface-pearl",
        tone === "neutral" && "border-hairline",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="text-primary">{icon}</span>
          <strong className="min-w-0 text-[15px] font-semibold leading-[1.24] tracking-[-0.224px]">{label}</strong>
        </div>
        <span className={tone === "positive" ? "text-primary" : "text-ink-muted-48"}>{statusIcon}</span>
      </div>
      <p className="m-0 text-sm leading-6 tracking-[-0.224px] text-ink-muted-48">{detail}</p>
    </div>
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
        <InfoRow label="Periodo de decisao" value={config.signal_timeframe} />
        <InfoRow label="Confirmacao" value={config.regime_timeframe_primary} />
        <InfoRow label="Criado" value={formatDateTime(config.created_at)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonDetails label="Detalhes avancados" value={compactJson(config.parameters)} icon={<FileJson size={16} aria-hidden="true" />} />
    </article>
  );
}

function RiskConfigRow({ config }: { config: RiskConfigItem }) {
  return (
    <article className={configRowClass(config.is_active)}>
      <ConfigRowHeader config={config} action={activateRiskConfig} />
      <div className="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <InfoRow label="Risco por operacao" value={percentLabel(config.risk_per_trade_pct)} />
        <InfoRow label="Perda diaria maxima" value={percentLabel(config.daily_loss_limit_pct)} />
        <InfoRow label="Exposicao maxima" value={percentLabel(config.max_exposure_pct)} />
        <InfoRow label="Ativado" value={formatDateTime(config.activated_at)} />
      </div>
      <JsonDetails label="Detalhes avancados" value={compactJson(config.parameters)} icon={<FileJson size={16} aria-hidden="true" />} />
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
    "grid gap-4 rounded-lg border border-hairline bg-canvas p-[18px]",
    isActive && "border-primary/45 bg-surface-pearl",
  );
}

function nextVersion(configs: Array<StrategyConfigItem | RiskConfigItem>) {
  return Math.max(0, ...configs.map((config) => config.version)) + 1;
}

function percentLabel(value: string | null | undefined) {
  return value == null || value === "" ? "-" : `${value}%`;
}

function single(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}
