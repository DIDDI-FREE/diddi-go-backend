# Architecture — diddi-go-backend

> Inside view of this module. Read this before touching code.
> Last checked against code: 2026-11-25 (branch fix/014-rewards-reservation-always-closed, on d636c0b). Anything not checked is marked "not verified".

## 1. Purpose
DiddiGo is the ride-hailing (VTC) backend of DiddiFree. It owns quotes, rides, driver matching, driver KYC/vehicles, partners/fleets, the ride payment record and the driver wallet/ledger.
It does NOT own identity (DiddiFreeID), payment execution (DiddiPay), maps/routing (DiddiMap), file storage (DiddiFiles), campaigns/discount rules (DiddiRewards) or chat/calls (DiddiComms).

## 2. Stack
- Language: Python >= 3.11 (`pyproject.toml`).
- Framework: FastAPI + uvicorn, one process, modular monolith (`app_base/main.py`).
- Database: PostgreSQL 16 + PostGIS (`postgis/postgis:16-3.4-alpine`), SQLAlchemy 2 async + asyncpg, GeoAlchemy2.
- Migrations: Alembic (`alembic/`), run at container start (`docker/start.sh`).
- Redis 7: driver locations, ride offers, idempotency stores, payment return contexts, caches, and the Redis Stream outbox target.
- HTTP client: httpx. JWT: PyJWT (HS256 local, RS256 via JWKS).
- Observability: OpenTelemetry OTLP HTTP, Prometheus text on `/metrics` (`app_base/core/telemetry.py`, `metrics.py`).
- Tooling: uv (`uv.lock`), ruff, pytest + pytest-asyncio. Docs portal: mkdocs (`mkdocs.yml`, `Dockerfile.docs`).

## 3. Layout
| Path | What lives there |
|---|---|
| `app_base/main.py` | App creation, middleware, error handlers, all router mounts, `/health`, `/ready`, `/metrics`. |
| `app_base/core/` | Settings, DB engine, Redis, auth dependencies, identity/JWT checks, errors, DI wiring (`deps.py`), lifespan, telemetry. |
| `app_base/modules/auth/` | Local users ("shadow users"), OTP, local JWT session. |
| `app_base/modules/ride/` | Quotes, rides, matching, drivers, vehicles, KYC, scoring, WebSocket, internal S2S routers, clients for DiddiMap / DiddiFiles / DiddiRewards / DiddiFreeID capabilities. |
| `app_base/modules/payment/` | Ride payment, DiddiPay client and webhook, driver wallet, top-ups, withdrawals, passenger debts, reconciliation, Rewards outbox. |
| `app_base/modules/partner/` | Partners, fleets, members, vehicle assignment (public admin + internal S2S routers). |
| `app_base/modules/notification/` | Device registration, FCM push, SMS providers. |
| `app_base/modules/observability/` | Admin log search through Loki. |
| `app_base/modules/audit/` | Backoffice audit events (model + repository only). |
| `app_base/shared_kernel/` | Small cross-module contracts and types (`GeoPoint`, routing, payment, sms, capabilities). |
| `app_base/tools/` | CLI helpers: `create_admin.py`, `reconcile_payments.py`. |
| `alembic/versions/` | 42 migration files (2026-07-28 to 2026-11-23). |
| `tools/` | API contract generator (`generate_api_contract.py`, `contract_artifacts.py`). |
| `docs/` | Generated API contract (`docs/api/`), integration notes, admin manifest, frontend briefs. `docs/archive/` is old. |
| `tests/` | 77 test files; mix of `unit`-marked tests and integration tests needing Postgres + Redis. |
| `docker/`, `docker-compose*.yml`, `Dockerfile*` | Build and deployment. |
| `bruno/` | Bruno API collection (not verified in detail). |

## 4. Layers and rules
Each module is a vertical slice: `presentation/` (routers, schemas) → `application/` (services) → `domain/` (entities, interfaces) ← `infra/` (SQLAlchemy models, repositories, HTTP clients).
- Routers get services through FastAPI `Depends` factories in `app_base/core/deps.py`. Add new wiring there.
- Long-lived clients (DiddiMap, DiddiPay, DiddiRewards, DiddiFiles, identity capabilities, SMS, Redis) are created once in `app_base/core/lifespan.py` and stored on `app.state`.
- All business errors are raised as `ApiError(status, code, message, details)` (`app_base/core/errors.py`); codes live in `app_base/core/error_codes.py`.
- Structured logs go through `log_event()` (`app_base/core/observability.py`).
- The layering is not strict in practice: `ride/application/services.py` imports `ride/infra/diddirewards_client.py`, `core/auth_deps.py` imports module repositories, and the payment service reads and saves rides. The graph reports no import cycles (`graphify-out/GRAPH_REPORT.md`).

## 5. Main flows
1. **Quote** — `POST /v1/rides/pricing/estimate`: `ride/presentation/router.py` (`estimate_pricing`) → `RideService.create_quote` (`ride/application/services.py`) → DiddiMap route estimate (`ride/infra/routing_client.py`) → optional DiddiRewards quote when `campaign_id` is sent and `DIDDI_REWARDS_ENABLED=true` (`ride/infra/diddirewards_client.py`) → row in `ride_quotes`. If Rewards fails, the quote is still returned at full price with `rewards.reason = "rewards_unavailable"`.
2. **Create ride and match** — `POST /v1/rides`: `create_ride` in `ride/presentation/router.py` → `RideService.request_ride` (consumes the quote, reserves the Rewards benefit if any) → `MatchingService.try_match` (`ride/application/matching_service.py`; Redis driver locations in `ride/infra/driver_location.py`, offers in `ride/infra/offer_store.py`) → offer sent to drivers by WebSocket and push. Drivers answer with `POST /v1/rides/{id}/accept|decline`.
3. **Ride lifecycle** — `PATCH /v1/rides/{id}/status`, `/arrive`, `/start` (start code), `/waiting/*`, `/cancel` → `RideService` → state machine `ALLOWED_TRANSITIONS` in `ride/domain/entities.py`. Invalid moves return `409 INVALID_STATUS_TRANSITION`. Cancel releases the Rewards reservation (`_release_rewards_if_needed`).
4. **Realtime** — one socket `/v1/ws?token=<access_token>` (`ride/presentation/websocket.py`). Server events: `ride.status_changed`, `ride.driver_location`, `ride.no_driver_found`, `ride.new_request`. Client events: `driver.location_push`, `ride.subscribe`. No replay after reconnect.
5. **Pay a ride** — `POST /v1/payments/{ride_id}/prepare` → `PaymentService.prepare_payment` (`payment/application/services.py`) → cash path, or `DiddiPayClient.create_payment_intent` (`payment/infra/diddipay_client.py`). Result arrives by signed webhook `POST /internal/webhooks/diddipay` → `apply_diddipay_webhook` (HMAC check, dedupe in `webhook_events`). Cash is confirmed by `POST /v1/payments/{ride_id}/confirm-cash`. Settlement writes the driver ledger (`_record_ride_settlement`), confirms the Rewards benefit and enqueues a Rewards event.
6. **Background workers** (started in `core/lifespan.py`): `payment-reconciliation` (`payment/application/reconciliation.py`, re-reads DiddiPay for late payments), `rewards-events` (`payment/application/rewards_events.py`, SQL outbox → Redis Stream), `capability-projection` (`ride/application/capability_projection_worker.py`, pushes driver status to DiddiFreeID), `rewards-reservations` (`payment/application/rewards_reservations.py`, every 60 s when `DIDDI_REWARDS_ENABLED=true`: retries failed Rewards confirms and releases on ended rides of the last 7 days). Their health shows in `GET /ready` under `components.workers`.

## 6. Data
- One PostgreSQL database, owned only by this repo. Schemas managed by Alembic: `auth`, `audit`, `ride`, `payment`, `notification`, `partner` (`alembic/env.py`, `INCLUDE_SCHEMAS`).
- Main tables (from `__tablename__` in each `infra/models.py`):
  - auth: `users`, `otp_codes`. notification: `user_devices`. audit: `backoffice_events`.
  - ride: `rides`, `ride_quotes`, `ride_status_history`, `ride_stops`, `ride_supplements`, `ride_ratings`, `ride_route_points`, `ride_location_batches`, `ride_emergency_events`, `driver_profiles`, `vehicles`, `pricing_rules`, `emergency_contacts`, `driver_priority_events`, `dispatch_config`, `driver_capability_projection_states`, `driver_capability_projection_events`.
  - payment: `transactions`, `passenger_debts`, `webhook_events`, `rewards_event_outbox`, `driver_wallets`, `driver_ledger_entries`, `driver_topups`, `driver_withdrawals`, `driver_withdrawal_quotes`, `driver_withdrawal_verifications`.
  - partner: `partners`, `partner_members`, `partner_driver_links`, `vehicle_assignments`.
- Migrations: `alembic/versions/`. The DB URL comes from `DATABASE_URL` (settings), not from `alembic.ini`. The app never calls `create_all` (`app_base/core/database.py`).
- Redis: runtime state only (driver positions, offers, idempotency keys, return contexts, breakdown cache). The Rewards stream can use a second Redis (`DIDDI_REWARDS_EVENTS_REDIS_URL`).
- `users` rows are also written on every authenticated request in identity mode ("shadow user" upsert in `core/auth_deps.py`).

## 7. Run and test
From the repo root (PowerShell). Commands are taken from `README.md`, `app_base/README.md`, `docker-compose.local.yml` and `.github/workflows/tests.yml`. They were not executed during this check.

```powershell
# Postgres (host port 15433) + Redis (host port 16380)
docker compose up -d db redis
# Apply migrations, then run the API
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m uvicorn app_base.main:app --reload
# Or everything in Docker with reload (API on port 18000)
docker compose -f docker-compose.yml -f docker-compose.local.yml up

# Tests
.venv\Scripts\python.exe -m pytest -m unit -q   # no Postgres/Redis needed
.venv\Scripts\python.exe -m pytest -q           # needs Postgres on 15433 and Redis on 16380
.venv\Scripts\ruff check .

# Regenerate the API contract after any HTTP or WebSocket change
.venv\Scripts\python.exe tools\generate_api_contract.py
```
- Integration tests create and drop a `diddi_go_test` database through Alembic and force local HS256 tokens (identity mode off) — see `tests/conftest.py`.
- CI (`.github/workflows/tests.yml`): ruff, compileall, unit tests, full tests, Docker build.

## 8. Critical zones — ask before editing (proposed — human to confirm)
| Path | Why it is critical | What breaks if changed wrongly |
|---|---|---|
| `app_base/core/identity.py` | Verifies DiddiFreeID user and service JWTs (RS256, JWKS, audience, scope, subject). | Every login and every S2S call fails, or unauthorised callers get in. |
| `app_base/core/auth_deps.py` | `get_current_user`, role gates, S2S and Backoffice dependencies, shadow-user upsert. | All protected routes; admin and driver gates. |
| `app_base/core/security.py` | Local HS256 token issue/verify (used when identity mode is off, and by all integration tests). | Local auth and the whole test suite. |
| `app_base/core/service_scopes.py` | Names of the S2S scopes other modules request. | DiddiAdmin, Comms, Support, Pilotage, Pro get 403. |
| `app_base/modules/payment/application/services.py` | Payment state, DiddiPay webhook signature check, settlement, debts, Rewards confirm/correct. | Wrong amounts, double settlement, forged callbacks accepted. |
| `app_base/modules/payment/application/wallet_service.py` | Driver wallet, ledger, top-ups, withdrawals and payouts. | Driver money lost or paid twice. |
| `app_base/modules/payment/infra/diddipay_client.py` | Calls to DiddiPay with idempotency keys and S2S tokens. | Payments and payouts stop or duplicate. |
| `app_base/modules/payment/application/reconciliation.py` | Repairs payments whose webhook was lost. | Payments stuck in `requires_action`. |
| `app_base/modules/payment/infra/models.py`, `repositories.py` | Money tables and the outbox/webhook dedupe queries. | Ledger corruption, duplicate events. |
| `app_base/modules/payment/application/rewards_events.py` and `_enqueue_rewards_event` in `payment/application/services.py` | Shape of events published to the `diddigo.events.v1` stream. | DiddiRewards rejects or misreads events. |
| `app_base/modules/ride/infra/diddirewards_client.py` | Rewards contract: paths, payloads, idempotency keys, scopes. | Discounts not applied, benefits never released or consumed. |
| `alembic/versions/`, `alembic/env.py` | Schema history. Migrations run automatically at container start. | A bad migration blocks startup on staging or damages data. |
| `app_base/modules/ride/domain/entities.py` | `Ride`, `RideStatus`, `ALLOWED_TRANSITIONS`. `Ride` (161 edges) and `RideStatus` (100 edges) are graph god nodes. | Ride state machine; status values are part of the public API and WebSocket. |
| `app_base/core/errors.py`, `app_base/core/error_codes.py` | `ApiError` is the top god node (369 edges). Error body shape and codes are read by clients. | Every error response in every module. |
| `app_base/core/settings.py` | All env var names and defaults (`Settings`, graph god node). | Renaming a field silently drops a deployed variable. |
| `app_base/modules/ride/presentation/websocket.py` | WebSocket auth and event names used by the mobile app. | Live tracking and driver offers. |
| `app_base/main.py` | Router mounts and prefixes; `/health`, `/ready`, `/metrics`. | Paths change for all consumers; probes and scraping fail. |
| `tools/generate_api_contract.py`, `tools/contract_artifacts.py`, `docs/api/openapi.yaml`, `docs/api/asyncapi.yaml` | Generated public contract. The YAML files are outputs: regenerate, do not hand-edit. | Contract drifts from code; `tests/test_contract_artifacts.py` covers the generator. |
| `docs/diddigo.admin.v1.json` | Admin manifest: command paths and scopes for DiddiAdmin. | Backoffice commands break. |
| `Dockerfile`, `docker/start.sh`, `docker-compose.yml`, `docker-compose.portainer.yml` | Build, startup guards, migrations at boot, Portainer stack (branch `stage`). | Staging deployment fails. |

An agent must NOT edit these without `critical_approved: yes` in the ticket (see `coord/PROTOCOL.md`).

## 9. Known debt and traps
- **Two auth modes.** If `IDENTITY_JWKS_URL` or `IDENTITY_BASE_URL` is set, user tokens are DiddiFreeID RS256. If not, local HS256 tokens are used. Tests force the local mode. Both paths must keep working.
- **Per-request identity cost.** In identity mode `get_current_user` builds a new `IdentityTokenVerifier` (new `PyJWKClient`) per call, fetches the profile from DiddiFreeID over HTTP, then upserts and commits a shadow user. Whether the JWKS cache is really reused is not verified.
- **Role mapping.** A DiddiFreeID `user` becomes a local `passenger`. Being a driver is decided by a local `driver_profiles` row (`require_business_driver`), not by the token.
- **Client defaults frozen at import.** `DiddiPayClient` and `DiddiRewardsClient` are dataclasses whose defaults read `settings` when the module is imported. Changing settings later does not change them.
- **Rewards worker always runs.** The `rewards-events` task starts even when `DIDDI_REWARDS_ENABLED=false`. Events are only enqueued when a ride has a Rewards reservation.
- **Rewards failures are soft on quote and release, hard on reserve.** Quote falls back to full price; release is marked `release_deferred`; a failed reserve raises inside `request_ride` (exact rollback behaviour not verified).
- **Rewards may reserve less than the quote.** `request_ride` reads `reserved_amount_minor` from the reserve answer and lowers `ride.rewards_discount_amount` to it (ticket 003). If nothing was reserved the reservation is released and the ride is full price. The passenger can so pay more than the quote showed.
- **Every Rewards reservation ends by confirm or release (ticket 014).** `rewards_status` values: `quoted`, `reserved`, `confirmed`, `corrected`, `correction_deferred`, `released`, `release_deferred`, `confirmation_refused`, `release_refused`. A confirm Rewards refuses for good (400/404/409/410/422) is ended by a release with reason `confirmation_refused`: the passenger keeps the discount, nothing is consumed in Rewards. Other failures stay `reserved` / `release_deferred` and the `rewards-reservations` worker retries them. `release_refused` is a dead end that needs a human. Shared helpers: `ride/application/rewards_release.py`. Reserve sends no `expires_at`.
- **Cash ride with a Rewards discount (ticket 039).** The driver collects the discounted amount. Settlement (`_record_ride_settlement` in `payment/application/services.py`) debits the full commission and credits the discount back with ledger type `rewards_discount`, once per ride. Mobile money rides credit the full driver share and need no such line. `WalletService.record_ride_settlement` is an unused older copy of the settlement: it does not have this credit.
- **Webhook status code.** `POST /internal/webhooks/diddipay` is declared 204 but returns 200 for a duplicate event. This is intentional (comment in `payment/presentation/router.py`).
- **Browser return pages are not confirmations.** `/payments/return` and `/wallet/return` only show a page; the app must poll DiddiGo.
- **Duplicate admin surface.** Partners and KYC exist twice: user-JWT admin routes (`/v1/admin/partners`, `/v1/drivers/{id}/kyc/*`) and S2S routes (`/internal/v1/...`). `X-User-ID` is a legacy alias of `X-Backoffice-Actor`.
- **Legacy scope alias.** `ride-summary:read` is still accepted for Pilotage (`core/service_scopes.py`).
- **`MAP_PROVIDER`** accepts only `diddimap`; anything else stops startup.
- **Docs drift.** `app_base/README.md` and the docstring at the top of `ride/presentation/websocket.py` describe older states (matching "deferred"). `docs/DIDDIREWARDS-INTEGRATION.md` still lists reserve/confirm as "to implement" although the code calls them. `/openapi.json` at runtime differs from `docs/api/openapi.yaml` (see `docs/api/open-questions.md`).
- **Stray file.** `docs/frontend/DIDDIGO_FRONTEND_BRIEF_2026-10-10 - Copie.md` is a copy.
- A mojibake string ("validÃ©") exists in `core/auth_deps.py` (`DRIVER_NOT_VERIFIED` message).

## 10. Graph
`graphify-out/GRAPH_REPORT.md` = overview. Ask the graph instead of re-reading files:
`graphify query "<question>"`, `graphify explain "<Symbol>"`, `graphify path "A" "B"`.
The graph was built from commit `a921c99b`. God nodes: `ApiError`, `Ride`, `log_event()`, `UserModel`, `RideService`, `GeoPoint`, `RideStatus`, `DriverProfile`.
