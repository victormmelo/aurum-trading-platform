from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BinancePrivateError(RuntimeError):
    """Raised when a signed Binance Spot request fails."""


@dataclass(frozen=True)
class BinanceCredentials:
    api_key: str
    api_secret: str


class BinancePrivateClient:
    def __init__(
        self,
        *,
        base_url: str,
        credentials: BinanceCredentials,
        timeout_seconds: float = 10.0,
        recv_window_ms: int = 5000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.credentials = credentials
        self.timeout_seconds = timeout_seconds
        self.recv_window_ms = recv_window_ms

    def get_account(self) -> dict[str, Any]:
        return self._signed_request("GET", "/account", {})

    def create_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: str | None = None,
        quote_order_qty: str | None = None,
        new_client_order_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "newOrderRespType": "FULL",
        }
        if quantity is not None:
            params["quantity"] = quantity
        if quote_order_qty is not None:
            params["quoteOrderQty"] = quote_order_qty
        if new_client_order_id is not None:
            params["newClientOrderId"] = new_client_order_id
        return self._signed_request("POST", "/order", params)

    def get_order(
        self,
        *,
        symbol: str,
        order_id: str | None = None,
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id is not None:
            params["origClientOrderId"] = client_order_id
        return self._signed_request("GET", "/order", params)

    def get_my_trades(self, *, symbol: str, order_id: str | None = None) -> list[dict[str, Any]]:
        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        payload = self._signed_request("GET", "/myTrades", params)
        if not isinstance(payload, list):
            raise BinancePrivateError("Binance myTrades response is not a list")
        return payload

    def _signed_request(self, method: str, path: str, params: dict[str, Any]) -> Any:
        payload = {
            **params,
            "recvWindow": self.recv_window_ms,
            "timestamp": int(time.time() * 1000),
        }
        query = urlencode(payload)
        signature = hmac.new(
            self.credentials.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_query = f"{query}&signature={signature}"
        url = f"{self.base_url}{path}?{signed_query}"
        request = Request(
            url,
            method=method,
            headers={
                "User-Agent": "aurum-api/0.1.0",
                "X-MBX-APIKEY": self.credentials.api_key,
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise BinancePrivateError(
                f"Binance signed request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise BinancePrivateError(f"Binance signed request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise BinancePrivateError("Binance signed request timed out") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise BinancePrivateError("Binance signed response is not valid JSON") from exc
