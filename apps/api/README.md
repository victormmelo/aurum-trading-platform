# Aurum API

FastAPI backend for the Aurum Trading Platform foundation cycle.

## Commands

```bash
pip install -e ".[dev]"
pytest
uvicorn app.main:app --reload
```

Import Binance Spot Testnet candles after PostgreSQL migrations are applied:

```bash
aurum-import-candles --interval 1h --interval 4h --interval 1d --limit 500
```
