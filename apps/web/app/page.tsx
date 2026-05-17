import {
  Activity,
  BarChart3,
  Bot,
  CirclePause,
  Database,
  FileDown,
  Gauge,
  KeyRound,
  LineChart,
  Settings2,
  ShieldCheck,
  Wallet,
} from "lucide-react";

import {
  apiUrl,
  appEnv,
  decisionRows,
  metrics,
  navItems,
  portfolioRows,
  riskItems,
} from "@/lib/mock-data";

const navIcons = [Gauge, LineChart, Wallet, BarChart3, Bot, Settings2, KeyRound, FileDown];

function toneClass(tone: string) {
  if (tone === "positive") return "metricPositive";
  if (tone === "warning") return "metricWarning";
  return "metricNeutral";
}

export default function DashboardPage() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">A</div>
          <div>
            <strong>Aurum</strong>
            <span>BTC Testnet</span>
          </div>
        </div>
        <nav className="nav" aria-label="Navegação principal">
          {navItems.map((item, index) => {
            const Icon = navIcons[index];
            return (
              <button className={index === 0 ? "navItem active" : "navItem"} key={item} title={item}>
                <Icon size={18} aria-hidden="true" />
                <span>{item}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Ambiente {appEnv}</p>
            <h1>Dashboard operacional</h1>
          </div>
          <div className="statusCluster" aria-label="Status do sistema">
            <span>
              <Database size={16} aria-hidden="true" />
              API {apiUrl}
            </span>
            <span>
              <ShieldCheck size={16} aria-hidden="true" />
              Read-only MCP planejado
            </span>
            <button className="pauseButton">
              <CirclePause size={18} aria-hidden="true" />
              Pausado
            </button>
          </div>
        </header>

        <section className="metricsGrid" aria-label="Indicadores principais">
          {metrics.map((metric) => (
            <article className="metricCard" key={metric.label}>
              <span>{metric.label}</span>
              <strong className={toneClass(metric.tone)}>{metric.value}</strong>
              <small>{metric.detail}</small>
            </article>
          ))}
        </section>

        <section className="contentGrid">
          <article className="panel marketPanel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Mercado</p>
                <h2>BTCUSDT 1h / 4h / 1d</h2>
              </div>
              <Activity size={20} aria-hidden="true" />
            </div>
            <div className="chartMock" aria-label="Curva mockada de preço BTCUSDT">
              <span style={{ height: "30%" }} />
              <span style={{ height: "46%" }} />
              <span style={{ height: "41%" }} />
              <span style={{ height: "58%" }} />
              <span style={{ height: "53%" }} />
              <span style={{ height: "74%" }} />
              <span style={{ height: "68%" }} />
              <span style={{ height: "82%" }} />
              <span style={{ height: "76%" }} />
              <span style={{ height: "88%" }} />
            </div>
            <div className="marketStats">
              <span>RSI 61.4</span>
              <span>ATR 1.92%</span>
              <span>Volume acima da média</span>
              <span>Sem rompimento confirmado</span>
            </div>
          </article>

          <article className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Carteira</p>
                <h2>Saldo e posição</h2>
              </div>
              <Wallet size={20} aria-hidden="true" />
            </div>
            <div className="tableList">
              {portfolioRows.map(([label, value, note]) => (
                <div className="tableRow" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>{note}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Decisões</p>
                <h2>Últimos ciclos</h2>
              </div>
              <Bot size={20} aria-hidden="true" />
            </div>
            <div className="decisionList">
              {decisionRows.map(([time, action, reason, status]) => (
                <div className="decisionRow" key={`${time}-${action}`}>
                  <time>{time}</time>
                  <strong>{action}</strong>
                  <span>{reason}</span>
                  <small>{status}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panelHeader">
              <div>
                <p className="eyebrow">Risco</p>
                <h2>Bloqueios e limites</h2>
              </div>
              <ShieldCheck size={20} aria-hidden="true" />
            </div>
            <div className="riskGrid">
              {riskItems.map(([label, value, note]) => (
                <div className="riskItem" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>{note}</small>
                </div>
              ))}
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
