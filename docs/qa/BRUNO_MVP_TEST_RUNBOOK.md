# Bruno MVP Test Runbook

Use this runbook to test the current DiddiGo + DiddiMap MVP with Bruno and a
small human QA team.

## 1. Select Environment

In Bruno, open:

```text
E:\DIDDI AI\diddi-go\bruno\diddigo-api
```

Use:

```text
local   = local DiddiGo + optional local/mock DiddiMap
staging = go-staging + abidjanmaps-backend-staging
```

Important variables:

```text
base_url             DiddiGo API base with /v1
diddimap_base_url    DiddiMap API base with /api/v1
auth_prefix          DiddiFreeID or local auth prefix
passenger_access_token
driver_access_token
admin_access_token
```

## 2. Developer Smoke Tests

Run DiddiMap first:

```text
09-DiddiMap-MVP/01 DiddiMap Health
09-DiddiMap-MVP/02 DiddiMap DB Health
09-DiddiMap-MVP/03 Autocomplete Plateau
09-DiddiMap-MVP/04 Geocoding Search Anador
09-DiddiMap-MVP/05 Route Yopougon To Plateau
09-DiddiMap-MVP/06 Route Proposals Detail
09-DiddiMap-MVP/07 Roads Search
```

Then run DiddiGo integration:

```text
10-MVP-Field-Test/01 DiddiGo Places Through DiddiMap
10-MVP-Field-Test/02 DiddiGo Pricing Yopougon Plateau
10-MVP-Field-Test/03 DiddiGo Route Dependent Ride Create
```

## 3. Full DiddiGo Happy Path

Follow the existing collection order:

```text
00-Health
01-Auth
02-Driver-Onboarding
03-Admin-KYC
04-Driver-Availability
05-Places-Pricing
06-Ride-Lifecycle
07-Payment
08-Devices
```

Critical timing note:

```text
Run 04-Driver-Availability/01 Go Online less than 30 seconds before
06-Ride-Lifecycle/01 Create Ride.
```

## 4. Human QA Recording

Record every manual scenario in:

```text
docs\qa\mvp_field_test_results.csv
```

Recommended statuses:

```text
Not Run
Pass
Fail
Blocked
Needs Review
```

Recommended severities:

```text
P0 = blocks MVP test
P1 = major user flow broken
P2 = workaround exists
P3 = polish / observation
```

## 5. Wave 1 Stabilization Exit Criteria

Wave 1 is stable enough only if:

```text
DiddiMap health/db-health pass
DiddiMap route tests pass for common Abidjan trips
DiddiGo places/pricing can reach DiddiMap
approved drivers can go online
nearby eligible driver receives offer
passenger and driver can complete one cash ride
share link works
emergency event is recorded
no undocumented 500 appears during the core flow
```
