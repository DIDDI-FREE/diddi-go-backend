# DiddiGo - API backend

Backend VTC de DiddiFree : monolithe modulaire FastAPI (modules `auth`, `ride`,
`payment`), conçu pour être extrait en microservices sans réécriture.

**Stack :** Python 3.11, FastAPI, PostgreSQL + PostGIS, Redis, WebSocket
**Références :**
- [DiddiFree_Architecture_Modulaire_DiddiGo.md](DiddiFree_Architecture_Modulaire_DiddiGo.md)
- [DiddiGo_Contrat_API.md](DiddiGo_Contrat_API.md)
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

Dans Portainer :
- utiliser la stack `docker-compose.portainer.yml`
- renseigner `APP_NAME`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`,
  `DIDDIMAP_BASE_URL`, `POSTGRES_PASSWORD`, `BACKEND_PORT`, `POSTGRES_PORT`,
  `REDIS_PORT`, `CORS_ORIGINS` et les autres variables si besoin
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

Si DiddiMap Core est indisponible, l'estimation de course ne casse pas :
DiddiGo retombe sur une estimation locale par coordonnÃ©es.

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
