# DiddiGo + DiddiMap MVP Use Case Test Matrix

This document defines the current MVP test scope. It separates automated Bruno
checks from human QA checks because some outcomes are technical, while others
are terrain/user-experience judgments.

## Scope

```text
DiddiMap = geographic provider: search, autocomplete, routing, route scoring,
trace analysis, route reports.

DiddiGo = VTC orchestrator: auth integration, driver KYC, vehicle, availability,
pricing policy, ride lifecycle, matching, notifications, share ride, emergency,
cash payment.
```

## Automated Developer Tests

| ID | System | Use case | Bruno request | Expected result |
|---|---|---|---|---|
| MAP-001 | DiddiMap | Service is reachable | 09-DiddiMap-MVP/01 | HTTP 200, status ok |
| MAP-002 | DiddiMap | Database is reachable | 09-DiddiMap-MVP/02 | HTTP 200, database available |
| MAP-003 | DiddiMap | Autocomplete with bias | 09-DiddiMap-MVP/03 | HTTP 200, frontend-friendly results |
| MAP-004 | DiddiMap | Search places and roads | 09-DiddiMap-MVP/04 | HTTP 200, list of candidates |
| MAP-005 | DiddiMap | Simple route | 09-DiddiMap-MVP/05 | HTTP 200, LineString, plausible distance |
| MAP-006 | DiddiMap | Alternatives/scoring | 09-DiddiMap-MVP/06 | HTTP 200, proposals with score |
| MAP-007 | DiddiMap | Road search | 09-DiddiMap-MVP/07 | HTTP 200, list |
| GO-000 | DiddiGo | Service is reachable | 00-Health/01 | HTTP 200, status ok |
| GO-001 | DiddiGo | DiddiGo place search via DiddiMap | 10-MVP-Field-Test/01 | HTTP 200, label/lat/lng |
| GO-002 | DiddiGo | Pricing via DiddiMap distance | 10-MVP-Field-Test/02 | HTTP 200, fare + commission fields |
| GO-003 | DiddiGo | Route-dependent ride creation | 10-MVP-Field-Test/03 | HTTP 201 or explicit business error |
| GO-004 | DiddiGo | Full happy path | 01..08 existing folders | ride completed + cash collected |

## Human QA Tests

| ID | Persona | Scenario | Expected user result |
|---|---|---|---|
| QA-001 | Passenger | Search pickup/dropoff around current location | Suggestions are useful and nearby |
| QA-002 | Passenger | Estimate route price | Price appears and feels plausible |
| QA-003 | Passenger | Create ride near online driver | Ride is created and driver is found |
| QA-004 | Driver | Receive offer while online | Offer arrives by WebSocket/FCM |
| QA-005 | Driver | Accept ride | Ride becomes matched |
| QA-006 | Driver | Refuse ride | Offer moves to another eligible driver or no_driver_found |
| QA-007 | Passenger | Track driver location | Marker moves without confusing freezes |
| QA-008 | Passenger | Share ride link | Public page opens without login and shows safe data |
| QA-009 | Passenger/Driver | Trigger emergency | Ride emergency status becomes open and backend log is visible |
| QA-010 | Driver | Complete ride and confirm cash | Payment becomes collected |

## Pass/Fail Rules

Critical blockers:

- DiddiMap health or DB health fails.
- DiddiGo cannot reach DiddiMap.
- Ride creation returns undocumented errors.
- KYC-approved driver cannot go online.
- Nearby eligible driver never receives a ride offer.
- Cash completion path cannot be completed.

Warnings:

- Search returns no result for a less common place.
- Route is technically valid but judged poor by drivers.
- FCM arrives late while WebSocket works.
- Share link works but UI needs refinement.

## Daily Field Test Note

```text
Date:
Tester:
Role:
Phone/device:
Scenario ID:
Expected:
Actual:
OK/KO:
Ride ID:
Driver ID:
Screenshot/log:
Comment:
```
