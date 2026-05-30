from __future__ import annotations

from decimal import Decimal

from app.execution.adapters import BinanceTestnetExecutionAdapter


def test_binance_testnet_adapter_parses_trade_id_from_full_order_fills() -> None:
    adapter = BinanceTestnetExecutionAdapter(FakeClient())

    result = adapter.place_order(
        request=type(
            "Request",
            (),
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": None,
                "quote_quantity": Decimal("25"),
                "client_order_id": "aurum-test",
            },
        )()
    )

    assert result.status == "FILLED"
    assert result.external_order_id == "12345"
    assert result.executed_quantity == Decimal("0.00025")
    assert result.average_price == Decimal("100000")
    assert result.fills[0].external_trade_id == "67890"
    assert result.fills[0].quote_quantity == Decimal("25.00000")


class FakeClient:
    def create_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: str | None,
        quote_order_qty: str | None,
        new_client_order_id: str,
    ) -> dict:
        assert symbol == "BTCUSDT"
        assert side == "BUY"
        assert quantity is None
        assert quote_order_qty == "25"
        assert new_client_order_id == "aurum-test"
        return {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "clientOrderId": new_client_order_id,
            "status": "FILLED",
            "executedQty": "0.00025",
            "cummulativeQuoteQty": "25",
            "fills": [
                {
                    "price": "100000",
                    "qty": "0.00025",
                    "commission": "0.00000025",
                    "commissionAsset": "BTC",
                    "tradeId": 67890,
                }
            ],
        }
