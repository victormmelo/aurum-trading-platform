export const serverApiUrl =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const publicApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const apiUrl = serverApiUrl;
export const appEnv = process.env.NEXT_PUBLIC_APP_ENV ?? "development";

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; data: null };

export type McpScope =
  | "read:market"
  | "read:portfolio"
  | "read:trades"
  | "read:decisions"
  | "read:config"
  | "read:reports";

export type BotStatus = {
  environment: string;
  symbol: string;
  status: string;
  trading_mode: string;
  last_cycle_at: string | null;
  paused_at: string | null;
  emergency_stopped_at: string | null;
  reason: string | null;
};

export type HealthStatus = {
  status: string;
  service: string;
  environment: string;
  version: string;
};

export type MarketSummary = {
  environment: string;
  symbol: string;
  snapshot: {
    id: string;
    captured_at: string;
    last_price: string;
    price_change_pct_24h: string | null;
    high_price_24h: string | null;
    low_price_24h: string | null;
    volume_24h: string | null;
    spread_bps: string | null;
    volatility_pct: string | null;
    trend_1h: string | null;
    trend_4h: string | null;
    trend_1d: string | null;
    indicators: Record<string, unknown>;
    source_payload: Record<string, unknown>;
  } | null;
};

export type PortfolioStatus = {
  environment: string;
  symbol: string;
  snapshot: {
    id: string;
    captured_at: string;
    usdt_balance: string;
    btc_balance: string;
    btc_market_price: string;
    btc_market_value: string;
    invested_value: string;
    average_cost: string;
    total_equity: string;
    exposure_pct: string;
    realized_pnl: string;
    unrealized_pnl: string;
    total_fees_usdt: string;
    source_payload: Record<string, unknown>;
  } | null;
  position: {
    id: string;
    asset: string;
    side: string;
    quantity: string;
    average_cost: string;
    remaining_cost: string;
    realized_pnl: string;
    total_fees_usdt: string;
    last_reconciled_at: string | null;
  } | null;
};

export type PortfolioReconciliationResponse = {
  environment: string;
  symbol: string;
  snapshot: NonNullable<PortfolioStatus["snapshot"]>;
  position: NonNullable<PortfolioStatus["position"]>;
};

export type Order = {
  id: string;
  environment?: string;
  exchange?: string;
  symbol?: string;
  decision_id?: string | null;
  bot_run_id?: string | null;
  external_order_id?: string | null;
  client_order_id?: string | null;
  side: string;
  status: string;
  order_type?: string;
  position_side?: string;
  requested_quantity: string;
  executed_quantity: string;
  quote_quantity: string | null;
  limit_price?: string | null;
  average_price: string | null;
  submitted_at: string | null;
  closed_at: string | null;
  raw_payload?: Record<string, unknown>;
};

export type OrdersResponse = {
  environment: string;
  symbol: string;
  orders: Order[];
};

export type ManualOrderResponse = {
  environment: string;
  symbol: string;
  order: Order;
};

export type OrderReconciliationResponse = {
  environment: string;
  symbol: string;
  reconciled_orders: Order[];
};

export type FillsResponse = {
  environment: string;
  symbol: string;
  fills: Array<{
    id: string;
    filled_at: string;
    price: string;
    quantity: string;
    quote_quantity: string;
    fee_amount: string | null;
    fee_asset: string | null;
    fee_estimated_usdt: string | null;
  }>;
};

export type Decision = {
  id: string;
  environment: string;
  symbol: string;
  bot_run_id: string | null;
  strategy_config_id: string | null;
  risk_config_id: string | null;
  market_snapshot_id: string | null;
  decided_at: string;
  decision: "COMPRA" | "VENDA" | "MANTER_POSICAO" | "NAO_OPERAR";
  reason: string;
  reason_payload: Record<string, unknown>;
  indicators: Record<string, unknown>;
  intended_order: Record<string, unknown>;
  execution_result: Record<string, unknown>;
  portfolio_state: Record<string, unknown>;
};

export type DecisionsResponse = {
  environment: string;
  symbol: string;
  decisions: Decision[];
};

export type StrategyConfig = {
  id: string;
  version: number;
  name: string;
  signal_timeframe: string;
  regime_timeframe_primary: string;
  regime_timeframe_secondary: string;
  parameters: Record<string, unknown>;
  is_active: boolean;
} | null;

export type RiskConfig = {
  id: string;
  version: number;
  name: string;
  risk_per_trade_pct: string | null;
  daily_loss_limit_pct: string | null;
  max_exposure_pct: string | null;
  parameters: Record<string, unknown>;
  is_active: boolean;
} | null;

export type McpStatus = {
  environment: string;
  auth_enabled: boolean;
  allowed_scopes: McpScope[];
  tools: string[];
};

export type McpToken = {
  id: string;
  environment: string;
  name: string;
  agent_name: string | null;
  scopes: McpScope[];
  status: string;
  expires_at: string | null;
  revoked_at: string | null;
  last_used_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type McpTokenCreateResponse = McpToken & {
  token: string;
};

export type McpTokensResponse = {
  environment: string;
  tokens: McpToken[];
};

export type McpAccessLog = {
  id: string;
  environment: string;
  token_id: string | null;
  agent_name: string | null;
  resource: string;
  arguments: Record<string, unknown>;
  status: string;
  status_code: number | null;
  error_message: string | null;
  latency_ms: number | null;
  occurred_at: string;
  created_at: string | null;
};

export type McpAccessLogsResponse = {
  environment: string;
  logs: McpAccessLog[];
};

export async function fetchApi<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${serverApiUrl}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return { ok: false, error: `${response.status} ${response.statusText}`, data: null };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown API error",
      data: null,
    };
  }
}

export async function postApi<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${serverApiUrl}${path}`, {
      method: "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
    });
    if (!response.ok) {
      const detail = await responseErrorDetail(response);
      return {
        ok: false,
        error: detail || `${response.status} ${response.statusText}`,
        data: null,
      };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown API error",
      data: null,
    };
  }
}

async function responseErrorDetail(response: Response) {
  try {
    const payload = (await response.json()) as unknown;
    if (payload && typeof payload === "object" && "detail" in payload) {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (detail && typeof detail === "object" && "reason" in detail) {
        const reason = (detail as { reason?: unknown }).reason;
        if (typeof reason === "string") return reason;
      }
      return JSON.stringify(detail);
    }
  } catch {
    return "";
  }
  return "";
}

export async function getMcpData() {
  const [status, tokens, logs] = await Promise.all([
    fetchApi<McpStatus>("/mcp/status"),
    fetchApi<McpTokensResponse>("/mcp/tokens"),
    fetchApi<McpAccessLogsResponse>("/mcp/audit-log?limit=20"),
  ]);

  return { status, tokens, logs };
}

export type ExportJob = {
  id: string;
  environment: string;
  symbol: string;
  status: "completed";
  format: "csv" | "txt" | "pdf";
  sections: Array<"market" | "portfolio" | "operations" | "decisions">;
  content_type: string;
  filename: string;
  created_at: string;
  completed_at: string;
  filters: Record<string, unknown>;
  content: string;
};

export async function getDashboardData() {
  const [
    health,
    bot,
    market,
    portfolio,
    orders,
    fills,
    decisions,
    strategyConfig,
    riskConfig,
  ] = await Promise.all([
    fetchApi<HealthStatus>("/health"),
    fetchApi<BotStatus>("/bot/status"),
    fetchApi<MarketSummary>("/market/summary"),
    fetchApi<PortfolioStatus>("/portfolio/status"),
    fetchApi<OrdersResponse>("/operations/orders?limit=5"),
    fetchApi<FillsResponse>("/operations/fills?limit=5"),
    fetchApi<DecisionsResponse>("/decisions?limit=5"),
    fetchApi<StrategyConfig>("/configs/strategy/active"),
    fetchApi<RiskConfig>("/configs/risk/active"),
  ]);

  return { health, bot, market, portfolio, orders, fills, decisions, strategyConfig, riskConfig };
}

export type StrategyConfigItem = {
  id: string;
  environment: string;
  version: number;
  name: string;
  symbol: string;
  signal_timeframe: string;
  regime_timeframe_primary: string;
  regime_timeframe_secondary: string;
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_by: string | null;
  activated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type RiskConfigItem = {
  id: string;
  environment: string;
  version: number;
  name: string;
  symbol: string;
  risk_per_trade_pct: string | null;
  daily_loss_limit_pct: string | null;
  max_exposure_pct: string | null;
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_by: string | null;
  activated_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type StrategyConfigsResponse = {
  environment: string;
  symbol: string;
  configs: StrategyConfigItem[];
};

export type RiskConfigsResponse = {
  environment: string;
  symbol: string;
  configs: RiskConfigItem[];
};

export async function getConfigsData() {
  const [strategyConfigs, riskConfigs, activeStrategy, activeRisk, bot, market, portfolio] = await Promise.all([
    fetchApi<StrategyConfigsResponse>("/configs/strategy"),
    fetchApi<RiskConfigsResponse>("/configs/risk"),
    fetchApi<StrategyConfigItem | null>("/configs/strategy/active"),
    fetchApi<RiskConfigItem | null>("/configs/risk/active"),
    fetchApi<BotStatus>("/bot/status"),
    fetchApi<MarketSummary>("/market/summary"),
    fetchApi<PortfolioStatus>("/portfolio/status"),
  ]);

  return { strategyConfigs, riskConfigs, activeStrategy, activeRisk, bot, market, portfolio };
}

export function formatMoney(value: string | null | undefined, currency = "USDT") {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value} ${currency}`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 2 })} ${currency}`;
}

export function formatQuantity(value: string | null | undefined, asset = "BTC") {
  if (value == null || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return `${value} ${asset}`;
  return `${number.toLocaleString("en-US", { maximumFractionDigits: 8 })} ${asset}`;
}

export function formatDateTime(value: string | null | undefined) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo",
  }).format(date);
}

export function compactJson(value: Record<string, unknown>) {
  const entries = Object.entries(value);
  if (entries.length === 0) return "{}";
  return JSON.stringify(value, null, 2);
}
