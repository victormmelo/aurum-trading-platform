from app.api.routes.health import health_check


def test_health_check_returns_service_status() -> None:
    response = health_check()

    assert response.model_dump() == {
        "status": "ok",
        "service": "Aurum API",
        "environment": "development",
        "version": "0.1.0",
    }
