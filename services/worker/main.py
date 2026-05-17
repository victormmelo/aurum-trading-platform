from __future__ import annotations

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.worker.cycle import run_worker_cycle


def main() -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    with session_factory() as session:
        result = run_worker_cycle(
            session,
            environment=settings.aurum_environment,
            symbol=settings.trading_symbol,
        )

    print(
        "Aurum worker dry-run cycle "
        f"status={result.status} decision={result.decision} reason={result.reason}"
    )


if __name__ == "__main__":
    main()
