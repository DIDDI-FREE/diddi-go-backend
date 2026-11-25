# Integrations — diddi-go-backend

> Outside view: how this module talks to the other DiddiFree modules.
> Everything in "Exposes" is a **contract**. Changing it follows the contract-change rule in `coord/PROTOCOL.md`.
> Last checked against code: 2026-11-25 (branch `feat/049-driver-bonuses`, on `7bf4002` + driver bonuses route, ticket 049). Mark anything unsure as "not verified".
> Lines marked "staging" come from tester campaign 001 (2026-11-24, `coord/outbox/001-staging-diddigo-vs-support-modules.md`), not from this repo's code.

Consumers were checked by reading sibling folders under `D:\DIDDI-DEV` (read-only). Repos that are not cloned there (DiddiRadar/Pilotage, DiddiFree Pro) are "not verified".

## 1. Exposes (others depend on this)

### HTTP / WebSocket APIs
| Endpoint or group | Auth (user JWT / S2S / none) | Known consumers | Defined in (file) |
|---|---|---|---|
| `GET /health`, `GET /ready` (`/ready` answers 200 with `"status": "degraded"` when DB and Redis are up but a worker is stale: read the body, not the HTTP code) | none | `diddi-admin` (`backend/app/modules/integrations/adapters.py`, `/health`); `diddi-observe` registry lists `diddigo`; test harness `tests/modules/diddigo` | `app_base/main.py` |
| `GET /metrics`, `GET /internal/metrics` | static bearer token (`METRICS_BEARER_TOKEN`) | `diddi-observe` (Prometheus scrape config; live scraping not verified) | `app_base/main.py` |
| `/v1/auth/*` (register, OTP, refresh, me) | none / user JWT (local HS256 mode) | not verified (the mobile app logs in through DiddiFreeID) | `app_base/modules/auth/presentation/router.py` |
| `/v1/devices/register`, `/unregister` | user JWT | `diddifree-frontend` | `app_base/modules/notification/presentation.py` |
| `/v1/places/search`, `/v1/rides/*` (estimate, create, accept, decline, status, arrive, start, waiting, stops, supplements, cancel, rating, location-samples, share-link, emergency, active/current) | user JWT | `diddifree-frontend` (`app/lib/features/diddigo/`); `diddi-review-worker` (`app/adapters/diddigo.py`: estimate, create, accept, arrive, start, status, location-samples, rating); `diddi-admin` reads `GET /v1/rides` | `app_base/modules/ride/presentation/router.py` |
| `GET /v1/rides/shared/{token}` | none (share token) | `diddifree-frontend` | same file |
| `WS /v1/ws?token=` | user JWT in query string | `diddifree-frontend` (path seen; event handling not verified) | `app_base/modules/ride/presentation/websocket.py` |
| `/v1/me/*` (capabilities, scores, emergency-contact), `/v1/pro/metiers` | user JWT | `diddifree-frontend` (`/me/capabilities`, `/me/emergency-contact`) | `app_base/modules/ride/presentation/capabilities_router.py` |
| `GET /v1/me/offers`, `GET /v1/me/offers/{offer_id}`, `POST /v1/me/referral/code` (`Idempotency-Key`), `GET /v1/me/referral` (ticket 040, relays to DiddiRewards) | user JWT | `diddifree-frontend` (announced in ticket to the frontend; not used yet) | `app_base/modules/ride/presentation/rewards_router.py` |
| `GET /v1/drivers/me/bonuses` (ticket 049, relay of the Rewards read route) | user JWT with a driver profile (any status) | `diddifree-frontend` (announced; not used yet) | same file |
| `/v1/drivers/*` (profile, vehicle, KYC resubmit, online/offline, nearby, me) | user JWT (driver or admin role) | `diddifree-frontend`; `diddi-admin` calls `GET /v1/drivers/kyc` and `/v1/drivers/{id}/kyc` (legacy path, next to the internal one) | `app_base/modules/ride/presentation/driver_router.py` |
| `/v1/payments/{ride_id}` (+ `/prepare`, `/confirm-cash`), `/v1/passenger/debts/*` | user JWT | `diddifree-frontend` | `app_base/modules/payment/presentation/router.py` |
| `/v1/drivers/me/wallet/*` (ledger, earnings, topups, withdrawals) | user JWT (driver) | `diddifree-frontend` (wallet, ledger, topups seen) | same file |
| `/v1/admin/drivers/{id}/wallet*`, `/v1/admin/payments/*`, `/v1/admin/partners/*`, `/v1/admin/vehicles/*`, `/v1/admin/logs/*` | user JWT with role `admin` | `diddi-admin` calls `/v1/admin/drivers/{id}/wallet` and `/wallet/ledger`; others not verified | payment, partner, ride (`driver_router.py`), observability routers |
| `GET /payments/return`, `GET /wallet/return` | none (one-time `context` token) | browser redirect after DiddiPay checkout; `diddifree-frontend` references `/payments/return` | `app_base/modules/payment/presentation/router.py` |
| `POST /internal/webhooks/diddipay` | HMAC-SHA256 of raw body in `X-DiddiPay-Signature`, plus `X-DiddiPay-Event-ID` | DiddiPay (`diddi-pay-backend`; sender code not verified) | same file; check in `payment/application/services.py` (`apply_diddipay_webhook`) |
| `GET/POST /internal/v1/drivers/kyc`, `/{driver_id}/kyc[/approve|/reject]`, `/vehicles/.../kyv[...]` | S2S, subject `service:backoffice`, scopes `diddigo:kyc:read` / `diddigo:kyc:decide` | `diddi-admin` (`backend/app/modules/diddigo.py`, `integrations/adapters.py`, `manifests/manifest.json`) | `app_base/modules/ride/presentation/kyc_internal_router.py` |
| `POST /internal/v1/drivers/provision`, `PATCH /internal/v1/drivers/{id}/profile-photo` | S2S backoffice, scope `diddigo:drivers:write` | `diddi-admin` (via manifest commands; exact call not verified) | `app_base/modules/ride/presentation/driver_internal_router.py` |
| `/internal/v1/admin/partners/*` | S2S backoffice, scopes `diddigo:partners:read` / `:write` | `diddi-admin` (reads: list, detail, members, drivers; writes not verified) | `app_base/modules/partner/presentation/internal_router.py` |
| `/internal/v1/admin/dispatch/*` (config, priority rules, boosts) | S2S backoffice, scopes `diddigo:dispatch:read` / `:write` | not verified | `app_base/modules/ride/presentation/dispatch_admin_router.py` |
| `GET /internal/v1/comms/tasks/{task_type}/{task_id}` | S2S, subject `service:diddicomms`, scope `diddigo:comms-task:read`, fixed client id | `diddi-comms` (`app_base/modules/context/infra/resolver_client.py`) | `app_base/modules/ride/presentation/comms_task_router.py` |
| `GET /internal/v1/support/ride/{ride_id}/context` | S2S, subject `service:diddisupport`, scope `diddigo:support-context:read`, fixed client id | `diddi-support` (`src/diddi_support/infrastructure/context/http.py`) | `app_base/modules/ride/presentation/support_context_router.py` |
| `GET /internal/v1/scores/users/{id}`, `/rides/{id}` (contract `diddi.score.v1`) | S2S, subject `service:diddifreepro`, scope `diddigo:scores:read` | DiddiFree Pro — not verified (no repo found) | `app_base/modules/ride/presentation/score_contract_router.py` |
| `GET /internal/v1/ride-summary`, `/internal/pilotage/{daily-summary,finance-summary,breakdown,health-summary}` (contract `pilotage.v1`) | S2S, subject `service:pilotage`, scope `diddigo:ride-summary:read` (legacy `ride-summary:read` accepted) | DiddiRadar — not verified (repo not cloned) | `app_base/modules/ride/presentation/summary_router.py` |

Contract source of truth: `docs/api/openapi.yaml` (HTTP) and `docs/api/asyncapi.yaml` (WebSocket), generated from code by `tools/generate_api_contract.py`. Human-readable: `docs/api/API_CONTRACT.md`, `docs/realtime/WEBSOCKET_CONTRACT.md`, `docs/api/error-catalog.md`. Error body shape comes from `ApiError` in `app_base/core/errors.py`.

### Events published
| Stream / topic | Event name | Payload defined in | Known consumers |
|---|---|---|---|
| Facts protocol v1: direct call `POST /internal/v1/rewards/integrations/diddigo/facts` (no stream) | `order.paid` | `_rewards_fact` in `app_base/modules/payment/application/services.py` | `diddi-rewards` (`app/modules/integrations/benefits_adapter.py`, `/facts`; contract ticket 069) |
| same | `order.refunded` (full refunds only) | same | same |
| same | `order.cancelled` (payment cancelled before paid) | same | same |

- Every paid ride is reported, discount or not. Fields: `schema_version` `"1"`, `fact_id` = `diddigo:<type>:<ride_id>` (also the `Idempotency-Key`), `order_id` = ride id, `customer_id` = passenger user id, `occurred_at`; `order.paid` adds `amount_minor` (fare before discount), `discount_minor`, `currency`, `payment_method` (`cash` / `online`), `professional_id` (driver's DiddiFreeID user id), `parent` (`null`), `rewards_reservation_id`; `order.refunded` adds `refunded_amount_minor`, `full: true`.
- Not reported: partial refunds (DiddiGo does not record the refunded amount; they change no count in Rewards), and ride cancellations that never had a payment.
- Outbox table `payment.rewards_event_outbox` (key `event_id` = `fact_id`), sent by the `rewards-events` worker (`payment/application/rewards_events.py`) until accepted. 5xx, 401/403 and timeouts: retried with growing delays. 400/404/409/422: row marked `failed`, log `rewards.fact.refused`, never resent. Rows of the old stream format (`ride.payment_confirmed`…) are left as they are and never sent.
- The Redis stream `diddigo.events.v1` is no longer written (ticket 064 superseded).

### Other (tokens, JWKS, shared files, packages)
| What | Known consumers | Defined in |
|---|---|---|
| S2S scope names, audience `diddigo` | `diddi-admin`, `diddi-comms`, `diddi-support`; DiddiFreeID must register them (not verified) | `app_base/core/service_scopes.py`, `docs/reference/permissions.md` |
| Admin manifest `backoffice.v1` / `admin.v1` (resources, commands, paths, scopes) | `diddi-admin` (`backend/manifests/manifest.json` has DiddiGo entries; sync method not verified) | `docs/diddigo.admin.v1.json`, test `tests/test_backoffice_manifest.py` |
| Observability manifest | `diddi-observe` (not verified) | `docs/observability/diddigo-observability-v1.yaml` |
| Idempotency key formats sent to others (`diddigo:ride:<id>`, `diddigo:ride:<id>:rewards-reserve:v1`, `...:rewards-release:v1`, `diddigo:driver_withdrawal:<id>:v1`) | DiddiPay, DiddiRewards | `payment/application/services.py`, `wallet_service.py`, `ride/application/services.py` |
| Local JWT (HS256) | this repo only; not a contract for others | `app_base/core/security.py` |
| Docs portal (mkdocs) | humans; staging URL in `README.md` | `mkdocs.yml`, `Dockerfile.docs`, `docker-compose.docs.yml` |

DiddiGo publishes no JWKS and no shared package.

## 2. Consumes (this module depends on others)

### Calls to other modules
| Module (repo) | What is called | Why | Client code (file) | Config / env var | If it is down |
|---|---|---|---|---|---|
| DiddiFreeID (`diddifree-auth`) | JWKS `/.well-known/jwks.json` | Verify user and service JWTs (RS256) | `app_base/core/identity.py` | `IDENTITY_BASE_URL`, `IDENTITY_JWKS_URL`, `IDENTITY_ISSUER` | Service tokens: `503 SERVICE_JWKS_UNAVAILABLE`. User tokens: `401 TOKEN_INVALID`. |
| DiddiFreeID | `GET /identity/v1/users/me` with the user's token | Load profile for each authenticated request. Fields read: `phone`, `full_name`, `role`, `status`, `requested_role`, `created_at` (ISO 8601 UTC, ticket 046); unknown fields are ignored | `app_base/core/identity.py` (`fetch_identity_profile`, `_profile_created_at`) | `IDENTITY_PROFILE_URL`, `IDENTITY_SERVICE_KEY` | Error `IDENTITY_PROFILE_ERROR` on 4xx/5xx; network failure handling not verified. A **new** user whose profile is missing or has no readable `created_at` is refused with `502 IDENTITY_PROFILE_INVALID` (message names the exact problem); existing users are not affected. |
| DiddiFreeID | `POST /identity/v1/auth/service/token` (client credentials) | Get S2S tokens for Pay, Files, Rewards, ID | each client below | `IDENTITY_BASE_URL` + per-client secrets | The dependent call fails. |
| DiddiFreeID | `.../identity/v1/pro/internal/users/{id}/capabilities/diddigo/driver/status` (audience `diddifree-id`, scope `capabilities:write`) | Push driver status to the identity capability model | `app_base/modules/ride/infra/identity_capability_client.py`, worker `ride/application/capability_projection_worker.py` | `IDENTITY_SERVICE_CLIENT_ID`, `IDENTITY_SERVICE_CLIENT_SECRET`, `CAPABILITY_PROJECTION_*` | Events stay in `driver_capability_projection_events` and are retried with backoff. |
| DiddiMap (`abidjanmaps-backend`) | `POST /api/v1/route`, `GET /api/v1/geocoding/search`, `/map-traces/{start,positions,finish,analyze}` under `/api/v1` or `/api/v1/integrations/diddigo` | Price, ETA, place search, GPS trace analysis | `app_base/modules/ride/infra/routing_client.py` | `DIDDIMAP_BASE_URL` (staging: `http://abidjanmaps-backend-staging.diddifree.com`, plain HTTP, see PM ticket 010), `DIDDIMAP_SERVICE_CLIENT_ID`, `DIDDIMAP_SERVICE_CLIENT_SECRET`, `DIDDIMAP_SERVICE_TOKEN_URL`, `DIDDIMAP_SERVICE_AUDIENCE`, `DIDDIMAP_SERVICE_TOKEN`, `DIDDIMAP_ACCESS_TOKEN`, `MAP_PROVIDER` | Quotes fail with an explicit error (no fake distance, `docs/integrations/diddimap.md`). ETA ranking in matching falls back to distance order (comment in `core/settings.py`). |
| DiddiPay (`diddi-pay-backend`) | `POST /payment-intents`, `GET /payment-intents/{id}`, `POST /payouts`, `GET /payouts/{id}`, `GET /payouts?business_reference=` | Ride payment, wallet top-up, driver withdrawal, reconciliation | `app_base/modules/payment/infra/diddipay_client.py` | `DIDDIPAY_BASE_URL`, `DIDDIPAY_CLIENT_ID`, `DIDDIPAY_SERVICE_CLIENT_SECRET` (S2S) or `DIDDIPAY_SERVICE_KEY` (legacy), `DIDDIPAY_CALLBACK_SECRET`, `DIDDIPAY_HTTP_TIMEOUT_SECONDS` | `503 PAYMENT_PROVIDER_UNAVAILABLE`; not configured → `503 PAYMENT_CONFIGURATION_MISSING`. Cash still works. Lost webhooks are repaired by the reconciliation worker. |
| DiddiRewards (`diddi-rewards`) | `POST /internal/v1/rewards/integrations/diddigo/benefits/{quote,reserve,confirm,correct}`, `.../benefits/reservations/{reservation_id}/release` and `.../diddigo/reconciliation`; `GET .../diddigo/consumers/{id}/offers`, `GET .../consumers/{id}/referral-code`, `POST .../consumers/{id}/referral-code/apply` (ticket 040, contract 061); `POST .../diddigo/facts`, `GET .../diddigo/actions`, `POST .../diddigo/actions/{id}/done` (facts protocol, contract 069); `GET .../diddigo/professionals/{user_id}/bonuses` (contract 057) | Campaign discount on a ride; offers and referral codes shown in the app; report paid / refunded / cancelled rides and pay the driver bonuses Rewards decides | `app_base/modules/ride/infra/diddirewards_client.py` | `DIDDI_REWARDS_ENABLED`, `DIDDI_REWARDS_AUTO_QUOTE_ENABLED`, `DIDDI_REWARDS_BASE_URL`, `DIDDI_REWARDS_CLIENT_ID`, `DIDDI_REWARDS_SERVICE_CLIENT_SECRET` or `DIDDI_REWARDS_SERVICE_TOKEN`, `DIDDI_REWARDS_SERVICE_SCOPES`, `DIDDI_REWARDS_TIMEOUT_SECONDS` | Quote: full price, `rewards.reason = "rewards_unavailable"`. Release: marked `release_deferred`, retried every 60 s by the `rewards-reservations` worker. Reserve: error raised in ride creation. Confirm: retried by the same worker; if Rewards refuses it for good (400/404/409/410/422) DiddiGo releases the reservation with reason `confirmation_refused` (ticket 014). Correct: `correction_deferred`, no automatic retry. |
| DiddiFiles (`diddi-files`) | `GET /v1/files/{file_id}/public-url` (audience `diddifiles`, scope `files:read`) | Resolve public URL of a driver profile photo | `app_base/modules/ride/infra/diddifiles_client.py` | `DIDDIFILES_BASE_URL` (staging: `https://diddifiles.diddifree.com`), `DIDDIFILES_SERVICE_CLIENT_ID`, `DIDDIFILES_SERVICE_CLIENT_SECRET`, `DIDDIFILES_TIMEOUT_SECONDS` | The client never raises: any error, a non-200 answer or a private file gives `photo_url: null` in the ride detail. Staging: token 200, then `public-url` 409 `FILE_NOT_PUBLIC` for a private file. |

**DiddiRewards behaviour DiddiGo relies on** (tickets 003, 014, 015, 016, 040 with Rewards contract 061; live on Rewards staging since 2026-11-25):
- Quote: `campaign_id` is sent only when the app sent one. With `DIDDI_REWARDS_AUTO_QUOTE_ENABLED=true` DiddiGo asks Rewards at every estimate without `campaign_id`; Rewards picks the customer's best offer and names it in `campaign_id` of the answer (ticket 040). Off by default. Every quote sends `honour_until` = the DiddiGo quote `expires_at`.
- Quote answer used: `quote_id` (stored on `ride.ride_quotes.rewards_quote_id`) and `offer` (stored on the quote, then on the ride without `history`, relayed untouched to the app).
- Reserve sends `quote_id`. While the quote is valid Rewards reserves the quoted amount (`quote_honoured: true`). Refusal `409 {"detail": {"code": "right_used_up"}}` becomes DiddiGo `409 REWARDS_OFFER_ALREADY_USED`: the request is rolled back, no ride, quote not consumed. Other 409 codes (`quote_already_used`, `quote_mismatch`, `quote_unknown`) stay `REWARDS_OPERATION_FAILED`.
- Reserve can still grant less than asked when the quote is not honoured (`quote_expired`, `right_partly_used`, or no `quote_id`): DiddiGo uses `reserved_amount_minor` as the ride discount, and releases at once when it is 0.
- Offers and referral relays need scopes `diddirewards:benefits:quote` (offers), `diddirewards:referrals:read` and `diddirewards:referrals:write` (referral). The last two are **not** in the default `DIDDI_REWARDS_SERVICE_SCOPES`: asking DiddiFreeID for a scope the client does not hold would break every Rewards call. Add them to the stack variable once DiddiFreeID grants them. Until then the referral routes answer `503 REWARDS_UNAVAILABLE`.
- Facts protocol (contract 069): `POST .../diddigo/facts` and `GET .../diddigo/actions?status=pending`, then `POST .../diddigo/actions/{action_id}/done` with `{"status": "done", "reference": <wallet entry id>}` or `failed` + `reason`, scope `diddirewards:facts:report`. Each `credit_professional` action writes one `rewards_bonus` ledger line (`reference_type` `rewards_action`, `reference_id` = `action_id`, unique per driver), so a replay never pays twice. Unknown driver, bad amount or non-XOF: confirmed `failed`. Pending actions are re-read every 60 s.
- Driver bonuses read: `GET .../diddigo/professionals/{driver user id}/bonuses`, scope `diddirewards:professional-bonuses:read`, relayed untouched (`bonuses` list) to `GET /v1/drivers/me/bonuses`; any failure answers `503 REWARDS_UNAVAILABLE`.
- Like the referral scopes, `diddirewards:facts:report` and `diddirewards:professional-bonuses:read` are not in the default scope list: it must be in `DIDDI_REWARDS_SERVICE_SCOPES` on the stack. Without it facts get 403 and stay queued (retried), nothing is lost.
- Release is the common route `benefits/reservations/{reservation_id}/release` (ticket 016), body `{"reason": "..."}`, scope `diddirewards:benefits:reserve`, answer 200 with the reservation (`duplicate: true` when already released or expired). The old command route `benefits/release` is no longer called. Reasons sent: the ride `cancellation_reason`, `no_driver_found`, `nothing_reserved`, `confirmation_refused` (cut to 180 characters). A retry always sends the same reason with the same `Idempotency-Key` (another reason would get 409).
- A reservation nobody closes expires on the Rewards side after 24 h. DiddiGo sends no `expires_at`. A confirm on an expired reservation gets 409, which DiddiGo ends by a release (answered as already done).
- Several pending reservations can exist on one entitlement: quote and reserve answer with what is left.

DiddiGo only stores `file_id` values for KYC/KYV documents; the upload is done by the client app directly with DiddiFiles (`docs/integrations/diddifiles.md`).

### Events consumed
| Stream / topic | Event | From (repo) | Handler (file) |
|---|---|---|---|
| none | — | — | — |

No Redis Stream or pub/sub consumer exists in `app_base/` (no `xadd`, no `xread*` since the facts protocol). The only inbound async message is the DiddiPay HTTP webhook listed above.

### External services (not DiddiFree)
| Service | Used for | Config / env var |
|---|---|---|
| Firebase Cloud Messaging | Push notifications (ride offers, status) — `app_base/modules/notification/infra/fcm.py` | `PUSH_ENABLED`, `FCM_PROJECT_ID`, `FCM_SERVICE_ACCOUNT_JSON`, `FCM_SERVICE_ACCOUNT_FILE` |
| Senndo / Yellika SMS | SMS provider port — `app_base/modules/notification/infra/sms.py` | `SMS_PROVIDER` (`disabled` by default), `SENNDO_API_KEY`, `SENNDO_BASE_URL`, `SENNDO_SENDER`, `YELLIKA_API_TOKEN`, `YELLIKA_BASE_URL`, `YELLIKA_SENDER_ID` |
| Evolution API (WhatsApp) | Emergency alerts — `app_base/modules/ride/application/emergency_notifications.py` | `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `EMERGENCY_SUPPORT_WHATSAPP` |
| SMTP | Emergency email | `EMERGENCY_SMTP_HOST`, `EMERGENCY_SMTP_PORT`, `EMERGENCY_SMTP_USERNAME`, `EMERGENCY_SMTP_PASSWORD`, `EMERGENCY_EMAIL_FROM`, `EMERGENCY_SUPPORT_EMAIL` |
| Loki | Admin log search — `app_base/modules/observability/infra/loki.py` | `LOKI_BASE_URL` (read with `os.getenv`, not in `Settings`) |
| OTLP collector (DiddiObserve) | Logs and traces export | `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_LOGS_ENABLED`, `OTEL_TRACES_SAMPLER_ARG` |
| Shared Redis (`diddi-general-redis`) | Was the target of the Rewards event stream; no longer written since the facts protocol | `DIDDI_REWARDS_EVENTS_REDIS_URL` (unused); external Docker network `diddi-general-redis` in `docker-compose.portainer.yml` |

## 3. Auth between modules
**How DiddiGo proves who it is.** It asks DiddiFreeID for a client-credentials token (`POST /identity/v1/auth/service/token`, form fields `grant_type`, `client_id`, `client_secret`, `audience`, `scope`, header `X-Client-ID`) and sends `Authorization: Bearer <token>` + `X-Client-ID`. Tokens are cached in memory until about 30 s before expiry.

| Target | Audience | Scopes requested | Secret env var |
|---|---|---|---|
| DiddiPay | `diddipay` | `diddipay:payment-intents:write`, `:read`, `diddipay:payouts:write`, `:read` (one token per scope) | `DIDDIPAY_SERVICE_CLIENT_SECRET` (else legacy header `X-Service-Key` from `DIDDIPAY_SERVICE_KEY`). Staging: the secret is not set, the legacy `X-Service-Key` path is the live one (DiddiPay answers 201). |
| DiddiRewards | `diddirewards` | value of `DIDDI_REWARDS_SERVICE_SCOPES` (default: `diddirewards:benefits:quote`, `:reserve`, `:release`, `:consume`, `:correct`, `diddirewards:reconcile`) in one token | `DIDDI_REWARDS_SERVICE_CLIENT_SECRET` (or a static `DIDDI_REWARDS_SERVICE_TOKEN`, which wins) |
| DiddiFiles | `diddifiles` | `files:read` | `DIDDIFILES_SERVICE_CLIENT_SECRET` |
| DiddiFreeID capabilities | `diddifree-id` | `capabilities:write` | `IDENTITY_SERVICE_CLIENT_SECRET` |
| DiddiMap | `DIDDIMAP_SERVICE_AUDIENCE` (default `diddimap`) | `diddimap:routes:read`, `diddimap:places:read`, `diddimap:map-traces:write`, `diddimap:map-traces:analyze` | `DIDDIMAP_SERVICE_CLIENT_SECRET`, token URL `DIDDIMAP_SERVICE_TOKEN_URL`. Staging: the secret is empty and `DIDDIMAP_SERVICE_TOKEN` is set, so DiddiGo uses the legacy static token and these scopes are never requested (traces work: start 201, positions 201, finish 200, analyze 200). |

**How DiddiGo checks callers.**
- Users: `Authorization: Bearer`. DiddiFreeID RS256 token checked with JWKS and issuer `IDENTITY_ISSUER`, claim `status` must be `active`. If identity is not configured: local HS256 token signed with `JWT_SECRET` (`app_base/core/auth_deps.py`, `identity.py`, `security.py`).
- Services: Bearer service token + header `X-Client-ID`. Checked: RS256 signature, issuer, audience `diddigo`, `role` and `token_type` = `service`, `status` = `active`, `client_id` claim equals `X-Client-ID`, expected `sub`, required scope (`decode_service_token` in `app_base/core/identity.py`).
- Expected subjects: `service:backoffice`, `service:diddicomms`, `service:diddisupport`, `service:diddifreepro`, `service:pilotage`. Fixed client ids for Comms, Support, Pro come from `DIDDICOMMS_SERVICE_CLIENT_ID`, `DIDDISUPPORT_SERVICE_CLIENT_ID`, `DIDDIFREEPRO_SERVICE_CLIENT_ID`.
- Backoffice write commands also need `X-Backoffice-Actor` (or legacy `X-User-ID`): the UUID of an active local admin user. Most also use an `Idempotency-Key` stored in Redis (`app_base/core/s2s_command_store.py`).
- DiddiPay webhook: HMAC-SHA256 of the raw body with `DIDDIPAY_CALLBACK_SECRET`.
- Metrics: bearer equal to `METRICS_BEARER_TOKEN` (alias `OBSERVABILITY_METRICS_TOKEN`).

## 4. If you change X, tell Y
| If you change... | These repos must know | How they are affected |
|---|---|---|
| Any `/v1/rides`, `/v1/payments`, `/v1/drivers`, `/v1/passenger/debts`, `/v1/me`, `/v1/devices` path, body or status value | `diddifree-frontend`, `diddi-review-worker`, `tests` | App screens and review/E2E journeys break. |
| WebSocket URL, auth or event names/payloads | `diddifree-frontend` | Live tracking and driver offers stop. |
| `RideStatus` or `PaymentStatus` values | `diddifree-frontend`, `diddi-review-worker` (sends `status` on `PATCH /v1/rides/{id}/status`); other readers of ride data (`diddi-admin`, `diddi-support`, `diddi-comms`) — their parsing is not verified | Status strings travel in API and WebSocket payloads. |
| Error body shape or error codes | all HTTP consumers (which codes each one reads is not verified) | Error handling keyed on `code`. |
| `/internal/v1/drivers/*` (KYC, provision), `/internal/v1/admin/partners/*`, `/v1/admin/drivers/*/wallet*`, `docs/diddigo.admin.v1.json` | `diddi-admin` | Backoffice screens and commands fail. |
| `/internal/v1/comms/tasks/...` response or auth | `diddi-comms` | Chat/call authorisation for rides. |
| `/internal/v1/support/ride/{id}/context` response or auth | `diddi-support` | Support case context. |
| `/internal/pilotage/*`, `/internal/v1/ride-summary` | DiddiRadar (not cloned — tell the PM) | KPI collection. |
| `/internal/v1/scores/*` | DiddiFree Pro (owner not verified — tell the PM) | Score projection. |
| Scope names in `core/service_scopes.py`, audience `diddigo`, expected subjects or client ids | `diddifree-auth` (client registration) and every S2S caller above | Callers get 401/403. |
| Scopes or audiences DiddiGo requests (`DIDDI_REWARDS_SERVICE_SCOPES`, `diddipay:*`, `diddimap:*`, `files:read`, `capabilities:write`) | `diddifree-auth` | The service client must be allowed these scopes, or token requests return 403. |
| Fact fields, `fact_id` format, or the wallet line written for a `credit_professional` action | `diddi-rewards` | Facts refused (4xx) or counted twice; bonuses not paid or not confirmed. |
| Rewards call payloads or idempotency keys | `diddi-rewards` | Reservation, release, consumption. |
| DiddiPay webhook handling (headers, signature, statuses) or `business_reference` format | `diddi-pay-backend` | Callbacks rejected; payments not matched. |
| `/health`, `/ready`, `/metrics`, log/trace fields | `diddi-observe`, `tests` | Probes, scraping, dashboards. |
| `docker-compose.portainer.yml` env var names | whoever runs the Portainer stack (human) | Variables silently ignored at deploy. |

## 5. Open questions
- **DiddiSend calls an endpoint DiddiGo does not have.** `diddi-send/app/modules/delivery/infra/diddigo_client.py` calls `GET {diddigo}/api/v1/couriers/{id}/availability`. No such route exists here. It only runs when DiddiSend's validation flag is on. Likely dead or planned.
- **`ride.completed` is expected but never sent.** `diddi-rewards/app/modules/integrations/diddigo/events.py` handles `ride.completed`; DiddiGo only emits `ride.payment_confirmed`, `ride.refunded`, `ride.cancelled`.
- **Stream field compatibility** — moot since the facts protocol: DiddiGo no longer publishes to the stream.
- **DiddiMap S2S scope names differ.** DiddiGo would request `diddimap:map-traces:write`; DiddiMap and DiddiFreeID know `diddimap:traces:write`. Unused today (static token on staging), but the S2S path would fail the day it is switched on.
- **Where DiddiPay gets the webhook URL** — settled (staging): `PAYMENT_CALLBACK_TARGETS` on the DiddiPay stack has an entry `diddigo`. `DIDDIGO_PAYMENT_CALLBACK_URL` is only used here as a fallback for the browser return URL sent as `callback_url`.
- **DiddiAdmin and KYC** — settled (staging): the screens call S2S `/internal/v1/drivers/kyc` (client `backoffice-staging-diddigo`, subject `service:backoffice`, scope `diddigo:kyc:read`). `GET /v1/rides` is called with the admin's DiddiFreeID JWT (role `admin`) and answers 200.
- **`401 TOKEN_INVALID` leaks the decoder message** to the caller (for example `Invalid header string: 'utf-8' codec can't decode byte…`). Minor, not fixed.
- **Pilotage and DiddiFree Pro consumers** are not verified (repos not available locally).
- **DiddiFood**: no call into DiddiGo found in `diddifood-backend` code (only docs and tests mention it).
- **Service-key header to DiddiFreeID** (`IDENTITY_SERVICE_KEY` → `X-Service-Key` on the profile call): whether DiddiFreeID still uses it is not verified.
- **`docs/DIDDIREWARDS-INTEGRATION.md`** is behind the code (lists reserve/confirm as not done). Newer notes: `docs/DIDDIREWARDS-HANDOFF-2026-11-24.md` (not read).
- `.env.example` and `docs/configuration/CONFIGURATION_REFERENCE.md` were not read; env var names above come from `app_base/core/settings.py` and the client files.
