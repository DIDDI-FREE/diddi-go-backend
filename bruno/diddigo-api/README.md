# DiddiGo API — Bruno collection

Pure API test suite for DiddiGo, driven entirely over HTTP (plus one hand-rolled
HMAC script for the DiddiPay webhook) — no direct DB/Python access, exactly like the
frontend consumes the API. Open `bruno/diddigo-api/` as a collection in the Bruno app,
or run it headless with `bru run` (see below).

## Environments

- **local** — `http://localhost:18000`. This is the port `docker compose -f
  docker-compose.yml -f docker-compose.local.yml up --build` actually exposes by
  default (`BACKEND_PORT` defaults to `18000` in `docker-compose.local.yml:22`) — some
  of the project's own docs say `8000`, which is only true if you run `uvicorn
  app_base.main:app --reload` directly on the host instead of through Docker. Verified
  empirically while validating this collection; adjust `base_url`/`base_url_root`/
  `auth_prefix` in the `local` environment if you run it the direct-uvicorn way instead.
  DiddiGo's own OTP/JWT auth (`IDENTITY_BASE_URL` unset). Fully self-service:
  passenger, driver, *and admin* can all be registered directly through this
  collection.
- **staging** — `https://go-staging.diddifree.com`. DiddiGo runs in *identity mode*
  (`IDENTITY_BASE_URL=https://auth-staging.diddifree.com` is set on the deployed
  stack) — auth is delegated entirely to DiddiFreeID. DiddiGo's own local
  `/v1/auth/otp/*` endpoints are not the real login path here; this collection's Auth
  folder posts to DiddiFreeID's `/identity/v1/auth/*` instead (`auth_prefix` var).
  **Admin cannot be self-registered on staging** — see below.

Both environments share one thing: every business endpoint (`/drivers`, `/rides`,
`/payments`, `/devices`, `/places`) is always DiddiGo's own API at `{{base_url}}`, in
both environments. Only the Auth folder's target host (`{{auth_prefix}}`) differs.

## Before running on staging

Set two things in the `staging` environment (Bruno sidebar → Environments):

1. `diddipay_callback_secret` — only needed for `07-Payment/04 ALT Simulate DiddiPay
   Webhook`. Leave blank to skip that one request.
2. `admin_phone` — the phone number of an **already-provisioned DiddiFreeID admin
   account**. DiddiFreeID has no self-service admin registration (see
   `01-Auth/07-register-admin-local-only.bru` docs) — `PATCH /users/{id}/role` is an
   admin-only DiddiFreeID operation this collection cannot bootstrap. Skip
   `07-register-admin-local-only.bru` on staging; run `08` and `09` directly.

## Known gaps — read before assuming a red result is a bug

| Area | Status | What it means for this collection |
|---|---|---|
| SMS delivery | Stubbed, logs only (`services.py:113`) | OTP codes never arrive by SMS on any environment yet. Every OTP-verify request needs a manual paste — see below. |
| DiddiPay config on the current staging deploy | `DIDDIPAY_*` env vars are unset on `diddi-go-backend` (verified via Portainer, 2026-08-15) | `07-Payment/03 ALT Prepare Payment` will 503 there until that's fixed. Not a bug in this collection. |
| Live WebSocket events (`ride.new_request`, `ride.driver_location`) | Not exercised by Bruno (no WS support) | This collection proves the underlying business logic works over REST — it does NOT prove the socket delivery of offers/live-location actually reaches a client. That needs a separate WS harness. |
| DiddiMap reachability | External dependency — **required for `POST /rides` itself, not just pricing/places** | `create_ride` calls DiddiMap synchronously for distance/duration; without it you get `503 DIDDIMAP_UNAVAILABLE` on ride creation, not just on `05-Places-Pricing`. `docker-compose.yml`'s own default for `DIDDIMAP_BASE_URL` is the real staging AbidjanMaps URL (not `localhost:4000` as `settings.py`'s bare default suggests) — that URL wasn't reachable from this sandbox. **Fix**: run `python bruno/diddigo-api/mock-diddimap.py` on the host, then point the local stack at it: `DIDDIMAP_BASE_URL=http://host.docker.internal:4000 docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --force-recreate app`. It implements just the two endpoints `routing_client.py` calls (`POST /api/v1/route`, `GET /api/v1/geocoding/search`) with a haversine-distance stub — good enough to unblock local E2E testing, not for anything that needs real geography. |

## The manual OTP step

No code bypass is wired into the app — this suite reads the real OTP the same way a
human would if SMS delivery were connected, just from logs instead of a text message:

1. Run `01 OTP Request <role>`.
2. Read the code:
   - **Local**: the uvicorn console prints `OTP stub — in dev, code for phone=... is
     XXXXXX.`
   - **Staging**: check the `diddi-auth` container logs in Portainer (DiddiFreeID
     stubs SMS the same way DiddiGo does).
3. Paste the 6-digit code into the matching runtime variable (`passenger_otp_code`,
   `driver_otp_code`, or `admin_otp_code`) before running the `OTP Verify` request.

This is a real gap worth closing eventually (a staging-only log-reader script could
automate step 2 via the Portainer API), but for now it's one manual paste per role,
per run — not per request.

## Suggested run order (happy path)

```
09-DiddiMap-MVP    → 01..07 (public DiddiMap smoke checks; run before DiddiGo field tests)
00-Health          → 01 Health
01-Auth             → 01..11, in order (register/otp/verify for passenger, driver, admin)
02-Driver-Onboarding → 01..03 (skip 04, only needed after a KYC rejection)
03-Admin-KYC        → 01, 02, 03 (approve — skip 04 reject, it's the alternative branch)
04-Driver-Availability → 01 Go Online (do this right before creating a ride — 30s TTL)
05-Places-Pricing   → 01, 02 (optional, depends on DiddiMap reachability)
10-MVP-Field-Test  → 01..03 (DiddiGo integration checks against DiddiMap)
06-Ride-Lifecycle   → 01..12, in order
07-Payment          → 01, 02 (cash path; 03/04 are the DiddiPay alternative branch)
08-Devices          → 01, 02
```

## MVP field test pack

The field-test pack adds two dedicated folders:

- `09-DiddiMap-MVP` validates the map provider itself: health, DB health,
  autocomplete, search, route, route proposals/detail, and road search.
- `10-MVP-Field-Test` validates that DiddiGo can consume DiddiMap for place
  search, pricing, and route-dependent ride creation.

Use the QA matrix in `docs/qa/mvp_field_test_results.csv` or the formatted Excel
workbook `outputs/qa/DiddiGo_DiddiMap_MVP_QA_Test_Matrix.xlsx` to record both
automated Bruno results and human field observations.

Folders/files numbered `9x` or suffixed `-alt`/`alternative` are deliberately NOT part
of this linear pass — they exercise branches (rejection, cancellation, decline,
DiddiPay) using their own throwaway variables (`cancel_test_ride_id`,
`decline_test_ride_id`, ...) so running them never corrupts the state the happy path
depends on.

## Running headless (CI-friendly for everything except the OTP step)

```bash
cd bruno/diddigo-api
npx @usebruno/cli run --env local . -r
```

`bru run` must be invoked from the collection root (where `bruno.json` lives) — `-r`
recurses into subfolders; `--recursive` is not a real flag despite reading like one.

Since the OTP step is manual, a fully unattended CI run isn't there yet for the Auth
folder specifically — but every other folder can run unattended against an
already-authenticated set of runtime variables (export them from a prior interactive
run, or wire up the log-reader script mentioned above).

## Validated end-to-end (not just parsed)

This collection was run for real against a live local stack (`docker compose up`,
Postgres/PostGIS + Redis + app, plus the `mock-diddimap.py` stub) all the way through:
register/OTP/login for passenger, driver, and admin → driver profile + vehicle →
admin KYC approval → go online → create ride → matched → accept → `driver_en_route` →
`in_progress` → `completed` (real fare computed: 783 XOF from the mock's haversine
distance) → cash payment confirmed (`status: "collected"`). Also confirmed for real:
the passenger-cancel and 401-on-expired-token paths.

That run caught two real bugs — both in this collection, not in DiddiGo — since fixed:

1. **Phone/plate/license/device-token pre-request scripts ignored `--env-var`
   overrides.** They checked `bru.getVar()` (runtime-variable scope) only; a value
   supplied via `--env-var` or the environment panel lives in a different scope
   (`bru.getEnvVar()`), so the guard always looked unset and silently regenerated a
   random value — meaning `register` and `otp/verify` ran against two *different*
   phone numbers when a value was pinned externally. Every generator script now checks
   both scopes (`bru.getVar(...) || bru.getEnvVar(...)`) before falling back to
   `Date.now()`-based generation. A couple of test-side `bru.getVar()` reads had the
   same blind spot and got the same fix (`03-Admin-KYC/01`, `06-Ride-Lifecycle/12`).
2. **`06-Ride-Lifecycle/02 Get Ride` asserted `driver != null` before "03 Accept
   Ride" had run.** `ride.driver_id` is only set inside `MatchingService.accept()` —
   an *open offer* (`matching_offer_opened` in the logs) is not the same as an
   *assigned* driver. Fixed the assertion to check `status: "requested"` /
   `driver: null` instead, matching the real state at that point in the sequence.

Two more things the live run surfaced that are just realistic timing, not bugs:
- **The 15s offer TTL is tight.** Any manual pause between "Create Ride" and "Accept
  Ride" (debugging, reading logs, editing files) can expire the offer
  (`409 OFFER_EXPIRED`). Run those two back-to-back.
- **One active ride per passenger.** `POST /rides` returns `409
  ACTIVE_RIDE_ALREADY_EXISTS` if the passenger's previous ride was created but never
  reached a terminal state (accepted-and-completed, or cancelled) — an expired offer
  still counts as active. Cancel or complete a stale ride before creating another for
  the same passenger.

## Design notes

- **Phone numbers and plate numbers are generated per run** (pre-request scripts using
  `Date.now()`), so re-running the whole collection never hits `409
  PHONE_ALREADY_REGISTERED` / `409 PLATE_ALREADY_REGISTERED`.
- **Matching runs synchronously** inside `POST /rides` — no polling or WebSocket is
  needed to test the core matching/accept/complete/pay flow. See
  `06-Ride-Lifecycle/01-create-ride.bru` docs for the code reference.
- **`POST /drivers/online` alone is enough presence** to be matched — it seeds both the
  Redis `seen` and `available` markers in one REST call
  (`driver_location.py:56-84`). The 30s presence TTL means "Go Online" must run
  shortly before "Create Ride", not once at the top of a long session.
