# DiddiGo - API backend

Backend VTC de DiddiFree : monolithe modulaire FastAPI (modules `auth`, `ride`,
`payment`), conçu pour être extrait en microservices sans réécriture.

**Stack :** Python 3.11, FastAPI, PostgreSQL + PostGIS, Redis, WebSocket
**Références :**
- [DiddiFree_Architecture_Modulaire_DiddiGo.md](DiddiFree_Architecture_Modulaire_DiddiGo.md)
- [DiddiGo_Contrat_API.md](DiddiGo_Contrat_API.md)
- [DiddiGo_Contrat_API_v2.md](DiddiGo_Contrat_API_v2.md)
- [BRANCHING.md](BRANCHING.md)

---

## Démarrage local

Pré-requis : Python 3.11+, `uv`, Docker.

```bash
uv sync
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

Le service `init-db` applique les migrations Alembic une fois puis s'arrête
normalement avec un code `0`. L'application ne démarre qu'après sa réussite.

Application : <http://localhost:8000/docs>
Santé : <http://localhost:8000/health>

Repères locaux :
- Backend exposé sur `18000`
- PostgreSQL exposé sur `15432`
- Redis exposé sur `16379`

---

## Portainer

`docker-compose.portainer.yml` est la stack dédiée au déploiement Portainer.
Elle est pensée pour recevoir les valeurs dans `Stack > Environment variables`.
Aucun fichier `.env` n'est nécessaire.

Le démarrage Portainer passe par `docker/start.sh`:
- attente de la base PostgreSQL
- `alembic upgrade head`
- lancement de FastAPI

Dans Portainer staging/test :
- utiliser la stack `docker-compose.portainer.yml`
- renseigner au minimum `APP_ENV`, `JWT_SECRET`, `DIDDIMAP_BASE_URL`,
  `IDENTITY_BASE_URL` et `POSTGRES_PASSWORD`
- `POSTGRES_PASSWORD` n'est plus bloque au parsing Compose, ce qui permet a
  Portainer de faire `pull/config`. Il reste obligatoire pour que PostgreSQL
  demarre correctement.
- `DATABASE_URL` et `REDIS_URL` ont des valeurs internes par defaut pour la
  stack Portainer (`db:5432` et `redis:6379`). Ne les renseigner que si la base
  PostgreSQL ou Redis vivent hors de cette stack.
- `BACKEND_PORT`, `POSTGRES_PORT`, `REDIS_PORT`, `CORS_ORIGINS` et les autres
  variables restent surchargeables si besoin
- pour autoriser les frontends de test, renseigner `CORS_ORIGINS` avec une
  liste sÃ©parÃ©e par des virgules, par exemple
  `https://go-staging.diddifree.com,https://qa.diddifree.com`
- `localhost` et `127.0.0.1` sont autorisÃ©s sur tous les ports par dÃ©faut via
  `CORS_ORIGIN_REGEX`, ce qui couvre les testeurs en local
- pour consommer DiddiFreeID en staging, renseigner
  `IDENTITY_BASE_URL=https://auth-staging.diddifree.com`.
  `IDENTITY_JWKS_URL` et `IDENTITY_PROFILE_URL` sont dérivées automatiquement,
  mais restent disponibles si on doit les surcharger.
- conserver `main` pour la production et `stage` pour QA / UI / intégration

Garde-fous production :
- `docker-compose.portainer.yml` exige `APP_ENV`, `JWT_SECRET`,
  `DIDDIMAP_BASE_URL` et `IDENTITY_BASE_URL`.
- Renseigner toujours `POSTGRES_PASSWORD` avec une valeur forte. Sans cette
  variable, Compose peut etre charge par Portainer, mais PostgreSQL refusera de
  demarrer.
- `DATABASE_URL` et `REDIS_URL` ne sont plus obligatoires quand Portainer
  utilise les services internes `db` et `redis`.
- `docker/start.sh` refuse de demarrer en `APP_ENV=production` avec le
  `JWT_SECRET` d'exemple.
- `docker/start.sh` refuse de demarrer en production sans DiddiAuth
  (`IDENTITY_BASE_URL` ou `IDENTITY_JWKS_URL`) et sans DiddiMap
  (`DIDDIMAP_BASE_URL`).
- `APP_ENV=production` est lu par le backend comme environnement runtime.

Important :
- la stack Portainer ne repose pas sur `--reload`
- elle ne dépend pas du montage local du code
- elle suppose que l'image peut être construite par Portainer à partir du repo
- `depends_on` a été volontairement évité dans la stack Portainer, car il n'est
  pas fiable selon le mode de déploiement ; le backend vérifie lui-même sa
  connectivité au démarrage via le lifespan.
- Redis ne publie pas de port hôte dans Portainer, pour limiter les collisions
  sur un VPS déjà chargé.

---

## Git flow

- `main` = production
- `stage` = intégration, QA, UI/UX, validation
- `feat/*` = branches de travail créées depuis `stage`

---

## Tests

La suite s'exécute contre le vrai PostGIS et le vrai Redis.

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d db redis
uv run pytest
uv run ruff check .
```

---

## IntÃ©gration DiddiMap Core

DiddiGo ne charge pas DiddiMap Core comme librairie Python. Il le consomme comme
service HTTP via `DIDDIMAP_BASE_URL`.

Au dÃ©marrage, `app_base.core.lifespan` crÃ©e un `DiddiMapRoutingClient` avec
`settings.diddimap_base_url`, puis le monte dans `app.state.diddimap`. Les
services de course le rÃ©cupÃ¨rent ensuite via l'injection `get_diddimap`.

Configuration recommandÃ©e :
- staging / Portainer : `DIDDIMAP_BASE_URL=http://abidjanmaps-backend-staging.diddifree.com`
- local : garder la mÃªme URL staging, sauf si un DiddiMap local tourne vraiment
  sur la machine de dev
- local avec DiddiMap lancÃ© sur la machine hÃ´te :
  `DIDDIMAP_BASE_URL=http://localhost:4000`
- docker compose avec DiddiMap dans le mÃªme rÃ©seau : utiliser son vrai nom de
  service, par exemple `DIDDIMAP_BASE_URL=http://abidjanmaps-backend:4000`

Si DiddiMap Core est indisponible, DiddiGo retourne une erreur explicite
`DIDDIMAP_UNAVAILABLE`. Il n'y a pas de fallback silencieux par coordonnÃ©es :
DiddiMap reste le seul fournisseur des informations geographiques.

DiddiGo garde en revanche sa propre politique de pricing : il utilise la
distance/duree DiddiMap, puis applique `ride.pricing_rules` ou la formule
tarifaire DiddiGo par defaut si aucune regle n'est encore seedee.

---

## WebSocket

Le temps rÃ©el des courses passe par :

```text
wss://<host>/v1/ws?token=<access_token>
```

Un appel HTTP classique sur `/v1/ws` retourne `426 WEBSOCKET_UPGRADE_REQUIRED`.
Si les logs affichent `GET /v1/ws ... 404` ou `426`, le client/proxy n'a pas
envoyÃ© un vrai handshake WebSocket. Avec Nginx Proxy Manager, activer
`Websockets Support` sur le proxy host DiddiGo.

Phase test chauffeur :
- Android doit utiliser un foreground service pendant que le chauffeur est en
  ligne, avec une notification persistante du type "DiddiGo chauffeur actif".
- Le WebSocket doit rester ouvert quand l'app est vivante.
- Le front chauffeur doit envoyer `driver.location_push` toutes les 3 a 5
  secondes tant que le chauffeur est online.
- Le backend considere un chauffeur absent si sa presence Redis expire, meme
  si le dernier `POST /drivers/online` avait repondu `200`.

Version 2.0 prevue :
- ajouter l'enregistrement des devices chauffeur (`driver_devices`)
- stocker les push tokens FCM par utilisateur et plateforme
- envoyer une notification push en plus du WebSocket quand une course est
  proposee
- conserver le WebSocket comme canal temps reel rapide quand l'app est active
- utiliser la push notification comme canal de reveil/alerte quand l'app n'est
  pas fiable en arriere-plan

Routes push disponibles :
- `POST /v1/devices/register` enregistre le token FCM du device connecte.
- `POST /v1/devices/unregister` desactive le token au logout.
- Android et iOS passent par FCM cote backend. Sur iOS, Firebase relaie vers
  APNs en interne; DiddiGo ne stocke pas de token APNs brut.

Profils :
- DiddiFreeID garde le profil global (`display_name`, `avatar_url`, langue,
  contact d'urgence general).
- DiddiGo garde uniquement les extensions metier transport.
- `POST /v1/drivers/profile` cree le profil chauffeur et stocke le dossier KYC
  DiddiGo (`legal_name`, `birth_date`, adresse, `file_id` documents
  permis/CNI/selfie issus de DiddiFiles).
- Les champs URL KYC restent acceptes pour compatibilite legacy, mais les
  nouveaux clients doivent uploader les documents via DiddiFiles et envoyer les
  `*_document_file_id`.
- `GET /v1/drivers/me` retourne le profil chauffeur, le statut KYC et le
  vehicule actif si present.

---

## Logs et diagnostic

DiddiGo emet une ligne JSON par requete HTTP avec :
- `request_id` : identifiant unique de la requete, reutilisable avec
  `X-Request-ID` si le frontend/proxy l'envoie
- `hour` : bucket horaire UTC, utile pour compter les requetes par heure dans
  Portainer
- `client_ip` : source extraite de `X-Forwarded-For`, `X-Real-IP`, puis socket
- `user_id` et `user_role` : utilisateur authentifie quand le token est valide
- `path`, `query`, `status_code`, `duration_ms`, `user_agent`

Les erreurs API retournent aussi `details.request_id`, pour relier une erreur
vue par le frontend a la ligne correspondante dans les logs backend.

Les WebSockets loggent aussi :
- `ws_connected`
- `ws_auth_failed`
- `ws_ride_subscribe`
- `ws_driver_location_push`
- `ws_disconnected`

Logs matching utiles :
- `driver_online`
- `driver_position_updated`
- `driver_available_set`
- `driver_geo_search_raw`
- `driver_geo_candidate_rejected`
- `driver_geo_search_result`
- `matching_start`
- `matching_candidate_selected`
- `matching_candidate_rejected`
- `matching_offer_opened`
- `ws_send_new_request`
- `matching_no_driver_found`

---

## Architecture

Monolithe modulaire : chaque module métier est une tranche verticale autonome
avec ses quatre couches. Le sens de dépendance est toujours
`presentation -> application -> domain <- infra`.

```
app_base/
├── core/                  config, moteur async SQLAlchemy, Redis, JWT, DI, lifespan
├── shared_kernel/         contrats inter-modules (RoutingProvider, PaymentProvider)
└── modules/
    ├── auth/              inscription, OTP, émission/validation JWT
    ├── ride/              cycle de vie course, tarification, WebSocket temps réel
    └── payment/           encaissement espèces (point d'extension DiddiPay)
```

---

## Notes

- Les variables de configuration sont lues depuis l'environnement.
- Le fichier `.env` n'est pas requis par les stacks livrées ici.
- Si `IDENTITY_BASE_URL` ou `IDENTITY_JWKS_URL` est défini, DiddiGo vérifie les
  tokens DiddiFreeID en RS256 via JWKS. Sinon, le mode JWT local reste actif
  pour dev/tests.
- DiddiFreeID émet `role=user` pour un utilisateur standard ; DiddiGo le
  normalise en `passenger` pour ses règles de course. Les rôles `driver` et
  `admin` restent inchangés.
- Les ports externes sont configurables via `BACKEND_PORT`, `POSTGRES_PORT`
  et `REDIS_PORT`.
- Alembic reste propriétaire du DDL.
