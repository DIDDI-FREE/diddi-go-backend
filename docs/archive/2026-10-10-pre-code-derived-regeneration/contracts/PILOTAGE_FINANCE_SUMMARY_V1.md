# DiddiGo Pilotage Finance Summary v1

## Endpoint

```http
GET /internal/pilotage/finance-summary?date=YYYY-MM-DD
```

Authentication uses the existing Pilotage service token:

```text
aud=diddigo
scope=diddigo:ride-summary:read
sub=service:pilotage
X-Client-ID=pilotage-staging-diddigo
```

The legacy alias `ride-summary:read` remains accepted by the service-token
verifier during migration.

## Business definitions

All ride metrics use rides completed during the selected Abidjan calendar day.
Only XOF records are included.

| Metric | Definition |
| --- | --- |
| `completed_fare_total_xof` | Sum of final fares for completed rides. |
| `digital_payments_xof` | Final fares whose method is `diddipay` or `wave`. |
| `cash_payments_xof` | Final fares whose method is `cash`. |
| `platform_commission_xof` | Commission recorded on completed rides. |
| `driver_earnings_xof` | Driver payout recorded on completed rides. |
| `driver_amount_paid_xof` | Driver earnings backed by a collected cash transaction or a succeeded digital transaction. |
| `driver_amount_outstanding_xof` | Driver earnings minus driver amount paid. |
| `refunds_xof` | Final fares of locally known fully refunded transactions. Partial refund amounts remain authoritative in DiddiPay. |

Top-up requested, pending and failed metrics use top-ups created during the
selected day. `pending` includes `pending`, `requires_action` and `processing`;
`failed` includes `failed` and `cancelled`. Succeeded metrics use `paid_at`, so
a request created on an earlier day and paid on the selected day is correctly
counted as a financial movement of the selected day.

Top-ups are never included in ride payment or fare metrics.

## Accounting controls

The endpoint fails explicitly instead of publishing inconsistent figures when:

```text
digital_payments_xof + cash_payments_xof
!= completed_fare_total_xof
```

```text
platform_commission_xof + driver_earnings_xof
!= completed_fare_total_xof
```

```text
driver_amount_paid_xof > driver_earnings_xof
```

DiddiGo exposes the business allocation of rides and driver balances. DiddiPay
remains authoritative for captures, exact partial refunds, processor fees,
settlements and payouts. Pilotage/Odoo must reconcile both sources rather than
substitute one for the other.
