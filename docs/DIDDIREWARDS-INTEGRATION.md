# DiddiRewards — DiddiGo

## Implémenté dans ce lot

DiddiGo possède un client S2S dédié pour le contrat explicite DiddiGo :

```text
POST /internal/v1/rewards/integrations/diddigo/benefits/quote
POST /internal/v1/rewards/integrations/diddigo/benefits/reserve
POST /internal/v1/rewards/integrations/diddigo/benefits/reservations/{reservation_id}/release
POST /internal/v1/rewards/integrations/diddigo/benefits/confirm
POST /internal/v1/rewards/integrations/diddigo/benefits/correct
POST /internal/v1/rewards/integrations/diddigo/reconciliation
```

Le endpoint de devis accepte désormais un `campaign_id` optionnel. Lorsque
`DIDDI_REWARDS_ENABLED=true`, DiddiGo demande une proposition Rewards et la
retourne dans le champ `rewards`, sans confirmer ni débiter l'avantage.

Le tarif DiddiGo original reste conservé tant que la règle de rémunération
du chauffeur et la persistance de la réservation ne sont pas finalisées.

## Variables

```ini
DIDDI_REWARDS_BASE_URL=
DIDDI_REWARDS_CLIENT_ID=diddigo
DIDDI_REWARDS_SERVICE_TOKEN=
DIDDI_REWARDS_SERVICE_CLIENT_SECRET=
DIDDI_REWARDS_SERVICE_SCOPES=diddirewards:benefits:quote diddirewards:benefits:reserve diddirewards:benefits:release diddirewards:benefits:consume diddirewards:benefits:correct diddirewards:reconcile
DIDDI_REWARDS_TIMEOUT_SECONDS=5
DIDDI_REWARDS_ENABLED=false
DIDDI_REWARDS_CAMPAIGN_ID=
DIDDI_REWARDS_EVENTS_REDIS_URL=
DIDDI_REWARDS_EVENTS_STREAM=diddigo.events.v1
```

Le token direct est prioritaire. À défaut, le client peut obtenir un token
S2S via DiddiFreeID avec `DIDDI_REWARDS_SERVICE_CLIENT_SECRET`.

Lorsque Rewards est activé, le démarrage vérifie que le client S2S peut
obtenir un jeton avec les scopes configurés. Un jeton statique ne permet pas
de vérifier ses claims au démarrage ; son provisioning reste à contrôler côté
DiddiFreeID.

## Contrat release proposé à DiddiRewards

Une réservation non consommée doit être libérée quand DiddiGo termine la
course par absence de chauffeur ou annulation :

```http
POST /internal/v1/rewards/integrations/diddigo/benefits/reservations/<reservation-id>/release
Authorization: Bearer <service-token>
X-Client-ID: diddigo
X-Request-ID: <request-id>
Idempotency-Key: diddigo:ride:<ride-id>:rewards-release:v1
Content-Type: application/json
```

```json
{
  "reason": "no_driver_found"
}
```

Depuis le ticket 016 (2026-11-25), DiddiGo appelle la route commune à tous les
services : identifiant de réservation dans l'URL, `reason` seul dans le corps,
scope `diddirewards:benefits:reserve`. Réponse `200` avec la réservation ;
une réservation déjà libérée ou expirée répond `200` avec `duplicate: true`.
L'ancienne route de commande `benefits/release` n'est plus appelée.

## Flux automatique après paiement

Après une transition de paiement `collected`, `succeeded`, `refunded`,
`partially_refunded` ou `cancelled`, DiddiGo appelle automatiquement
`POST /internal/v1/rewards/integrations/diddigo/reconciliation` lorsqu'une
consommation existe. L'appel utilise une clé d'idempotence stable par course.
Une indisponibilité Rewards ne bloque pas le paiement ; l'outbox Redis garde
le fait pour la reprise asynchrone.

La création et la gestion des campagnes restent de la responsabilité de
DiddiAdmin. DiddiGo ne lit pas la base DiddiRewards.

## Événements

DiddiGo écrit d’abord les faits dans une outbox SQL transactionnelle, puis le
worker `rewards-events` les publie dans Redis Streams. Les événements sont
dédupliqués par `event_id` et réessayés avec un backoff borné.

L’équipe centrale doit fournir `DIDDI_REWARDS_EVENTS_REDIS_URL` si le stream
Rewards n’est pas sur le Redis applicatif DiddiGo.
