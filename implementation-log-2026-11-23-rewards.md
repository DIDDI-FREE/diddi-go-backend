# DiddiGo — journal d’implémentation DiddiRewards

Date : 2026-11-23  
Service : `diddigo`  
Branche : `codex/diddigo-stage-onboarding`

## Objectif

Intégrer les réductions et avantages DiddiRewards dans le parcours DiddiGo,
en utilisant le contrat explicite :

- `POST /internal/v1/rewards/integrations/diddigo/benefits/quote`
- `POST /internal/v1/rewards/integrations/diddigo/benefits/reserve`
- `POST /internal/v1/rewards/integrations/diddigo/benefits/confirm`
- `POST /internal/v1/rewards/integrations/diddigo/benefits/correct`
- `POST /internal/v1/rewards/integrations/diddigo/reconciliation`

Référence vérifiée : `http://diddi-rewards-staging.diddifree.com/openapi.json`.

## Plan d’implémentation

| Lot | Contenu | État |
|---|---|---|
| 1 | Client S2S, configuration, devis Rewards | Terminé |
| 2 | Persistance de l’entitlement et réservation liée à `ride_id` | Terminé dans ce lot |
| 3 | Calcul du montant client réduit et cohérence DiddiPay | Terminé dans ce lot |
| 4 | Confirmation Rewards après paiement confirmé | Terminé dans ce lot |
| 5 | Outbox `ride.payment_confirmed`, `ride.refunded`, `ride.cancelled` | À faire |
| 6 | Corrections de remboursement et rapprochement | Correction HTTP implémentée, rapprochement à faire |
| 7 | Tests staging et validation DiddiRewards/Loki/Tempo | À faire |

## Journal des changements

### 2026-11-23 — Lot 1

- Ajout de `DiddiRewardsClient`.
- Authentification par token S2S direct ou client credentials DiddiFreeID.
- Ajout des variables `DIDDI_REWARDS_*` dans les settings et Compose.
- Ajout de l’appel `benefits/quote` avec `service_code=go`.
- Ajout de `campaign_id` optionnel au endpoint de devis DiddiGo.
- Ajout de tests du contrat HTTP et de l’idempotence de réservation.
- Commit : `c543a9f feat(rewards): add DiddiGo quote adapter`.

### 2026-11-23 — Lot 2

- Ajout du contexte Rewards dans `RideQuote` et `Ride`.
- Migration Alembic `b2c3d4e5f6a7` pour les colonnes Rewards.
- Persistance de l’entitlement, de la version de campagne et du montant proposé.
- Réservation après création de la course avec :
  `ride_id`, `Idempotency-Key` et `X-Request-ID`.
- Statut local de l’avantage : `quoted`, puis `reserved`.

### 2026-11-23 — Lot 3

- `client_paid_minor` est calculé comme `final_fare - rewards_discount_amount`.
- Le montant brut reste disponible dans `ride.final_fare`.
- Le paiement cash vérifie le montant net attendu.
- Le PaymentIntent DiddiPay reçoit le montant net client.
- Après `collected` ou `succeeded`, DiddiGo appelle `benefits/confirm`.
- La confirmation est idempotente et le statut local passe à `confirmed`.
- Une panne Rewards ne bloque pas le paiement : la confirmation est journalisée
  comme différée et reste à reprendre par le worker de rapprochement.

### 2026-11-23 — Lot 4

- Ajout des appels Rewards `correct` et `reconciliation` dans le client S2S.
- Persistance de `consumption_id` sur la course.
- Après un remboursement DiddiPay, DiddiGo tente une correction append-only.
- Une panne Rewards laisse le remboursement local intact et marque la correction
  comme différée.
- Migration ajoutée : `c3d4e5f6a7b8`.

### 2026-11-23 — Lot 5

- Ajout d’une reprise administrative idempotente :
  `POST /v1/admin/payments/rides/{ride_id}/reconcile-rewards`.
- Cette route rejoue une confirmation ou une correction différée puis appelle
  le rapprochement Rewards si une consommation existe.
- L’outbox Redis/Streams reste à brancher pour publier les événements métier
  durables (`ride.payment_confirmed`, `ride.refunded`, `ride.cancelled`).

## Décision de sécurité financière

Le tarif DiddiGo original n’est pas encore remplacé par le montant réduit dans
DiddiPay. La raison est volontaire : le contrat fournit séparément
`client_paid_minor`, `driver_payout_minor` et `diddi_contribution_minor`.
La règle métier de rémunération du chauffeur doit être confirmée avant de
modifier le PaymentIntent.

Ainsi, aucun paiement ne peut actuellement être confirmé à tort comme
réduction Rewards consommée.

## Variables attendues par l’équipe centrale

```ini
DIDDI_REWARDS_BASE_URL=http://diddi-rewards-staging.diddifree.com
DIDDI_REWARDS_CLIENT_ID=diddigo-staging
DIDDI_REWARDS_SERVICE_TOKEN=
DIDDI_REWARDS_SERVICE_CLIENT_SECRET=
DIDDI_REWARDS_TIMEOUT_SECONDS=5
DIDDI_REWARDS_ENABLED=false
DIDDI_REWARDS_CAMPAIGN_ID=
```

Les secrets ne doivent pas être commités. En staging, l’équipe doit fournir
le token S2S ou le secret client par le canal sécurisé habituel.

## Validation locale

- Ruff : réussi.
- Import de l’application : réussi.
- Tests ciblés : `19 passed`.
- Test du client Rewards : `2 passed`.
- Aucun accès direct à la base DiddiRewards.

## Points restant à valider en staging

- Le token et le scope autorisent bien les routes DiddiGo.
- Le `campaign_id` est actif et compatible avec `service_code=go`.
- La réservation est visible côté DiddiRewards.
- Le montant final DiddiPay correspondra à la règle financière validée.
- Les confirmations, corrections et rapprochements seront reçus et dédupliqués.
