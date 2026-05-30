from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from app.execution.binance_private import BinancePrivateClient


@dataclass(frozen=True)
class ExecutionRequest:
    environment: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal | None
    quote_quantity: Decimal | None
    client_order_id: str


@dataclass(frozen=True)
class ExecutionFill:
    external_trade_id: str | None
    price: Decimal
    quantity: Decimal
    quote_quantity: Decimal
    fee_amount: Decimal | None
    fee_asset: str | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class ExecutionResult:
    adapter: str
    external_order_id: str | None
    client_order_id: str | None
    status: str
    executed_quantity: Decimal
    quote_quantity: Decimal | None
    average_price: Decimal | None
    raw_payload: dict[str, Any]
    fills: list[ExecutionFill]


class ExecutionAdapter(Protocol):
    name: str

    def place_order(self, request: ExecutionRequest) -> ExecutionResult: ...

    def fetch_order(
        self,
        *,
        symbol: str,
        external_order_id: str | None,
        client_order_id: str | None,
    ) -> ExecutionResult: ...


class DryRunExecutionAdapter:
    name = "dry_run"

    def place_order(self, request: ExecutionRequest) -> ExecutionResult:
        average_price = None
        executed_quantity = request.quantity or Decimal("0")
        quote_quantity = request.quote_quantity
        return ExecutionResult(
            adapter=self.name,
            external_order_id=None,
            client_order_id=request.client_order_id,
            status="FILLED",
            executed_quantity=executed_quantity,
            quote_quantity=quote_quantity,
            average_price=average_price,
            raw_payload={
                "dry_run": True,
                "symbol": request.symbol,
                "side": request.side,
                "type": request.order_type,
            },
            fills=[],
        )

    def fetch_order(
        self,
        *,
        symbol: str,
        external_order_id: str | None,
        client_order_id: str | None,
    ) -> ExecutionResult:
        return ExecutionResult(
            adapter=self.name,
            external_order_id=external_order_id,
            client_order_id=client_order_id,
            status="FILLED",
            executed_quantity=Decimal("0"),
            quote_quantity=None,
            average_price=None,
            raw_payload={"dry_run": True, "symbol": symbol},
            fills=[],
        )


class BinanceTestnetExecutionAdapter:
    name = "binance_testnet"

    def __init__(self, client: BinancePrivateClient) -> None:
        self.client = client

    def place_order(self, request: ExecutionRequest) -> ExecutionResult:
        payload = self.client.create_market_order(
            symbol=request.symbol,
            side=request.side,
            quantity=_decimal_to_api(request.quantity),
            quote_order_qty=_decimal_to_api(request.quote_quantity),
            new_client_order_id=request.client_order_id,
        )
        return _result_from_binance_payload(self.name, payload)

    def fetch_order(
        self,
        *,
        symbol: str,
        external_order_id: str | None,
        client_order_id: str | None,
    ) -> ExecutionResult:
        order_payload = self.client.get_order(
            symbol=symbol,
            order_id=external_order_id,
            client_order_id=client_order_id,
        )
        fills: list[dict[str, Any]] = []
        if external_order_id is not None:
            fills = self.client.get_my_trades(symbol=symbol, order_id=external_order_id)
        return _result_from_binance_payload(self.name, {**order_payload, "fills": fills})


class BlockedMainnetExecutionAdapter:
    name = "binance_mainnet"

    def place_order(self, request: ExecutionRequest) -> ExecutionResult:
        raise RuntimeError("Mainnet execution is blocked in the Aurum MVP")

    def fetch_order(
        self,
        *,
        symbol: str,
        external_order_id: str | None,
        client_order_id: str | None,
    ) -> ExecutionResult:
        raise RuntimeError("Mainnet reconciliation is blocked in the Aurum MVP")


def _result_from_binance_payload(adapter: str, payload: dict[str, Any]) -> ExecutionResult:
    fills = [_fill_from_payload(fill) for fill in payload.get("fills", [])]
    executed_quantity = Decimal(str(payload.get("executedQty", "0")))
    quote_quantity = (
        Decimal(str(payload["cummulativeQuoteQty"]))
        if payload.get("cummulativeQuoteQty") is not None
        else None
    )
    average_price = _average_price(executed_quantity, quote_quantity)
    return ExecutionResult(
        adapter=adapter,
        external_order_id=(
            str(payload.get("orderId")) if payload.get("orderId") is not None else None
        ),
        client_order_id=payload.get("clientOrderId"),
        status=str(payload.get("status", "NEW")),
        executed_quantity=executed_quantity,
        quote_quantity=quote_quantity,
        average_price=average_price,
        raw_payload=payload,
        fills=fills,
    )


def _fill_from_payload(payload: dict[str, Any]) -> ExecutionFill:
    price = Decimal(str(payload.get("price", "0")))
    quantity = Decimal(str(payload.get("qty", payload.get("quantity", "0"))))
    quote_quantity = Decimal(str(payload.get("quoteQty", price * quantity)))
    trade_id = payload.get("tradeId", payload.get("id"))
    return ExecutionFill(
        external_trade_id=str(trade_id) if trade_id is not None else None,
        price=price,
        quantity=quantity,
        quote_quantity=quote_quantity,
        fee_amount=(
            Decimal(str(payload["commission"]))
            if payload.get("commission") is not None
            else None
        ),
        fee_asset=payload.get("commissionAsset"),
        raw_payload=payload,
    )


def _average_price(executed_quantity: Decimal, quote_quantity: Decimal | None) -> Decimal | None:
    if quote_quantity is None or executed_quantity <= 0:
        return None
    return quote_quantity / executed_quantity


def _decimal_to_api(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")
