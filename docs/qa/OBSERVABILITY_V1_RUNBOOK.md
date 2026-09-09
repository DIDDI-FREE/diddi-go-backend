# Observabilite V1 - Runbook terrain

Date: 2026-09-08

Ce runbook explique comment utiliser les logs et `/metrics` pendant les tests
terrain DiddiGo.

## Objectif

Repondre vite aux questions suivantes :

- est-ce que les requetes arrivent au backend ?
- est-ce que les chauffeurs passent vraiment online ?
- pourquoi un chauffeur est bloque ?
- pourquoi une course ne trouve pas de chauffeur ?
- est-ce que les WebSockets et push envoient les offres ?
- est-ce que les erreurs DiddiMap/DiddiPay sont explicites ?

## Logs JSON

Dans Portainer, chercher :

```text
request_id
ride_id
driver_id
user_id
payment_intent_id
```

Evenements importants :

```text
http.request
driver.online
driver.online.blocked
ride.created
ride.matching.started
ride.matching.candidates_found
ride.matching.driver_filtered
ride.matching.driver_candidate_selected
ride.matching.offer_sent
ride.matching.no_driver_found
ws.connected
ws.driver_location.received
ws.ride_offer.sent
push.ride_offer.sent
push.ride_offer.failed
diddimap.request.failed
payment.prepare.created
payment.webhook.processed
```

## Metrics

Endpoint :

```http
GET /metrics
```

Compteurs :

```text
diddigo_http_requests_total
diddigo_http_request_duration_ms_count
diddigo_http_request_duration_ms_sum
diddigo_business_events_total
```

## Dashboard Grafana optionnel

Pour les tests terrain, DiddiGo livre aussi un overlay Compose optionnel :

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml -f docker-compose.observability.yml up --build
```

Acces local :

```text
Prometheus  http://localhost:19090
Grafana     http://localhost:13000
```

Le dashboard Grafana provisionne est :

```text
DiddiGo / DiddiGo Terrain
```

Il permet de suivre rapidement :

- trafic HTTP;
- erreurs `5xx`;
- matching et courses;
- blocages chauffeur;
- WebSocket et push;
- erreurs DiddiMap et paiement.

En Portainer, cet overlay doit rester optionnel. Ne pas exposer Grafana avec
`admin/admin`; definir `GRAFANA_ADMIN_PASSWORD` dans les variables de stack.

## Checklist pendant un test ride

1. Avant la course, verifier que le chauffeur passe online.

```text
event="driver.online"
```

2. Si online echoue, chercher :

```text
event="driver.online.blocked"
```

Ca doit donner un `reason` explicite :

```text
driver_not_verified
vehicle_not_verified
no_active_vehicle
partner_not_active:suspended
```

3. A la creation de course, chercher :

```text
event="ride.created"
event="ride.matching.started"
event="ride.matching.candidates_found"
```

4. Si aucun chauffeur ne recoit l'offre, regarder :

```text
event="ride.matching.driver_filtered"
event="ride.matching.no_driver_found"
```

5. Si le chauffeur est selectionne mais ne recoit rien :

```text
event="ws.ride_offer.sent"
event="push.ride_offer.sent"
event="push.ride_offer.failed"
```

## Requetes rapides

Voir les erreurs HTTP serveur :

```text
diddigo_http_requests_total{status_family="5xx"}
```

Voir les courses sans chauffeur :

```text
diddigo_business_events_total{event="ride.matching.no_driver_found"}
```

Voir les blocages online :

```text
diddigo_business_events_total{event="driver.online.blocked"}
```

Voir les erreurs push :

```text
diddigo_business_events_total{event="push.ride_offer.failed"}
```

Voir les positions WebSocket recues :

```text
diddigo_business_events_total{event="ws.driver_location.received"}
```

## Limites V1

- metrics en memoire par process;
- reset au redemarrage du conteneur;
- pas de traces distribuees OpenTelemetry;
- logs JSON restent la source de verite pour les IDs precis.

## Regle d'analyse

Toujours partir de `request_id` ou `ride_id` dans les logs, puis utiliser
`/metrics` pour voir si le probleme est isole ou frequent.
