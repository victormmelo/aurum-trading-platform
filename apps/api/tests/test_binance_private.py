from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.execution import binance_private
from app.execution.binance_private import BinanceCredentials, BinancePrivateClient


def test_signed_account_request_signs_required_parameters(monkeypatch) -> None:  # noqa: ANN001
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def read(self) -> bytes:
            return b'{"balances":[]}'

    def fake_urlopen(request, timeout):  # noqa: ANN001
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["api_key"] = request.headers["X-mbx-apikey"]
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(binance_private.time, "time", lambda: 1_780_000_000)
    monkeypatch.setattr(binance_private, "urlopen", fake_urlopen)

    client = BinancePrivateClient(
        base_url="https://testnet.binance.vision/api/v3",
        credentials=BinanceCredentials(api_key="key", api_secret="secret"),
        recv_window_ms=7000,
    )

    payload = client.get_account()

    query = parse_qs(urlparse(captured["url"]).query)
    assert payload == {"balances": []}
    assert captured["method"] == "GET"
    assert captured["api_key"] == "key"
    assert captured["timeout"] == 10.0
    assert query["timestamp"] == ["1780000000000"]
    assert query["recvWindow"] == ["7000"]
    assert query["signature"] == [
        "ae89657ca602a149b3e15f3438c2f496fad4209d7b98f1eebaa25719bcf61520"
    ]


def test_market_order_uses_quote_order_qty_and_full_response(monkeypatch) -> None:  # noqa: ANN001
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return None

        def read(self) -> bytes:
            return b'{"symbol":"BTCUSDT","status":"FILLED"}'

    def fake_urlopen(request, timeout):  # noqa: ANN001, ARG001
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        return Response()

    monkeypatch.setattr(binance_private.time, "time", lambda: 1_780_000_000)
    monkeypatch.setattr(binance_private, "urlopen", fake_urlopen)

    client = BinancePrivateClient(
        base_url="https://testnet.binance.vision/api/v3",
        credentials=BinanceCredentials(api_key="key", api_secret="secret"),
    )

    client.create_market_order(
        symbol="BTCUSDT",
        side="BUY",
        quote_order_qty="25",
        new_client_order_id="aurum-test",
    )

    query = parse_qs(urlparse(captured["url"]).query)
    assert captured["method"] == "POST"
    assert query["symbol"] == ["BTCUSDT"]
    assert query["side"] == ["BUY"]
    assert query["type"] == ["MARKET"]
    assert query["quoteOrderQty"] == ["25"]
    assert query["newOrderRespType"] == ["FULL"]
    assert query["newClientOrderId"] == ["aurum-test"]
