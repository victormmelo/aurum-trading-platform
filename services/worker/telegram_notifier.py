from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"
_TIMEOUT = 10.0


def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    """Send a Telegram message. Retries once after 60 s on failure."""
    url = f"{_TELEGRAM_API}/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

    for attempt in range(2):
        try:
            resp = httpx.post(url, json=payload, timeout=_TIMEOUT)
            if resp.status_code == 200:
                return True
            logger.error(
                "Telegram API error attempt=%d status=%d body=%s",
                attempt + 1,
                resp.status_code,
                resp.text[:300],
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Telegram send error attempt=%d: %s", attempt + 1, exc)
        if attempt == 0:
            time.sleep(60)

    return False


def notify_buy_executed(
    bot_token: str,
    chat_id: str,
    *,
    price: Decimal,
    quantity: Decimal,
    notional: Decimal,
    sma_short: Decimal | None,
    sma_long: Decimal | None,
    sma_short_period: int = 50,
    sma_long_period: int = 200,
    executed_at: datetime,
) -> None:
    short_str = f"${float(sma_short):,.2f}" if sma_short else "N/A"
    long_str = f"${float(sma_long):,.2f}" if sma_long else "N/A"
    text = (
        f"🟢 *COMPRA EXECUTADA*\n"
        f"─────────────────────\n"
        f"📅 Data/Hora: {executed_at.strftime('%d/%m/%Y %H:%M')}\n"
        f"💰 Preço: ${float(price):,.2f}\n"
        f"📊 Qtd BTC: {quantity:.8f} BTC\n"
        f"💵 Valor investido: ${float(notional):,.2f}\n\n"
        f"📈 Média Curta ({sma_short_period}): {short_str}\n"
        f"📉 Média Longa ({sma_long_period}): {long_str}\n"
        f"🔀 *Golden Cross detectado*\n\n"
        f"💼 Posição atual: COMPRADO"
    )
    send_message(bot_token, chat_id, text)


def notify_sell_executed(
    bot_token: str,
    chat_id: str,
    *,
    price: Decimal,
    quantity: Decimal,
    notional: Decimal,
    entry_price: Decimal,
    sma_short: Decimal | None,
    sma_long: Decimal | None,
    sma_short_period: int = 50,
    sma_long_period: int = 200,
    executed_at: datetime,
) -> None:
    short_str = f"${float(sma_short):,.2f}" if sma_short else "N/A"
    long_str = f"${float(sma_long):,.2f}" if sma_long else "N/A"
    cost_basis = entry_price * quantity
    pnl = notional - cost_basis
    pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else Decimal("0")
    pnl_sign = "+" if pnl >= 0 else ""
    text = (
        f"🔴 *VENDA EXECUTADA*\n"
        f"─────────────────────\n"
        f"📅 Data/Hora: {executed_at.strftime('%d/%m/%Y %H:%M')}\n"
        f"💰 Preço: ${float(price):,.2f}\n"
        f"📊 Qtd BTC: {quantity:.8f} BTC\n"
        f"💵 Valor recebido: ${float(notional):,.2f}\n\n"
        f"📈 Média Curta ({sma_short_period}): {short_str}\n"
        f"📉 Média Longa ({sma_long_period}): {long_str}\n"
        f"🔀 *Death Cross detectado*\n\n"
        f"📊 *Resultado da operação:*\n"
        f"Lucro/Prejuízo: {pnl_sign}${float(pnl):,.2f} ({pnl_sign}{float(pnl_pct):.2f}%)\n"
        f"💼 Posição atual: VENDIDO (aguardando)"
    )
    send_message(bot_token, chat_id, text)
