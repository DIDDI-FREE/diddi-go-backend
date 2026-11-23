# DiddiRewards — DiddiGo

## Implémenté dans ce lot

DiddiGo possède un client S2S dédié pour le contrat explicite DiddiGo :

```text
POST /internal/v1/rewards/integrations/diddigo/benefits/quote
POST /internal/v1/rewards/integrations/diddigo/benefits/reserve
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
DIDDI_REWARDS_TIMEOUT_SECONDS=5
DIDDI_REWARDS_ENABLED=false
DIDDI_REWARDS_CAMPAIGN_ID=
DIDDI_REWARDS_EVENTS_REDIS_URL=
DIDDI_REWARDS_EVENTS_STREAM=diddigo.events.v1
```

Le token direct est prioritaire. À défaut, le client peut obtenir un token
S2S via DiddiFreeID avec `DIDDI_REWARDS_SERVICE_CLIENT_SECRET`.

## Reste à implémenter

1. Persister l'entitlement et la réservation sur le devis et la course.
2. Réserver après création de la course avec `ride_id` et idempotence.
3. Appliquer le montant final autorisé avant la création du PaymentIntent DiddiPay.
4. Confirmer après paiement avec `confirm` et publier les faits outbox.
5. Ajouter corrections de remboursement et rapprochement.

La création et la gestion des campagnes restent de la responsabilité de
DiddiAdmin. DiddiGo ne lit pas la base DiddiRewards.

## Événements

DiddiGo écrit d’abord les faits dans une outbox SQL transactionnelle, puis le
worker `rewards-events` les publie dans Redis Streams. Les événements sont
dédupliqués par `event_id` et réessayés avec un backoff borné.

L’équipe centrale doit fournir `DIDDI_REWARDS_EVENTS_REDIS_URL` si le stream
Rewards n’est pas sur le Redis applicatif DiddiGo.
