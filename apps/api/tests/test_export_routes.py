from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import exports as export_routes
from app.core.schemas import ExportCreateRequest, ExportJobResponse
from app.db.session import get_db_session
from app.main import create_app

NOW = datetime(2026, 5, 17, 20, 0, tzinfo=UTC)


def test_create_export_returns_completed_job_and_get_reuses_it(monkeypatch) -> None:  # noqa: ANN001
    client = _client()
    export_routes._EXPORT_JOBS.clear()
    export_id = uuid.uuid4()

    def generate(store, request, environment, symbol):  # noqa: ANN001
        assert environment == "testnet"
        assert symbol == "BTCUSDT"
        assert request.format == "txt"
        assert request.sections == ["decisions"]
        return ExportJobResponse(
            id=export_id,
            environment=environment,
            symbol=symbol,
            status="completed",
            format=request.format,
            sections=request.sections,
            content_type="text/plain",
            filename="aurum.txt",
            created_at=NOW,
            completed_at=NOW,
            filters={"sections": request.sections},
            content="Aurum export report\n",
        )

    monkeypatch.setattr(export_routes, "generate_export", generate)

    response = client.post("/exports", json={"format": "txt", "sections": ["decisions"]})

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == str(export_id)
    assert payload["status"] == "completed"

    get_response = client.get(f"/exports/{export_id}")
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "Aurum export report\n"


def test_get_export_returns_404_for_unknown_id() -> None:
    export_routes._EXPORT_JOBS.clear()
    response = _client().get(f"/exports/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "export not found"}


def test_generate_export_renders_csv_with_empty_sections() -> None:
    request = ExportCreateRequest(format="csv")

    job = export_routes.generate_export(
        _ExportStore(),
        request,
        environment="testnet",
        symbol="BTCUSDT",
        now=NOW,
    )

    assert job.status == "completed"
    assert job.content_type == "text/csv"
    assert job.filename == "aurum-btcusdt-20260517200000.csv"
    assert "section,field,value" in job.content


def test_generate_export_renders_pdf_as_base64_text_report() -> None:
    decision = SimpleNamespace(
        decided_at=NOW,
        decision="NAO_OPERAR",
        reason="Robô pausado",
    )
    request = ExportCreateRequest(format="pdf", sections=["decisions"])

    job = export_routes.generate_export(
        _ExportStore(decisions=[decision]),
        request,
        environment="testnet",
        symbol="BTCUSDT",
        now=NOW,
    )

    assert job.content_type == "application/pdf"
    assert "Robô pausado" in __import__("base64").b64decode(job.content).decode("utf-8")


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: object()
    return TestClient(app)


@dataclass
class _ExportStore:
    market: object | None = None
    portfolio: object | None = None
    orders: list[object] | None = None
    fills: list[object] | None = None
    decisions: list[object] | None = None

    def get_latest_market_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> object | None:
        return self.market

    def get_latest_portfolio_snapshot(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> object | None:
        return self.portfolio

    def list_orders(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        side: str | None,
        status: str | None,
    ) -> list[object]:
        return self.orders or []

    def list_fills(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
    ) -> list[object]:
        return self.fills or []

    def list_decisions(
        self,
        *,
        environment: str,
        symbol: str,
        period_start: datetime | None,
        period_end: datetime | None,
        decision: str | None,
    ) -> list[object]:
        return self.decisions or []
