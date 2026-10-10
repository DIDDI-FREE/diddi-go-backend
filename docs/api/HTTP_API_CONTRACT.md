# Contrat HTTP DiddiGo

**Source :** `app_base.main:app.openapi()`
**Généré le :** 2026-10-10
**Version applicative :** 0.1.0

La spécification complète, incluant les schémas de requête et de réponse, est dans [`openapi.json`](openapi.json). Ce fichier est généré depuis le code ; ne pas le modifier manuellement.
Le temps réel est décrit séparément dans le [`contrat WebSocket`](../realtime/WEBSOCKET_CONTRACT.md), car OpenAPI ne modélise pas ses messages.

## Surface

- **121 chemins**
- **135 opérations HTTP**

## admin-driver-wallet

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/admin/drivers/{driver_id}/wallet` | Admin Get Driver Wallet | 200, 422 | oui |
| GET | `/v1/admin/drivers/{driver_id}/wallet/ledger` | Admin Get Driver Ledger | 200, 422 | oui |
| GET | `/v1/admin/drivers/{driver_id}/wallet/withdrawals` | Admin List Driver Withdrawals | 200, 422 | oui |

## admin-observability

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/admin/logs/drivers/{driver_id}` | Search Driver Logs | 200, 422 | oui |
| GET | `/v1/admin/logs/rides/{ride_id}` | Search Ride Logs | 200, 422 | oui |

## admin-partners

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/admin/partners` | List Partners | 200, 422 | oui |
| POST | `/v1/admin/partners` | Create Partner | 201, 422 | oui |
| GET | `/v1/admin/partners/{partner_id}` | Get Partner | 200, 422 | oui |
| PATCH | `/v1/admin/partners/{partner_id}` | Update Partner | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/activate` | Activate Partner | 200, 422 | oui |
| GET | `/v1/admin/partners/{partner_id}/drivers` | List Drivers | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/drivers` | Affiliate Driver | 201, 422 | oui |
| DELETE | `/v1/admin/partners/{partner_id}/drivers/{driver_id}` | Unaffiliate Driver | 200, 422 | oui |
| PATCH | `/v1/admin/partners/{partner_id}/kyc` | Submit Partner Kyc | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/kyc/approve` | Approve Partner Kyc | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/kyc/reject` | Reject Partner Kyc | 200, 422 | oui |
| GET | `/v1/admin/partners/{partner_id}/members` | List Members | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/members` | Add Member | 201, 422 | oui |
| DELETE | `/v1/admin/partners/{partner_id}/members/{member_id}` | Deactivate Member | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/reject` | Reject Partner | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/suspend` | Suspend Partner | 200, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/vehicles` | Create Partner Vehicle | 201, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/assign` | Assign Vehicle | 201, 422 | oui |
| POST | `/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/unassign` | Unassign Vehicle | 200, 422 | oui |

## admin-payment

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| POST | `/v1/admin/payments/reconcile` | Reconcile Pending Payments | 200, 422 | oui |
| POST | `/v1/admin/payments/rides/{ride_id}/reconcile` | Reconcile Ride Payment | 200, 422 | oui |
| POST | `/v1/admin/payments/topups/{topup_id}/reconcile` | Reconcile Driver Topup | 200, 422 | oui |
| GET | `/v1/admin/payments/withdrawals/{withdrawal_id}` | Admin Get Driver Withdrawal | 200, 422 | oui |
| POST | `/v1/admin/payments/withdrawals/{withdrawal_id}/reconcile` | Reconcile Driver Withdrawal | 200, 422 | oui |

## admin-vehicles

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/admin/vehicles/kyv` | List Vehicle Kyv Queue | 200, 422 | oui |
| GET | `/v1/admin/vehicles/{vehicle_id}/kyv` | Get Vehicle Kyv Detail | 200, 422 | oui |

## auth

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/auth/me` | Me | 200 | oui |
| POST | `/v1/auth/otp/request` | Request Otp | 200, 422 | non/documenté |
| POST | `/v1/auth/otp/verify` | Verify Otp | 200, 422 | non/documenté |
| POST | `/v1/auth/refresh` | Refresh | 200, 422 | non/documenté |
| POST | `/v1/auth/register` | Register | 201, 422 | non/documenté |

## devices

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| POST | `/v1/devices/register` | Register Device | 200, 422 | oui |
| POST | `/v1/devices/unregister` | Unregister Device | 200, 422 | oui |

## driver

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/drivers/kyc` | List Driver Kyc Queue | 200, 422 | oui |
| POST | `/v1/drivers/kyc/resubmit` | Resubmit Kyc | 200, 422 | oui |
| GET | `/v1/drivers/me` | Get My Profile | 200 | oui |
| PATCH | `/v1/drivers/me/profile-photo` | Update My Profile Photo | 200, 422 | oui |
| PUT | `/v1/drivers/me/vehicle` | Update My Vehicle | 200, 422 | oui |
| POST | `/v1/drivers/offline` | Go Offline | 200 | oui |
| POST | `/v1/drivers/online` | Go Online | 200, 422 | oui |
| POST | `/v1/drivers/profile` | Create Profile | 201, 422 | oui |
| POST | `/v1/drivers/vehicle` | Register Vehicle | 201, 422 | oui |
| POST | `/v1/drivers/vehicles/{vehicle_id}/kyv/approve` | Approve Vehicle Kyv | 200, 422 | oui |
| POST | `/v1/drivers/vehicles/{vehicle_id}/kyv/reject` | Reject Vehicle Kyv | 200, 422 | oui |
| POST | `/v1/drivers/vehicles/{vehicle_id}/kyv/resubmit` | Resubmit Vehicle Kyv | 200, 422 | oui |
| GET | `/v1/drivers/{driver_id}/kyc` | Get Driver Kyc Detail | 200, 422 | oui |
| POST | `/v1/drivers/{driver_id}/kyc/approve` | Approve Driver Kyc | 200, 422 | oui |
| POST | `/v1/drivers/{driver_id}/kyc/reject` | Reject Driver Kyc | 200, 422 | oui |

## driver-wallet

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/drivers/me/wallet` | Get My Wallet | 200 | oui |
| GET | `/v1/drivers/me/wallet/ledger` | Get My Ledger | 200, 422 | oui |
| POST | `/v1/drivers/me/wallet/topups` | Create Driver Topup | 201, 422 | oui |
| GET | `/v1/drivers/me/wallet/topups/{topup_id}` | Get Driver Topup | 200, 422 | oui |
| GET | `/v1/drivers/me/wallet/withdrawals` | List Driver Withdrawals | 200, 422 | oui |
| POST | `/v1/drivers/me/wallet/withdrawals` | Request Driver Withdrawal | 201, 422 | oui |
| POST | `/v1/drivers/me/wallet/withdrawals/quote` | Quote Driver Withdrawal | 200, 422 | oui |
| GET | `/v1/drivers/me/wallet/withdrawals/{withdrawal_id}` | Get Driver Withdrawal | 200, 422 | oui |

## internal-admin-partners

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/internal/v1/admin/partners` | List Partners | 200, 422 | oui |
| POST | `/internal/v1/admin/partners` | Create Partner | 201, 422 | oui |
| GET | `/internal/v1/admin/partners/{partner_id}` | Get Partner | 200, 422 | oui |
| PATCH | `/internal/v1/admin/partners/{partner_id}` | Update Partner | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/activate` | Activate Partner | 200, 422 | oui |
| GET | `/internal/v1/admin/partners/{partner_id}/drivers` | List Drivers | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/drivers` | Affiliate Driver | 201, 422 | oui |
| DELETE | `/internal/v1/admin/partners/{partner_id}/drivers/{driver_id}` | Unaffiliate Driver | 200, 422 | oui |
| PATCH | `/internal/v1/admin/partners/{partner_id}/kyc` | Submit Partner Kyc | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/kyc/approve` | Approve Partner Kyc | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/kyc/reject` | Reject Partner Kyc | 200, 422 | oui |
| GET | `/internal/v1/admin/partners/{partner_id}/members` | List Members | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/members` | Add Member | 201, 422 | oui |
| DELETE | `/internal/v1/admin/partners/{partner_id}/members/{member_id}` | Deactivate Member | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/reject` | Reject Partner | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/suspend` | Suspend Partner | 200, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/vehicles` | Create Partner Vehicle | 201, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/assign` | Assign Vehicle | 201, 422 | oui |
| POST | `/internal/v1/admin/partners/{partner_id}/vehicles/{vehicle_id}/unassign` | Unassign Vehicle | 200, 422 | oui |

## internal-comms

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/internal/v1/comms/tasks/{task_type}/{task_id}` | Get Comms Task | 200, 422 | oui |

## internal-dispatch-admin

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/internal/v1/admin/dispatch/config` | Get Dispatch Config | 200, 422 | oui |
| PUT | `/internal/v1/admin/dispatch/config` | Put Dispatch Config | 200, 422 | oui |
| GET | `/internal/v1/admin/dispatch/drivers/{driver_id}/priority` | Get Driver Priority | 200, 422 | oui |
| POST | `/internal/v1/admin/dispatch/priority-boosts` | Grant Priority Boost | 201, 422 | oui |
| GET | `/internal/v1/admin/dispatch/priority-rules` | List Priority Rules | 200, 422 | oui |

## internal-driver-kyc

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/internal/v1/drivers/kyc` | List Driver Kyc Queue | 200, 422 | oui |
| GET | `/internal/v1/drivers/{driver_id}/kyc` | Get Driver Kyc Detail | 200, 422 | oui |
| POST | `/internal/v1/drivers/{driver_id}/kyc/approve` | Approve Driver Kyc | 200, 422 | oui |
| POST | `/internal/v1/drivers/{driver_id}/kyc/reject` | Reject Driver Kyc | 200, 422 | oui |

## internal-drivers

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| POST | `/internal/v1/drivers/provision` | Provision Driver Profile | 200, 422 | oui |
| PATCH | `/internal/v1/drivers/{driver_id}/profile-photo` | Update Driver Profile Photo | 200, 422 | oui |

## internal-ride-summary

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/internal/pilotage/breakdown` | Get Pilotage Breakdown | 200, 422 | oui |
| GET | `/internal/pilotage/daily-summary` | Get Pilotage Daily Summary | 200, 422 | oui |
| GET | `/internal/pilotage/finance-summary` | Get Pilotage Finance Summary | 200, 422 | oui |
| GET | `/internal/pilotage/health-summary` | Get Pilotage Health Summary | 200, 422 | oui |
| GET | `/internal/v1/ride-summary` | Get Ride Summary | 200, 422 | oui |

## internal-webhooks

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| POST | `/internal/webhooks/diddipay` | Diddipay Webhook | 204, 422 | non/documenté |

## me

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/me/capabilities` | Get My Capabilities | 200 | oui |
| GET | `/v1/me/emergency-contact` | Get My Emergency Contact | 200 | oui |
| PUT | `/v1/me/emergency-contact` | Upsert My Emergency Contact | 200, 422 | oui |
| DELETE | `/v1/me/emergency-contact` | Delete My Emergency Contact | 200 | oui |
| GET | `/v1/me/scores` | Get My Scores | 200 | oui |

## partners

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/partners/me` | Get My Partners | 200 | oui |

## payment

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/payments/{ride_id}` | Get Payment | 200, 422 | oui |
| POST | `/v1/payments/{ride_id}/confirm-cash` | Confirm Cash | 200, 422 | oui |
| POST | `/v1/payments/{ride_id}/prepare` | Prepare Payment | 200, 422 | oui |

## payment-return

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/payments/return` | Payment Browser Return | 200, 422 | non/documenté |
| GET | `/wallet/return` | Payment Browser Return | 200, 422 | non/documenté |

## places

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/places/search` | Search Places | 200, 422 | non/documenté |

## ride

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/rides` | List Rides | 200, 422 | oui |
| POST | `/v1/rides` | Create Ride | 201, 422 | oui |
| POST | `/v1/rides/pricing/estimate` | Estimate Pricing | 200, 422 | oui |
| GET | `/v1/rides/shared/{token}` | Get Shared Ride | 200, 422 | non/documenté |
| GET | `/v1/rides/{ride_id}` | Get Ride | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/accept` | Accept Ride | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/arrive` | Mark Driver Arrived | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/cancel` | Cancel Ride | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/decline` | Decline Ride | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/emergency` | Request Emergency | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/location-samples` | Add Location Samples | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/no-show` | Mark Passenger No Show | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/rating` | Rate Ride | 201, 422 | oui |
| GET | `/v1/rides/{ride_id}/score` | Get Ride Score | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/share-link` | Create Share Link | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/start` | Start Ride | 200, 422 | oui |
| PATCH | `/v1/rides/{ride_id}/status` | Update Status | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/stops` | Add Ride Stop | 201, 422 | oui |
| GET | `/v1/rides/{ride_id}/supplements` | List Ride Supplements | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/supplements` | Add Ride Supplement | 201, 422 | oui |
| POST | `/v1/rides/{ride_id}/waiting/start` | Start Waiting | 200, 422 | oui |
| POST | `/v1/rides/{ride_id}/waiting/stop` | Stop Waiting | 200, 422 | oui |

## ride-ws

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/v1/ws` | Websocket Upgrade Required | 426 | non/documenté |

## sans-tag

| Méthode | Chemin | Opération | Réponses déclarées | Sécurité OpenAPI |
|---|---|---|---|---|
| GET | `/health` | Health | 200 | non/documenté |
| GET | `/ready` | Readiness | 200 | non/documenté |
