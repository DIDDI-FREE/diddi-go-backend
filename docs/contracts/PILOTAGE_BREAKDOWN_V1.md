# DiddiGo Pilotage Breakdown v1

Date: 2026-10-03

## Route

```http
GET /internal/pilotage/breakdown?date=YYYY-MM-DD&dimension=<dimension>&metric=<metric>
Authorization: Bearer <DiddiFreeID service token>
X-Client-ID: <pilotage client id>
```

The service token must use `aud=diddigo`, `sub=service:pilotage`, and scope
`diddigo:ride-summary:read`.

## Supported matrix

| Dimension | rides_requested | rides_completed | completed_fare_total_xof |
| --- | --- | --- | --- |
| `hour` | yes | yes | yes |
| `payment_method` | yes | yes | yes |
| `service_type` | yes | yes | yes |
| `final_status` | yes | no | no |

`service_type` means the vehicle category selected for the ride. It is stored
as a snapshot on the ride so later vehicle edits cannot rewrite historical
reporting.

Unsupported dimensions, metrics, or combinations return `404
BREAKDOWN_NOT_AVAILABLE`.

## Response

```json
{
  "contract_version": "pilotage.breakdown.v1",
  "module": "diddigo",
  "date": "2026-10-03",
  "timezone": "Africa/Abidjan",
  "dimension": "payment_method",
  "metric": "rides_completed",
  "unit": "count",
  "total": 10,
  "items": [
    {"key": "cash", "label": "Espèces", "value": 6},
    {"key": "wave", "label": "Wave", "value": 4}
  ],
  "is_final": false,
  "calculated_at": "2026-10-03T12:00:00Z"
}
```

The sum of item values always equals `total`. Unknown stored keys remain
visible and use the raw key as their label. No ride or person identifier is
returned.

## Time semantics

- `rides_requested` uses `requested_at`.
- `rides_completed` uses `completed_at` and `status=completed`.
- `completed_fare_total_xof` uses `completed_at`, `status=completed`, and
  `currency=XOF`.
- Hour buckets are calculated in `Africa/Abidjan` and use keys `00` to `23`.

## Cache

Redis key:

```text
pilotage:breakdown:v1:{date}:{dimension}:{metric}
```

- current day TTL: 300 seconds;
- completed day TTL: 86400 seconds;
- a Redis failure falls back explicitly to PostgreSQL;
- SQL/provider failures are never cached as zero values.

## Errors

| Status | Code | Meaning |
| --- | --- | --- |
| 401 | `TOKEN_MISSING` | Missing service token. |
| 403 | `SERVICE_SCOPE_INVALID` | Invalid service identity or scope. |
| 404 | `BREAKDOWN_NOT_AVAILABLE` | Unsupported breakdown. |
| 422 | `INVALID_DATE` | Invalid calendar date or format. |
| 422 | `SUMMARY_DATE_IN_FUTURE` | Future date. |
| 422 | `SUMMARY_DATE_OUT_OF_RANGE` | Date outside the reporting window. |
| 500 | `BREAKDOWN_TOTAL_MISMATCH` | Aggregate integrity failure. |
| 503 | `RIDE_BREAKDOWN_UNAVAILABLE` | PostgreSQL aggregation unavailable. |
