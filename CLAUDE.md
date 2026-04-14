# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Multi-source data integration platform that fetches data from external APIs and imports it into Cosmos ERP (on-premise MSSQL) via stored procedures. Written in Python/FastAPI, deployed via Docker Compose.

```
External APIs → [Fetcher Containers] → iface-db (FastAPI :8000) → MSSQL (Cosmos ERP)
```

All DB operations go through `iface-db` HTTP API — fetchers never connect to MSSQL directly.

## Commands

All commands require `-e <env_file>`. `.env.a` = Company A (Speeding Rocket), `.env.b` = Company B (EIP LL).

```bash
# Build all images
docker compose --env-file .env.a build

# Start iface-db (long-running core service)
docker compose --env-file .env.a up -d iface-db

# Initialize DB schema (first deploy only, per company)
./run-job.sh -e .env.a init

# Run a fetcher job manually
./run-job.sh -e .env.a eip order
./run-job.sh -e .env.a eip payment
./run-job.sh -e .env.a eip pre_products
./run-job.sh -e .env.a eip product_incorrects
./run-job.sh -e .env.a eip inventory
./run-job.sh -e .env.a retex daily
./run-job.sh -e .env.a retex cm_ax_import 2026/04/01 2026/04/14
./run-job.sh -e .env.a xdelivery order
./run-job.sh -e .env.a xdelivery saas
./run-job.sh -e .env.a currency currency_api
./run-job.sh -e .env.a currency customs_rate

# Expose iface-db for Swagger UI / dev access (set IFACE_DB_PORT in .env first)
docker compose --env-file .env.a -f docker-compose.yml -f docker-compose.ports.yml up -d
# Swagger: http://localhost:${IFACE_DB_PORT}/docs
```

## Architecture

### Services

- **iface-db** (`iface-db/`): Long-running FastAPI service. All DB writes/reads/SP calls go through it. Secured by SP/View whitelists in `iface-db/app/core/config.py`.
- **iface-eip-fetcher**: Fetches EIP e-commerce orders/payments. Job flows defined in YAML (`config/eip.yml`, `config/eipll.yml`) — no code change needed for new companies or SP names.
- **iface-retex-fetcher**: RETEX POS daily operations, CM notification slip export (XLS to warehouse; future: WMS API), and SO back-fill.
- **iface-xdelivery-fetcher**: Logistics returns and SaaS billing.
- **iface-currency-fetcher**: Forex rates from currencyapi.com and Taiwan customs.
- **iface-client** (`iface-client/iface_client.py`): Shared Python library installed via `pip` into every fetcher image at build time.
- **iface-initdb**: One-shot container for first-deploy DB initialization (idempotent SQL scripts).

### Multi-company isolation

One `.env` file = one complete isolated company environment. `COMPOSE_PROJECT_NAME` drives Docker network and container naming. Adding a new company requires only a new `.env` file — zero code changes.

### IFACE status lifecycle

`0` (pending) → `5` (imported to ERP) → `6` (reply confirmed / no data) or `E` (error → `IFACE_ERROR` table).

## Security boundary — SP/View whitelists

`iface-db` only executes SPs and queries views that are explicitly listed in `iface-db/app/core/config.py`:

- `ALLOWED_PROCEDURES` — SPs called via `POST /api/v1/iface/sp/{name}` (write-only, no result set)
- `ALLOWED_SP_QUERIES` — SPs called via `POST /api/v1/iface/sp-query/{name}` (returns result set; also specifies target database)
- `ALLOWED_VIEWS` — Views for `reply/` and `query/` endpoints
- `NAMED_QUERIES` — Parameterized SQL queries with inline SQL stored directly in config

**Any new SP or View must be added to the appropriate whitelist before it can be called.** Unlisted names return `403 Forbidden`.

## Rebuild rules

| Changed file | Rebuild needed |
|---|---|
| `iface-db/app/**` | `docker compose --env-file .env.a up -d --build iface-db` |
| `iface-client/iface_client.py` | All fetcher images: `docker compose --env-file .env.a build` |
| `iface-eip-fetcher/app/**` | `docker compose --env-file .env.a build iface-eip-fetcher` |
| `iface-*-fetcher/app/**` | That fetcher only |
| `iface-eip-fetcher/config/*.yml` | **No rebuild** — YAML is volume-mounted, changes take effect immediately |

## iface-client API

The shared client (`from iface_client import ...`) wraps all iface-db HTTP calls:

| Function | Purpose |
|---|---|
| `iface_import(api_url, json_doc, query, module, function, initial_status="0")` | Write data to IFACE table; returns `batch_id` |
| `run_procedure(name, database="IFACE", params={})` | Execute whitelisted SP |
| `status_update(module, function, from, to)` | Bulk update STATUS field |
| `get_reply(view_name)` | Query reply view for ERP → external API writeback |
| `query_view(view_name, module, function)` | Query reference data views |
| `sp_query(name, params)` | Execute SP that returns result set |
| `named_query(name, **kwargs)` | Execute named parameterized query |

## Adding a new fetcher

1. Create `iface-xxx-fetcher/` with `Dockerfile`, `requirements.txt`, `app/main.py`, `app/xxx_client.py`, `.env.example`
2. Add service to `docker-compose.yml` with `profiles: [xxx]`, `restart: "no"`, `depends_on: iface-db`
3. Add env vars to `.env.x`
4. Add new SPs/Views to whitelists in `iface-db/app/core/config.py`
5. Add crontab entry using `run-job.sh`

Dockerfile build context must be the hub root (`.`) so `iface-client/` is accessible during build.

## Error handling

Failed records: `IFACE.STATUS='E'` + `ERROR_MESSAGE` column + copy written to `IFACE_ERROR` quarantine table. Manual remediation:

```sql
-- Find unresolved errors
SELECT * FROM IFACE_ERROR WHERE RESOLVED = 0 ORDER BY QUARANTINE_DATE DESC;

-- Mark resolved after manual fix
UPDATE IFACE_ERROR SET RESOLVED=1, RESOLVED_DATE=GETDATE(), RESOLVED_BY='mis', RESOLVED_NOTE='...'
WHERE ERROR_ID = 123;
```
