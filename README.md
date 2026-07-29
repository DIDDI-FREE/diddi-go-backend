# DiddiGo — API backend

Backend VTC de DiddiFree : monolithe modulaire FastAPI (modules `auth`, `ride`,
`payment`), conçu pour être extrait en microservices sans réécriture.

**Stack :** Python 3.11 · FastAPI · PostgreSQL + PostGIS · Redis · WebSocket
**Références :** [`DiddiFree_Architecture_Modulaire_DiddiGo.md`](DiddiFree_Architecture_Modulaire_DiddiGo.md) ·
[`DiddiGo_Contrat_API.md`](DiddiGo_Contrat_API.md)

---

## Démarrage rapide

Prérequis : Python 3.11+, [`uv`](https://docs.astral.sh/uv/), Docker.

```bash
uv sync                       # installe les dépendances (runtime + dev)
docker compose up -d db redis # PostGIS sur le port 5433, Redis sur 6379
uv run alembic upgrade head   # crée les schémas auth / ride / payment
uv run uvicorn app_base.main:app --reload
```

Documentation interactive : <http://localhost:8000/docs> · Santé : `/health`

> Le port hôte de PostgreSQL est **5433** (et non 5432) pour ne pas entrer en
> conflit avec une instance PostgreSQL déjà présente sur la machine. À
> l'intérieur du réseau Docker, les conteneurs communiquent sur 5432.

### Docker local

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec app alembic upgrade head
```

### Portainer

```bash
docker stack deploy -c docker-compose.portainer.yml diddigo
```

Dans Portainer, renseigner les variables d'environnement directement dans
`Stack > Environment variables`. Aucun fichier `.env` n'est requis.
`docker-compose.portainer.yml` est la stack autonome pour le déploiement.
`docker-compose.yml` sert de base commune, et `docker-compose.local.yml`
apporte le confort du reload et des volumes de développement.

### Convention de branches

- `main` = production
- `stage` = intégration, QA, UI/UX, validation
- `feat/*` = branches de travail créées depuis `stage`

Voir [BRANCHING.md](BRANCHING.md).

---

## Tests

La suite s'exécute contre le vrai PostGIS et le vrai Redis (les colonnes
`GEOGRAPHY` et les commandes `GEO` ne sont pas simulables). Une base
`diddi_go_test` est recréée puis migrée au début de chaque session.

```bash
docker compose up -d db redis
uv run pytest                                    # 128 tests
uv run pytest tests/test_ride_state_machine.py   # domaine pur, sans base
uv run ruff check .
```

---

## Architecture

Monolithe modulaire : chaque module métier est une tranche verticale autonome
avec ses quatre couches. Le sens de dépendance est toujours
`presentation → application → domain ← infra` : le domaine ne dépend de rien,
et c'est `infra` qui implémente les interfaces qu'il déclare.

```
app_base/
├── core/                  config, moteur async SQLAlchemy, Redis, JWT, DI, lifespan
├── shared_kernel/         contrats inter-modules (RoutingProvider, PaymentProvider)
└── modules/
    ├── auth/              inscription, OTP, émission/validation JWT
    ├── ride/              cycle de vie course, tarification, WebSocket temps réel
    └── payment/           encaissement espèces (point d'extension DiddiPay)
```

**Règle de frontière :** un module ne requête jamais en SQL direct les tables
d'un autre module, même dans la même base. `payment` lit l'état d'une course
via `RideRepository`, jamais par un `JOIN` cross-schéma. C'est ce qui rendra
l'extraction en microservice mécanique.

### Services externes

| Service | Rôle | Comportement si indisponible |
|---|---|---|
| DiddiMap core | distance / durée / géocodage (profil `palh_vtc`) | l'estimation retombe sur un calcul haversine local — une course n'échoue jamais parce que la carte est hors ligne |
| Redis | position live des chauffeurs (`GEO`), présence TTL 30 s | requis |
| PostgreSQL + PostGIS | persistance, historique, recherche spatiale | requis |

---

## API

Toutes les routes sont préfixées par `/v1`. Format d'erreur uniforme :
`{"error": {"code": "...", "message": "...", "details": null}}`.

| Module | Endpoints |
|---|---|
| `auth` | `POST /auth/register` · `POST /auth/otp/request` · `POST /auth/otp/verify` · `POST /auth/refresh` · `GET /auth/me` |
| `ride` | `POST /rides/pricing/estimate` · `POST /rides` · `GET /rides` · `GET /rides/{id}` · `POST /rides/{id}/accept` · `POST /rides/{id}/decline` · `PATCH /rides/{id}/status` · `POST /rides/{id}/cancel` · `POST /rides/{id}/rating` |
| `driver` | `POST /drivers/profile` · `POST /drivers/vehicle` · `GET /drivers/me` · `POST /drivers/online` · `POST /drivers/offline` |
| `payment` | `POST /payments/{ride_id}/confirm-cash` · `GET /payments/{ride_id}` |
| WebSocket | `/v1/ws?token=<access_token>` — socket unique multiplexé par `event` |

Machine à états des courses (validée dans l'entité `Ride`, pas dans le service) :

```
requested → matched → driver_en_route → in_progress → completed
    ↓            ↓
no_driver_found  cancelled_by_passenger / cancelled_by_driver
```

Une transition non autorisée renvoie `409 INVALID_STATUS_TRANSITION` avec
`details.current_status` et `details.attempted_status`.

### Moteur de matching

Modèle **offre séquentielle** : la course est proposée au chauffeur
disponible le plus proche (rayon 5 km), qui dispose de 15 secondes pour
répondre. En cas de refus ou d'expiration, elle passe au suivant, jusqu'à
acceptation ou épuisement des candidats — la course devient alors
`no_driver_found`.

Parcours chauffeur, dans l'ordre :

```
POST /auth/register (role=driver) → OTP → POST /drivers/profile
  → POST /drivers/vehicle → POST /drivers/online {lat,lng}
  → (offre reçue par WebSocket) → POST /rides/{id}/accept | /decline
```

Deux points d'implémentation :

- **La fenêtre de 15 s est un TTL Redis, pas un minuteur.** La clé d'offre
  expire d'elle-même ; aucun job planifié à perdre si le processus redémarre.
- **L'attribution est un `SET NX`.** Deux chauffeurs qui acceptent au même
  instant ne peuvent pas gagner tous les deux : le second reçoit
  `409 RIDE_ALREADY_MATCHED`.

Un chauffeur en course quitte le vivier (il continue d'émettre sa position
pour le passager) et y revient à la fin de la course ou à son annulation.

## Git flow

La convention de branches du projet est documentée dans [BRANCHING.md](BRANCHING.md).

- `main` = production
- `stage` = intégration, QA, UI/UX, tests
- `feat/*` = branches de travail créées depuis `stage`

### OTP en développement

Aucun fournisseur SMS n'est branché : le code à six chiffres est **écrit dans
les logs applicatifs** au niveau `WARNING`. À remplacer par un vrai envoi SMS
avant toute mise en production.

---

## Migrations

Alembic est seul propriétaire du DDL (`Base.metadata.create_all` n'est jamais
appelé au démarrage).

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Les colonnes PostGIS sont gérées par `geoalchemy2.alembic_helpers`, importé
dans `alembic/env.py` ; le template de migration importe `geoalchemy2`
automatiquement.

---

## Écart assumé par rapport au document d'architecture

`ride.rides.status` est en `VARCHAR(30)` et non `VARCHAR(20)` : la plus longue
valeur du contrat, `cancelled_by_passenger`, fait 22 caractères — toute
annulation passager aurait échoué en base. Même correction sur
`ride_status_history.from_status` / `to_status`.

## Reste à faire (itérations suivantes)

- **Validation KYC réelle.** `APPROVE_DRIVERS_ON_CREATE` (dans
  `ride/application/driver_service.py`) active tout chauffeur dès qu'il
  soumet un permis, faute de back-office. À passer à `False` en même temps
  que l'endpoint d'approbation, sinon des chauffeurs non vérifiés reçoivent
  des courses.
- **Envoi réel des SMS d'OTP** — aujourd'hui le code part dans les logs.
- Tarification dynamique (`surge_multiplier`, plafond ×1.6) et endpoint admin.
- Endpoints d'administration (suspension de compte, gestion des véhicules).
- Relance automatique du matching à l'expiration d'une offre : la fenêtre se
  ferme toute seule, mais la course suivante n'est proposée qu'au prochain
  événement (refus, nouvelle tentative). Un worker de relance rendrait le
  passage au chauffeur suivant immédiat.
- Fan-out WebSocket multi-instance : `ConnectionManager` garde les sockets en
  mémoire, ce qui suppose un seul processus. À basculer sur Redis pub/sub le
  jour où l'app tourne en plusieurs répliques.
- `mobile_money` / `wallet` — le module `payment` reste cash-only.
- Bus d'événements inter-modules (`ride.completed` → futur DiddiSkill).
