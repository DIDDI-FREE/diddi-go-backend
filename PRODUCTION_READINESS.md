# DiddiGo - Production readiness

Ce document liste les points obligatoires avant passage en production.

## Variables Portainer obligatoires

```env
APP_ENV=production
JWT_SECRET=<random-32+-characters-secret>
POSTGRES_PASSWORD=<strong-password>
IDENTITY_BASE_URL=https://auth.diddifree.com
DIDDIMAP_BASE_URL=http://abidjanmaps-backend-staging.diddifree.com
CORS_ORIGINS=https://go.diddifree.com
PUSH_ENABLED=true
FCM_PROJECT_ID=<firebase-project-id>
FCM_SERVICE_ACCOUNT_JSON=<firebase-service-account-json>
```

`DATABASE_URL` et `REDIS_URL` sont optionnels quand Portainer utilise les
services internes `db` et `redis`. Les renseigner uniquement si PostgreSQL ou
Redis vivent hors de cette stack.

`POSTGRES_PASSWORD` ne bloque pas le parsing Compose afin que Portainer puisse
charger la stack, mais il reste obligatoire au runtime. Sans valeur forte,
PostgreSQL refusera de demarrer.

`IDENTITY_JWKS_URL` et `IDENTITY_PROFILE_URL` peuvent rester vides si
`IDENTITY_BASE_URL` est renseigne.

## Temps reel chauffeur

Phase test :

```text
Android foreground service
+ WebSocket
+ driver.location_push toutes les 3 a 5 secondes
```

Version 2.0 :

```text
WebSocket = canal rapide quand l'app est active
FCM = canal push quand l'app est suspendue/fermee
```

Implementation actuelle :

```text
Android = FCM implemente
iOS = FCM implemente cote backend; Firebase relaie ensuite vers APNs
DiddiGo ne configure pas APNs directement
```

## Logs Portainer a verifier

Apres redeploiement, chercher :

```text
http.request
driver_online
driver_position_updated
driver_available_set
matching_start
driver_geo_search_raw
matching_candidate_selected
matching_candidate_rejected
matching_offer_opened
ws_send_new_request
matching_no_driver_found
```

## Garde-fous backend

- Production refuse le `JWT_SECRET` d'exemple.
- Production refuse de demarrer sans DiddiAuth configure.
- Production refuse de demarrer sans DiddiMap configure.
- DiddiGo ne fait pas de fallback geographique silencieux.
- DiddiGo garde sa politique de pricing, mais la distance/duree viennent de
  DiddiMap.
