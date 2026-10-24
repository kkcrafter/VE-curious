# Backend

FastAPI + SQLite, one process. Design and API contract: [`docs/design/backend-outline.md`](../docs/design/backend-outline.md).

## Run

```bash
cp .env.example .env   # fill in ECURIOUS_API_KEY; ADAPTER=mock needs no key
uv run --env-file .env uvicorn app.main:app --reload --port 3000
```

API docs (OpenAPI): http://localhost:3000/docs

## Test

```bash
uv run pytest -q
```

## Layout

| File | Job |
|---|---|
| `app/config.py` | Settings from env |
| `app/db.py` | SQLite schema, seed (bays from `LOCK_IDS`, demo drivers), event log writer |
| `app/machine.py` | State machine, pure |
| `app/adapters.py` | Hardware adapters: `MockAdapter` (and Ecurious) behind one interface |
| `app/core.py` | Only place that changes reservation state or calls hardware |
| `app/main.py` | HTTP routes |
