# Dispatch engine E2E (SCRUM-63) — live staging

End-to-end tests that drive the **real** `go-staging` API to verify the dispatch
engine (offer waves, ETA ranking, priority cap, radius/budget, ledger). They are
**deselected by default** and **skip** unless credentials are set, so a normal
`pytest` run never touches the network.

## What it does / needs (read before running)

- **Real OTP.** The passenger, each driver, and the admin log in by OTP. The
  harness **pauses and prompts** you to paste each code (a human receives the
  SMS). For an unattended rerun you can pre-set `DIDDIGO_OTP_<digits>` (e.g.
  `DIDDIGO_OTP_2250700000101=123456`) — but codes expire (~5 min).
- **An admin account.** Driver **KYC approve** and vehicle **KYV approve** are
  `require_role("admin")` routes, so `DIDDIGO_E2E_ADMIN_PHONE` must be an account
  that is already `role=admin` on staging.
- **S2S credentials** for the `/internal/v1/admin/dispatch/*` routes
  (client-credentials; the admin's DiddiFreeID id is sent as `X-Backoffice-Actor`).
- **It mutates staging** (dispatch config, temporary priority boosts) and creates
  throwaway `+225070000012X` drivers + a test passenger. Config changes are always
  **restored** via the `dispatch_config_guard` fixture; boosts are short-lived.
  Run it when staging isn't under real traffic — a real online driver near the
  test pickup could otherwise intercept an offer and skew the ranking assertions.
- Requires the `websockets` package (already in the dev env) to observe which
  drivers a wave was offered to.

## Environment variables

| Var | Required | Default |
| --- | --- | --- |
| `DIDDIGO_E2E_BASE_URL` | no | `https://go-staging.diddifree.com` |
| `DIDDIGO_E2E_ADMIN_PHONE` | **yes** | — (must be role=admin) |
| `DIDDIGO_S2S_TOKEN_URL` | **yes** | — |
| `DIDDIGO_S2S_CLIENT_ID` | **yes** | — |
| `DIDDIGO_S2S_CLIENT_SECRET` | **yes** | — |
| `DIDDIGO_S2S_AUDIENCE` | no | `diddigo` |
| `DIDDIGO_E2E_PASSENGER_PHONE` | no | `+2250700000101` |
| `DIDDIGO_E2E_DRIVER_PHONE_PREFIX` | no | `+225070000012` |
| `DIDDIGO_E2E_DRIVER_COUNT` | no | `3` |
| `DIDDIGO_OTP_<digits>` | no | prompt if unset |
| pickup/near/far/remote/dropoff lat-lng, vehicle/comfort/payment, timeouts | no | Abidjan defaults in `config.py` |

If any **required** var is missing the suite skips with a message listing what's
absent — it never fails for configuration.

## Run

```bash
# nothing (default run excludes e2e):
pytest -q

# the whole dispatch E2E (you'll be prompted for OTP codes):
DIDDIGO_E2E_ADMIN_PHONE=+225... \
DIDDIGO_S2S_TOKEN_URL=https://auth-staging.diddifree.com/identity/v1/auth/service/token \
DIDDIGO_S2S_CLIENT_ID=... DIDDIGO_S2S_CLIENT_SECRET=... \
pytest -m e2e tests/e2e -s          # -s so the OTP prompt is visible

# one scenario:
pytest -m e2e tests/e2e/test_dispatch_staging.py::test_ranking_offers_the_nearest_driver_first -s
```

## Scenarios

| Test | Asserts | UC |
| --- | --- | --- |
| `test_happy_path_ride_lifecycle` | request → offered → accept → in_progress → completed → rating | pipeline |
| `test_density_gate_no_drivers_nearby` | remote pickup, nobody online → `no_driver_found` | UC-287 |
| `test_ranking_offers_the_nearest_driver_first` | `offer_wave_size=1` → nearest driver gets the sole offer | UC-283 |
| `test_priority_cap_far_driver_cannot_outrank_near` | boosted far driver still loses to the near one | UC-284 |
| `test_search_budget_gives_up_quickly` | 5s budget + no drivers → fast `no_driver_found` | UC-282 |
| `test_completed_ride_records_a_priority_ledger_event` | completed ride writes a ledger event | UC-108/285 |

The ranking/cap **math** is proven deterministically by the unit suites; these
tests prove the behaviour survives end-to-end through the real API, Redis, and
DiddiMap.
