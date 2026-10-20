# SCRUM-510 - Fiabilite de la projection chauffeur DiddiFreeID

## Regle

DiddiGo reste la source de verite du chauffeur. DiddiFreeID recoit uniquement
la projection globale `diddigo/driver`; DiddiFree Pro l'affiche.

## Fonctionnement

1. Une transition KYC, KYV, online ou offline enregistre un evenement dans
   `ride.driver_capability_projection_events`.
2. La version monotone et le dernier evenement sont conserves dans
   `ride.driver_capability_projection_states`.
3. La transaction metier valide l'evenement avant toute livraison distante.
4. Le worker envoie l'evenement a DiddiFreeID avec son `event_id` et sa
   `projection_version` persistants.
5. Un echec temporaire est rejoue avec les memes identifiants et un backoff.
6. Un `409` est classe `conflict` et n'est pas rejoue aveuglement.
7. Apres redemarrage, les lignes `pending` et `retry` restent livrables.
8. La reconciliation reconstruit les projections manquantes depuis les profils,
   vehicules et marqueurs Redis, puis rafraichit les projections avant 60 s.

## Configuration

```ini
CAPABILITY_PROJECTION_ENABLED=true
CAPABILITY_PROJECTION_DELIVERY_INTERVAL_SECONDS=5
CAPABILITY_PROJECTION_RECONCILIATION_INTERVAL_SECONDS=30
CAPABILITY_PROJECTION_REFRESH_SECONDS=45
CAPABILITY_PROJECTION_BATCH_SIZE=100
CAPABILITY_PROJECTION_RETRY_BASE_SECONDS=5
CAPABILITY_PROJECTION_RETRY_MAX_SECONDS=300
```

Les secrets restent `IDENTITY_SERVICE_CLIENT_ID` et
`IDENTITY_SERVICE_CLIENT_SECRET`; aucun nouveau secret n'est introduit.

## Observabilite

Evenements JSON principaux :

- `identity.capability.projection.enqueued`;
- `identity.capability.projection.delivered`;
- `identity.capability.projection.delivery_failed`;
- `identity.capability.projection.reconciled`;
- `identity.capability.projection.worker_failed`.

Metriques :

- `diddigo_capability_projection_events_total{result=...}`;
- `diddigo_capability_projection_backlog{status=...}`;
- `diddigo_capability_projection_last_success_age_seconds`;
- `diddigo_capability_projection_reconciliations_total{result=...}`.

Une alerte doit etre levee lorsqu'un backlog `retry` augmente durablement,
qu'un conflit apparait ou que l'age de la derniere reussite depasse la fenetre
de fraicheur convenue.
