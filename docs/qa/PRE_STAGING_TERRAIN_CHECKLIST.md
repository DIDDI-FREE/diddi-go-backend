# DiddiGo - Checklist pre-staging terrain

Date: 2026-09-09
Version cible: DiddiGo V1 terrain / production limitee prudente
Perimetre: DiddiGo uniquement

Objectif: verifier que le backend DiddiGo deploye en staging est coherent avec
les routes, variables d'environnement, tests Bruno, logs et dependances
externes attendues avant les tests chauffeurs/passagers.

## Branches et deploiement

- `dev`: branche actuellement consommee par Portainer staging.
- `stage`: branche QA / integration / validation.
- `main`: branche production.
- Le deploiement Portainer doit utiliser `docker-compose.portainer.yml`.
- La stack Portainer ne doit pas dependrer d'un fichier `.env` commite.
- Les secrets restent dans `Stack > Environment variables` Portainer.

## Variables Portainer minimum

Ces variables doivent etre visibles dans la configuration de la stack avant
deployer:

```env
JWT_SECRET=<secret-32-caracteres-minimum>
POSTGRES_PASSWORD=<mot-de-passe-postgres-stack>
CORS_ORIGINS=https://go-staging.diddifree.com
```

Pour le staging actuel, garder ou renseigner:

```env
APP_NAME=DiddiGo
APP_ENV=production
LOG_LEVEL=INFO
LOG_FORMAT=json
BACKEND_PORT=18000
POSTGRES_DB=diddi_go
POSTGRES_USER=postgres
IDENTITY_BASE_URL=https://auth-staging.diddifree.com
DIDDIMAP_BASE_URL=http://abidjanmaps-backend-staging.diddifree.com
DRIVER_MIN_BALANCE=0
```

Si DiddiMap exige un token service pour les traces GPS:

```env
DIDDIMAP_ACCESS_TOKEN=<service-token-diddimap-pour-diddigo>
```

Si les notifications push sont actives:

```env
PUSH_ENABLED=true
FCM_PROJECT_ID=<firebase-project-id>
FCM_SERVICE_ACCOUNT_JSON=<firebase-service-account-json-one-line>
```

Alternative FCM si le fichier est monte dans le conteneur:

```env
FCM_SERVICE_ACCOUNT_FILE=/run/secrets/firebase-service-account.json
```

Si DiddiPay est active:

```env
DIDDIPAY_BASE_URL=https://pay-api-staging.diddifree.com/payfund/v1
DIDDIPAY_CLIENT_ID=diddigo
DIDDIPAY_SERVICE_KEY=<service-key-diddipay-pour-diddigo>
DIDDIPAY_CALLBACK_SECRET=<secret-hmac-callback-diddipay>
DIDDIPAY_HTTP_TIMEOUT_SECONDS=15
DIDDIGO_PAYMENT_CALLBACK_URL=https://go-staging.diddifree.com/payments/return
PAYMENT_RECONCILIATION_ENABLED=true
PAYMENT_RECONCILIATION_INTERVAL_SECONDS=300
PAYMENT_RECONCILIATION_BATCH_SIZE=50
PAYMENT_RECONCILIATION_MIN_AGE_SECONDS=120
PAYMENT_RECONCILIATION_MAX_AGE_SECONDS=259200
```

Ne pas renseigner `DATABASE_URL` ni `REDIS_URL` si la stack utilise les services
internes `db` et `redis`. Dans ce cas, Compose les construit depuis
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` et le service Redis interne.

## Routes speciales a ne pas chercher sous /v1

Ces routes sont normales hors prefixe API:

```text
GET /health
GET /metrics
GET /payments/return
GET /wallet/return
POST /internal/webhooks/diddipay
```

Ces routes appartiennent a des services externes, pas a DiddiGo:

```text
/v1/files/*
```

DiddiGo stocke seulement les `file_id` DiddiFiles pour KYC/KYV/profil metier.

## Smoke tests apres relance Portainer

Tester rapidement:

```http
GET https://go-staging.diddifree.com/health
GET https://go-staging.diddifree.com/metrics
GET https://go-staging.diddifree.com/docs
GET https://go-staging.diddifree.com/v1/ws
GET https://go-staging.diddifree.com/payments/return
GET https://go-staging.diddifree.com/wallet/return
```

Attendus:

- `/health` retourne `200`.
- `/metrics` retourne du texte Prometheus.
- `/docs` charge Swagger.
- `/v1/ws` en HTTP simple retourne `426 WEBSOCKET_UPGRADE_REQUIRED`, pas `404`.
- `/payments/return` et `/wallet/return` ne retournent pas `404`.

## Bruno

Collection:

```text
E:\DIDDI AI\diddi-go\bruno\diddigo-api
```

Variables importantes:

```text
base_url
diddimap_base_url
auth_prefix
passenger_access_token
driver_access_token
admin_access_token
driver_profile_id
```

Suites minimales avant terrain:

```text
00-Health
09-DiddiMap-MVP
10-MVP-Field-Test
11-Partner-KYV
```

Si un token Bruno est marque `Runtime` et expire, il faut relancer le script qui
le genere ou recreer le token dans DiddiFreeID/DiddiGo. Le CLI Bruno ne peut pas
deviner une variable runtime creee uniquement dans la session GUI.

## Logs attendus dans Portainer

Les logs Docker/Portainer doivent contenir:

```text
http.request
request_id
client_ip
hour
path
status_code
duration_ms
```

Pour les tests terrain, rechercher aussi:

```text
ride.created
ride.matching.started
ride.matching.candidates_found
ride.matching.driver_filtered
ride.matching.offer_sent
ride.matching.no_driver_found
ride.accepted
ride.status_changed
ride.location_samples.saved
ride.actual_pricing.applied
driver.online
driver.online.blocked
payment.prepare.created
payment.webhook.processed
push.ride_offer.sent
push.ride_offer.failed
ws.driver_location.received
```

## Criteres de sortie terrain V1

La vague est stable seulement si:

- aucun `500` non documente sur les parcours principaux;
- DiddiMap places/pricing/traces repond via DiddiGo ou echoue explicitement;
- un chauffeur KYC/KYV valide peut passer online;
- un chauffeur non valide est bloque avec un code metier clair;
- une course proche notifie un chauffeur eligible;
- le chauffeur ne voit pas le prix avant acceptation/demarrage selon la regle produit actuelle;
- le passager peut creer, suivre, annuler ou terminer une course selon son etat;
- paiement cash fonctionne;
- topup DiddiPay/Wave retourne `next_action` quand le statut est `requires_action`;
- le callback DiddiPay et la reconciliation mettent a jour paiement/wallet;
- les liens de partage ride fonctionnent sans login;
- les logs permettent de retrouver `ride_id`, `driver_id`, `user_id` et `request_id`.

