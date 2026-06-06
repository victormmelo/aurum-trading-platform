"""Automated BTC market report: data collection, AI analysis, Telegram dispatch."""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.strategy.indicators import simple_moving_average

logger = logging.getLogger(__name__)

_BINANCE_PUBLIC = "https://api.binance.com/api/v3"
_TIMEOUT = 10.0
_SMA_SHORT_PERIOD = 50
_SMA_LONG_PERIOD = 200
_KLINES_LIMIT = 210  # enough history for SMA 200


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def _get(url: str, params: dict[str, str] | None = None) -> Any:
    """HTTP GET with timeout. Returns parsed JSON or None on any error."""
    try:
        resp = httpx.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("HTTP GET failed url=%s: %s", url, exc)
        return None


def fetch_ticker() -> dict[str, Decimal] | None:
    """24hr price ticker from Binance public API."""
    data = _get(f"{_BINANCE_PUBLIC}/ticker/24hr", {"symbol": "BTCUSDT"})
    if not isinstance(data, dict):
        return None
    try:
        return {
            "price": Decimal(data["lastPrice"]),
            "change_pct": Decimal(data["priceChangePercent"]),
            "volume_usdt": Decimal(data["quoteVolume"]),
        }
    except (KeyError, Exception) as exc:  # noqa: BLE001
        logger.error("Ticker parse error: %s", exc)
        return None


def fetch_kline_closes() -> list[Decimal] | None:
    """Hourly close prices from Binance public API for MA calculation."""
    data = _get(
        f"{_BINANCE_PUBLIC}/klines",
        {"symbol": "BTCUSDT", "interval": "1h", "limit": str(_KLINES_LIMIT)},
    )
    if not isinstance(data, list) or len(data) < _SMA_LONG_PERIOD:
        logger.error("Klines fetch returned insufficient data length=%s", len(data) if isinstance(data, list) else "none")
        return None
    try:
        return [Decimal(kline[4]) for kline in data]  # index 4 = close price
    except Exception as exc:  # noqa: BLE001
        logger.error("Klines parse error: %s", exc)
        return None


def fetch_fear_greed() -> dict[str, Any] | None:
    """Fear & Greed Index from alternative.me."""
    data = _get("https://api.alternative.me/fng/", {"limit": "1"})
    if not isinstance(data, dict) or not data.get("data"):
        return None
    try:
        item = data["data"][0]
        return {"value": int(item["value"]), "label": item["value_classification"]}
    except (KeyError, IndexError, ValueError) as exc:
        logger.error("Fear & Greed parse error: %s", exc)
        return None


def fetch_news(news_api_key: str | None = None) -> list[str]:
    """News titles: CryptoPanic first, NewsAPI as fallback."""
    data = _get(
        "https://cryptopanic.com/api/v1/posts/",
        {"auth_token": "free", "currencies": "BTC", "kind": "news", "limit": "5"},
    )
    if isinstance(data, dict) and data.get("results"):
        return [r["title"] for r in data["results"][:5] if isinstance(r, dict) and "title" in r]

    if not news_api_key:
        return []
    data = _get(
        "https://newsapi.org/v2/everything",
        {
            "q": "bitcoin",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": "5",
            "apiKey": news_api_key,
        },
    )
    if isinstance(data, dict) and data.get("articles"):
        return [a["title"] for a in data["articles"][:5] if isinstance(a, dict) and "title" in a]

    return []


# ---------------------------------------------------------------------------
# MA context
# ---------------------------------------------------------------------------


def compute_ma_context(closes: list[Decimal]) -> dict[str, Any]:
    sma_short = simple_moving_average(closes, _SMA_SHORT_PERIOD)
    sma_long = simple_moving_average(closes, _SMA_LONG_PERIOD)
    current = closes[-1]
    trend = "ALTA" if (sma_short and sma_long and sma_short > sma_long) else "BAIXA"

    gap_abs: Decimal | None = None
    gap_pct: Decimal | None = None
    distance_pct: Decimal | None = None
    if sma_short and sma_long and sma_long != 0:
        distance_pct = (sma_short - sma_long) / sma_long * 100
        gap_abs = abs(sma_short - sma_long)
        gap_pct = abs(distance_pct)

    return {
        "current_price": current,
        "sma_short": sma_short,
        "sma_long": sma_long,
        "trend": trend,
        "distance_pct": distance_pct,
        "gap_abs": gap_abs,
        "gap_pct": gap_pct,
    }


# ---------------------------------------------------------------------------
# AI analysis
# ---------------------------------------------------------------------------


def _plain(text: str) -> str:
    """Strip Telegram Markdown v1 special chars from user-generated text."""
    return text.replace("*", "").replace("_", " ").replace("`", "")


def analyze_with_ai(
    api_key: str,
    ticker: dict[str, Any],
    ma: dict[str, Any],
    fg: dict[str, Any] | None,
    news: list[str],
    model: str,
) -> dict[str, Any] | None:
    try:
        import anthropic  # noqa: PLC0415
    except ImportError:
        logger.error("anthropic package not installed — AI analysis skipped")
        return None

    price = float(ma["current_price"])
    sma_short = ma["sma_short"]
    sma_long = ma["sma_long"]
    short_str = f"${float(sma_short):,.2f}" if sma_short else "N/A"
    long_str = f"${float(sma_long):,.2f}" if sma_long else "N/A"
    dist_str = f"{float(ma['distance_pct']):+.2f}%" if ma["distance_pct"] else "N/A"
    fg_str = f"{fg['value']}/100 ({fg['label']})" if fg else "N/A"
    news_block = "\n".join(f"- {t}" for t in news) if news else "Sem notícias disponíveis"

    prompt = (
        "Você é um analista de criptomoedas experiente. Analise os dados abaixo e responda "
        "APENAS com um objeto JSON válido (sem blocos de código markdown, sem texto extra).\n\n"
        f"DADOS DO MERCADO:\n"
        f"- BTC/USDT Preço atual: ${price:,.2f}\n"
        f"- Variação 24h: {float(ticker['change_pct']):+.2f}%\n"
        f"- Volume 24h: ${float(ticker['volume_usdt']):,.0f} USDT\n"
        f"- Fear & Greed Index: {fg_str}\n\n"
        f"MÉDIAS MÓVEIS (1h):\n"
        f"- Média Curta (SMA {_SMA_SHORT_PERIOD}): {short_str}\n"
        f"- Média Longa (SMA {_SMA_LONG_PERIOD}): {long_str}\n"
        f"- Distância entre médias: {dist_str}\n"
        f"- Tendência: {ma['trend']}\n\n"
        f"NOTÍCIAS RECENTES:\n{news_block}\n\n"
        'Responda com este JSON exato:\n'
        '{\n'
        '  "situacao": "situação atual em 2-3 linhas",\n'
        '  "perspectiva": "Alta" ou "Média" ou "Baixa",\n'
        '  "perspectiva_texto": "explicação em 1-2 linhas",\n'
        '  "gatilho_compra": "valor/condição específica para sinal de compra",\n'
        '  "gatilho_venda": "valor/condição específica para sinal de venda",\n'
        '  "impacto_noticias": "Favorável" ou "Neutro" ou "Desfavorável",\n'
        '  "resumo_noticias": "resumo das notícias em português em 2-3 linhas",\n'
        '  "conclusao": "frase final de 1 linha resumindo o cenário"\n'
        "}"
    )

    text = ""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("AI response not valid JSON: %s | snippet: %s", exc, text[:300])
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("AI analysis error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------


def _build_message(
    ticker: dict[str, Any],
    ma: dict[str, Any],
    fg: dict[str, Any] | None,
    news: list[str],
    ai: dict[str, Any] | None,
    now: datetime,
) -> str:
    change = ticker["change_pct"]
    volume_b = float(ticker["volume_usdt"]) / 1_000_000_000
    price_icon = "🟢" if change >= 0 else "🔴"
    trend_icon = "📈" if ma["trend"] == "ALTA" else "📉"
    change_sign = "+" if change >= 0 else ""
    fg_str = f"{fg['value']}/100 ({fg['label']})" if fg else "N/A"

    sma_short = ma["sma_short"]
    sma_long = ma["sma_long"]
    short_str = f"${float(sma_short):,.2f}" if sma_short else "N/A"
    long_str = f"${float(sma_long):,.2f}" if sma_long else "N/A"
    dist_str = (
        f"{'+' if ma['distance_pct'] >= 0 else ''}{float(ma['distance_pct']):.2f}%"
        if ma["distance_pct"] is not None
        else "N/A"
    )
    gap_str = (
        f"${float(ma['gap_abs']):,.2f} (~{float(ma['gap_pct']):.2f}%)"
        if ma["gap_abs"]
        else "N/A"
    )

    if ai:
        impact_icon = {"Favorável": "📈", "Desfavorável": "📉"}.get(ai.get("impacto_noticias", ""), "➡️")
        news_summary = _plain(ai.get("resumo_noticias", ""))
        news_impact = f"Impacto: {impact_icon} {ai.get('impacto_noticias', 'Neutro')}"
        ai_section = (
            f"\n────────────────────────────────\n"
            f"🤖 *ANÁLISE DA IA*\n\n"
            f"📌 {_plain(ai.get('situacao', ''))}\n\n"
            f"🎯 Perspectiva de operação: *{ai.get('perspectiva', '')}*\n"
            f"{_plain(ai.get('perspectiva_texto', ''))}\n\n"
            f"⚡ Gatilho COMPRA: {_plain(ai.get('gatilho_compra', ''))}\n"
            f"⚡ Gatilho VENDA: {_plain(ai.get('gatilho_venda', ''))}\n\n"
            f"💬 _{_plain(ai.get('conclusao', ''))}_"
        )
    else:
        news_summary = "\n".join(f"• {t}" for t in news[:5]) if news else "Sem notícias disponíveis"
        news_impact = ""
        ai_section = (
            "\n────────────────────────────────\n"
            "🤖 *ANÁLISE DA IA*\n\n"
            "⚠️ Análise indisponível no momento."
        )

    impact_line = f"\n{news_impact}" if news_impact else ""

    return (
        f"📊 *RELATÓRIO DE MERCADO — {now.strftime('%d/%m/%Y %H:%M')}*\n"
        f"────────────────────────────────\n"
        f"{price_icon} *BTC/USDT:* ${float(ma['current_price']):,.2f}\n"
        f"📉 Variação 24h: {change_sign}{float(change):.2f}%\n"
        f"💹 Volume 24h: ${volume_b:.2f}B\n"
        f"😱 Fear & Greed: {fg_str}\n\n"
        f"{trend_icon} *Médias Móveis:*\n"
        f"• Curta ({_SMA_SHORT_PERIOD}): {short_str}\n"
        f"• Longa ({_SMA_LONG_PERIOD}): {long_str}\n"
        f"• Distância: {dist_str}\n"
        f"• Tendência: {ma['trend']}\n"
        f"• Falta para cruzamento: {gap_str}\n\n"
        f"────────────────────────────────\n"
        f"📰 *NOTÍCIAS*\n"
        f"{news_summary}"
        f"{impact_line}"
        f"{ai_section}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def send_market_report(
    bot_token: str,
    chat_id: str,
    anthropic_api_key: str | None = None,
    news_api_key: str | None = None,
    anthropic_model: str = "claude-sonnet-4-6",
) -> None:
    """Collect market data, run AI analysis, and send the report via Telegram."""
    from telegram_notifier import send_message  # noqa: PLC0415

    now = datetime.now(UTC)

    ticker = fetch_ticker()
    if ticker is None:
        logger.error("Market report aborted: Binance ticker fetch failed")
        return

    closes = fetch_kline_closes()
    if closes is None:
        logger.error("Market report aborted: Binance klines fetch failed")
        return

    ma = compute_ma_context(closes)
    fg = fetch_fear_greed()
    news = fetch_news(news_api_key)

    ai: dict[str, Any] | None = None
    if anthropic_api_key:
        ai = analyze_with_ai(anthropic_api_key, ticker, ma, fg, news, anthropic_model)
        if ai is None:
            logger.warning("AI analysis failed — sending report without AI section")

    text = _build_message(ticker, ma, fg, news, ai, now)
    send_message(bot_token, chat_id, text)
