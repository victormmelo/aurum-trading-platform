export const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const appEnv = process.env.NEXT_PUBLIC_APP_ENV ?? "development";

export const navItems = [
  "Dashboard",
  "Mercado",
  "Carteira",
  "Operações",
  "Decisões",
  "Estratégias",
  "MCP",
  "Exportações",
];

export const metrics = [
  { label: "BTCUSDT", value: "$104,280.42", detail: "+1.84% 24h", tone: "positive" },
  { label: "Regime 4h", value: "Positivo", detail: "Preço acima da MM200", tone: "positive" },
  { label: "Robô", value: "Pausado", detail: "Testnet aguardando validação", tone: "warning" },
  { label: "Exposição", value: "0.00%", detail: "Sem posição aberta", tone: "neutral" },
];

export const portfolioRows = [
  ["USDT disponível", "10,000.00", "Testnet"],
  ["BTC em carteira", "0.00000000", "Conciliado"],
  ["Patrimônio total", "10,000.00 USDT", "Mock"],
  ["PnL realizado", "0.00 USDT", "Sem trades"],
];

export const decisionRows = [
  ["12:00", "NAO_OPERAR", "Robô pausado manualmente", "Registrado"],
  ["11:00", "NAO_OPERAR", "Sem rompimento de máxima 20 candles", "Registrado"],
  ["10:00", "MANTER_POSICAO", "Sem posição aberta para gerenciar", "Registrado"],
];

export const riskItems = [
  ["Perda diária", "0.00%", "Limite 2.00%"],
  ["Spread", "0.02%", "Aceitável"],
  ["ATR stop", "Inativo", "Sem posição"],
  ["API Binance", "Testnet", "Sem chave real"],
];
