# DiddiFree — Architecture applicative modulaire & Conception DiddiGo

**Stack retenue :** Python / FastAPI · PostgreSQL + PostGIS · Redis · WebSocket
**Périmètre actuel :** APP BASE (monolithe modulaire) hébergeant le module DiddiGo, un module Auth interne,
et un module Payment (cash) — conçus pour une extraction en microservices sans réécriture.
**Statut :** Document de design, à valider avant implémentation
**Historique :** v1 — schéma DiddiGo seul · v2 — contraintes de lancement (pas de socle central) ·
v3 — architecture modulaire verticale (5 couches) · v4 — clean architecture à 4 couches (ce document)

---

## 0. Contraintes de lancement — rappel

Le cahier des charges d'origine suppose un socle commun déjà en place (DiddiFree ID, DiddiPay). Au
lancement, seul **DiddiGo est live**, et **DiddiMap core** existe déjà comme brique de géocodage et de
calcul d'itinéraire/distance (moteur OSRM/GraphHopper/Valhalla — voir doc infrastructure technique).
DiddiGo consomme DiddiMap comme un **service externe** ; il ne réimplémente ni graphe routier ni
géocodage.

| Dépendance prévue | Statut réel | Décision |
|---|---|---|
| DiddiFree ID (identité) | Inexistant | Module `auth` interne à l'APP BASE (voir section 1) |
| DiddiPay (paiement) | Inexistant | Module `payment` interne, **cash uniquement** au lancement |
| DiddiMap core (géo/itinéraire) | **Existe, externe** | Client HTTP dans la couche `infra` du module `ride` |
| Position live / proximité chauffeur | Non couvert par DiddiMap | Redis `GEO`, interne au module `ride` |

---

## 1. Architecture applicative — organisation en modules verticaux

Principe : un **monolithe modulaire**, pas un enchevêtrement de couches horizontales partagées. Chaque
module métier (`auth`, `ride`, `payment`, et demain `catalog`, `wallet`, etc.) est une **tranche
verticale autonome** — il possède ses propres couches de haut en bas, et n'expose que ce qu'il choisit
d'exposer aux autres modules. C'est ce qui permet, le jour venu, d'extraire un module en microservice en
ne touchant qu'à sa couche `infra` (remplacer un appel de fonction par un appel HTTP), sans
toucher à sa logique métier.

```
app_base/
├── core/                          # transverse : config, DB engine, sécurité, exceptions communes
│   ├── config.py
│   ├── database.py
│   └── exceptions.py
│
├── shared_kernel/                 # types partagés entre modules (contrats, pas d'implémentation)
│   ├── contracts/                 # interfaces : AuthProvider, PaymentProvider, RoutingProvider
│   └── events/                    # bus d'événements internes (ride.completed, user.registered...)
│
├── modules/
│   │
│   ├── auth/                      # ── Module identité (remplace DiddiFree ID pour l'instant) ──
│   │   ├── presentation/          # routers FastAPI, schémas Pydantic (request/response)
│   │   ├── application/           # use cases : register(), login(), verify_otp(), get_current_user()
│   │   ├── domain/                # entités : User, Role — aucune dépendance à FastAPI ni SQLAlchemy
│   │   └── infra/                 # modèles SQLAlchemy, repositories, adaptateur SMS/OTP (Twilio, agrégateur local)
│   │
│   ├── ride/                      # ── Module DiddiGo ──
│   │   ├── presentation/          # routers REST + endpoints WebSocket
│   │   ├── application/           # use cases : request_ride(), match_driver(), update_status()...
│   │   ├── domain/                # entités : Ride, Driver, Vehicle, machine à états
│   │   └── infra/                 # modèles SQLAlchemy (schéma `ride`), repositories, client DiddiMap, adaptateur Redis GEO
│   │
│   └── payment/                   # ── Module paiement (cash au lancement) ──
│       ├── presentation/          # routers : confirmation d'encaissement
│       ├── application/           # use cases : create_transaction(), confirm_cash_collection()
│       ├── domain/                # entités : Transaction, statut d'encaissement
│       └── infra/                 # modèles SQLAlchemy (schéma `payment`) — point d'extension futur DiddiPay
│
└── main.py                        # assemble l'app FastAPI, monte les routers de chaque module
```

**Ce que chaque couche a le droit de faire :**

| Couche | Rôle | Dépend de |
|---|---|---|
| `presentation` (UI) | Reçoit la requête HTTP/WS, valide le format, appelle un use case | `application` |
| `application` | Orchestre la logique métier (use cases), transactionnel | `domain`, interfaces définies par `domain` |
| `domain` | Entités et règles métier pures — aucune dépendance technique | Rien |
| `infra` | Implémente les interfaces du `domain` : repositories/mapping DB **et** adaptateurs externes (API DiddiMap, SMS, futur DiddiPay) | `core.database`, rien du reste du module |

**Sens de dépendance (règle d'or de la clean architecture)** : `presentation → application → domain ← infra`.
Le `domain` ne dépend de rien ; c'est `infra` qui implémente les interfaces (ports) que `domain` ou
`application` définissent — jamais l'inverse. Concrètement : `domain` déclare une interface
`RideRepository` (méthodes abstraites), et c'est `infra` qui fournit `SqlAlchemyRideRepository`. Le
mapping DB et les clients API tiers vivent au même endroit parce qu'ils jouent le même rôle du point de
vue de l'architecture : ce sont tous les deux des détails techniques remplaçables, jamais consultés
directement par `application`.

**Règle de frontière inter-module — la plus importante :** un module ne fait **jamais** de requête SQL
directe sur les tables d'un autre module, même si elles vivent dans la même base de données. Il passe
systématiquement par la couche `application` de ce module (ex. `ride` appelle
`auth_module.get_user(user_id)`, jamais `SELECT * FROM auth.users`). C'est ce qui rend l'extraction future
en microservice mécanique : on remplace l'appel de fonction Python par un appel HTTP, l'appelant ne
change pas.

**Déclencheur d'extraction en microservice réel** : le jour où un deuxième module métier (au-delà de
`ride`) doit être déployé en production avec un rythme de release ou une charge différente — pas avant.
D'ici là, un seul processus FastAPI, une seule base PostgreSQL avec un schéma par module.

---

## 2. Vue d'ensemble runtime

| Composant (module) | Rôle | Techno |
|---|---|---|
| `auth` | Inscription, connexion, émission/validation de tokens JWT | FastAPI + PostgreSQL (`auth` schema) |
| `ride` | Cycle de vie course, matching, tarification, suivi GPS | FastAPI + PostgreSQL (`ride`) + Redis |
| `payment` | Enregistrement des transactions cash, futur point d'extension DiddiPay | FastAPI + PostgreSQL (`payment`) |
| DiddiMap core *(externe)* | Géocodage, calcul d'itinéraire/distance/ETA | Appelé en HTTP depuis `ride/infra` |

**Pourquoi PostgreSQL + PostGIS dans `ride`** : les courses ont une nature géospatiale forte (points de
départ/arrivée, recherche de chauffeurs à proximité). PostGIS apporte les types géométriques et les index
spatiaux (`GIST`). DiddiMap core gère le graphe routier et le calcul d'itinéraire — DiddiGo ne le
duplique pas — mais reste responsable de stocker *ses propres* points (pickup/dropoff) et de faire la
recherche de proximité chauffeur, ce que DiddiMap n'expose pas.

**Pourquoi Redis en complément** : la position d'un chauffeur change plusieurs fois par minute — pas une
donnée à écrire en base relationnelle à cette fréquence. Redis (`GEO`) stocke la position *courante* de
chaque chauffeur actif ; PostgreSQL garde l'historique pour l'audit, pas le flux temps réel.

---

## 3. Schéma de données — un schéma PostgreSQL par module

```sql
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS ride;
CREATE SCHEMA IF NOT EXISTS payment;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3.1 Module `auth`

```sql
CREATE TABLE auth.users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone           VARCHAR(20) NOT NULL UNIQUE,
    full_name       VARCHAR(120),
    password_hash   TEXT,                       -- NULL si auth par OTP uniquement
    role            VARCHAR(20) NOT NULL DEFAULT 'passenger',  -- passenger | driver | admin
    status          VARCHAR(20) NOT NULL DEFAULT 'active',     -- active | suspended
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auth.otp_codes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone       VARCHAR(20) NOT NULL,
    code_hash   TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_otp_phone ON auth.otp_codes(phone);
```

Conçu large dès le départ : `role` et le modèle `users` ne contiennent rien de spécifique à une course —
c'est directement réutilisable tel quel par un futur module DiddiShop, DiddiSanté, etc., sans migration.

### 3.2 Module `ride` (DiddiGo)

> `user_id` référence `auth.users(id)` — **référence logique**, résolue via l'API interne du module
> `auth` (`auth_module.get_user(id)`), jamais par un `JOIN` cross-schéma direct depuis le code du module
> `ride`. La contrainte `REFERENCES` en base est conservée pour l'intégrité des données (même base
> physique), mais aucune requête applicative ne la traverse directement.

```sql
CREATE TABLE ride.driver_profiles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL UNIQUE REFERENCES auth.users(id),
    license_number      VARCHAR(50) NOT NULL,
    license_verified_at TIMESTAMPTZ,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending_verification',
                        -- pending_verification | active | suspended | offline
    rating_avg          NUMERIC(3,2) DEFAULT 5.00,
    rating_count        INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ride.vehicles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id       UUID NOT NULL REFERENCES ride.driver_profiles(id) ON DELETE CASCADE,
    plate_number    VARCHAR(20) NOT NULL UNIQUE,
    make            VARCHAR(50),
    model           VARCHAR(50),
    color           VARCHAR(30),
    category        VARCHAR(20) NOT NULL DEFAULT 'standard',  -- standard | comfort | van
    active          BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ride.rides (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_user_id   UUID NOT NULL REFERENCES auth.users(id),
    driver_id           UUID REFERENCES ride.driver_profiles(id),
    vehicle_id          UUID REFERENCES ride.vehicles(id),

    status              VARCHAR(20) NOT NULL DEFAULT 'requested',
                        -- requested | matched | driver_en_route | in_progress
                        -- | completed | cancelled_by_passenger | cancelled_by_driver | no_driver_found

    pickup_location     GEOGRAPHY(POINT, 4326) NOT NULL,
    pickup_address      TEXT,
    dropoff_location    GEOGRAPHY(POINT, 4326) NOT NULL,
    dropoff_address     TEXT,

    scheduled_at        TIMESTAMPTZ,                 -- NULL = course immédiate
    requested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    matched_at          TIMESTAMPTZ,
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    cancelled_at        TIMESTAMPTZ,
    cancellation_reason TEXT,

    estimated_fare      NUMERIC(10,2),
    final_fare          NUMERIC(10,2),
    currency            CHAR(3) NOT NULL DEFAULT 'XOF',
    distance_km         NUMERIC(6,2),               -- renvoyé par DiddiMap core à la réservation
    duration_seconds    INTEGER,                     -- idem

    payment_transaction_id UUID,                     -- référence logique vers payment.transactions

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rides_passenger ON ride.rides(passenger_user_id);
CREATE INDEX idx_rides_driver ON ride.rides(driver_id);
CREATE INDEX idx_rides_status ON ride.rides(status);
CREATE INDEX idx_rides_pickup_geo ON ride.rides USING GIST(pickup_location);

CREATE TABLE ride.ride_status_history (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id     UUID NOT NULL REFERENCES ride.rides(id) ON DELETE CASCADE,
    from_status VARCHAR(20),
    to_status   VARCHAR(20) NOT NULL,
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata    JSONB
);

-- Échantillonnage du trajet réel (pas le flux live, qui reste dans Redis)
CREATE TABLE ride.ride_route_points (
    id          BIGSERIAL PRIMARY KEY,
    ride_id     UUID NOT NULL REFERENCES ride.rides(id) ON DELETE CASCADE,
    location    GEOGRAPHY(POINT, 4326) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_route_points_ride ON ride.ride_route_points(ride_id, recorded_at);

CREATE TABLE ride.pricing_rules (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city             VARCHAR(50) NOT NULL,
    vehicle_category VARCHAR(20) NOT NULL DEFAULT 'standard',
    base_fare        NUMERIC(10,2) NOT NULL,
    price_per_km     NUMERIC(10,2) NOT NULL,
    price_per_min    NUMERIC(10,2) NOT NULL,
    min_fare         NUMERIC(10,2) NOT NULL,
    surge_multiplier NUMERIC(3,2) NOT NULL DEFAULT 1.00,  -- borné éthiquement, cf. doc infra (plafond x1.6)
    active_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    active_to        TIMESTAMPTZ
);

CREATE TABLE ride.ride_ratings (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id    UUID NOT NULL REFERENCES ride.rides(id) ON DELETE CASCADE,
    rater_role VARCHAR(10) NOT NULL,   -- 'passenger' | 'driver'
    rating     SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(ride_id, rater_role)
);
```

### 3.3 Module `payment` (cash au lancement)

```sql
CREATE TABLE payment.transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ride_id         UUID NOT NULL,              -- référence logique vers ride.rides(id)
    amount          NUMERIC(10,2) NOT NULL,
    currency        CHAR(3) NOT NULL DEFAULT 'XOF',
    method          VARCHAR(20) NOT NULL DEFAULT 'cash',   -- cash aujourd'hui ; mobile_money/wallet plus tard
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending | collected | disputed
    collected_by    UUID,                       -- driver_profiles.id, encaissant confirmé
    collected_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_payment_ride ON payment.transactions(ride_id);
```

Le module `payment` est volontairement minimal : au lancement, il ne fait qu'enregistrer qu'une course a
été payée en espèces et par qui elle a été confirmée (le chauffeur, à la fin de la course). C'est le seul
module dont l'implémentation entière sera remplacée quand DiddiPay existera — l'interface
(`PaymentProvider.create_transaction()`, `.confirm()`) ne changera pas pour les appelants.

---

## 4. Design API (aperçu)

### REST — module `ride`

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/rides` | Créer une demande de course (déclenche le matching) |
| `GET` | `/rides/{ride_id}` | Détail d'une course |
| `GET` | `/rides?passenger_id=...` | Historique des courses d'un utilisateur |
| `PATCH` | `/rides/{ride_id}/status` | Transition de statut |
| `POST` | `/rides/{ride_id}/cancel` | Annulation |
| `POST` | `/rides/{ride_id}/rating` | Notation post-course |
| `POST` | `/pricing/estimate` | Estimation tarifaire (appelle DiddiMap pour la distance) |

### REST — module `auth`

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/auth/register` | Inscription (téléphone + nom) |
| `POST` | `/auth/otp/request` | Envoi d'un code OTP par SMS |
| `POST` | `/auth/otp/verify` | Vérification OTP → émission JWT |
| `GET` | `/auth/me` | Profil de l'utilisateur courant (à partir du token) |

### REST — module `payment`

| Méthode | Route | Description |
|---|---|---|
| `POST` | `/payments/{ride_id}/confirm-cash` | Le chauffeur confirme l'encaissement en espèces |
| `GET` | `/payments/{ride_id}` | Statut de paiement d'une course |

### WebSocket — module `ride`

| Canal | Direction | Contenu |
|---|---|---|
| `/ws/rides/{ride_id}` | Serveur → passager | Position du chauffeur, changements de statut |
| `/ws/drivers/{driver_id}` | Serveur → chauffeur | Nouvelles demandes de course |
| `/ws/drivers/{driver_id}/location` | Chauffeur → serveur | Push de position toutes les 3-5s |

### Machine à états des courses

```
requested → matched → driver_en_route → in_progress → completed
    ↓            ↓
no_driver_found  cancelled_by_passenger / cancelled_by_driver
```

---

## 5. Intégration DiddiMap core (externe)

Le module `ride/infra` porte un client HTTP unique vers DiddiMap core, derrière une interface
`RoutingProvider` définie dans `shared_kernel/contracts` :

```python
class RoutingProvider(Protocol):
    def estimate(self, origin: Point, destination: Point, profile: str) -> RouteEstimate:
        """Retourne distance_km, duration_seconds — via OSRM /route côté DiddiMap."""

    def geocode(self, query: str, bias: Point | None = None) -> list[GeocodeResult]:
        """Résolution d'adresse — via le PALH Geocoder de DiddiMap."""
```

DiddiGo n'appelle jamais OSRM/GraphHopper directement — toujours via l'API DiddiMap core, qui reste seule
propriétaire du graphe routier (« l'actif », selon le principe directeur de l'infra). Le profil `vtc`
(`palh_vtc.lua`) doit être précisé dans chaque appel `/route`.

**Ce que DiddiMap ne couvre pas et que `ride` garde en interne** : la recherche de chauffeurs disponibles
à proximité d'un point (matching temps réel). Ce n'est pas un problème de routage mais de position live
— domaine de Redis `GEO`, mis à jour à chaque push WebSocket d'un chauffeur.

---

## 6. Points d'extension future (socle central DiddiFree)

| Aujourd'hui | Demain (socle central prêt) | Ce qui change |
|---|---|---|
| Module `auth` interne, JWT maison | DiddiFree ID centralisé | `auth/infra` appelle le service central au lieu de vérifier en local ; `application` et `domain` inchangés |
| Module `payment`, cash uniquement | DiddiPay | Nouvelle implémentation de `PaymentProvider` (appel API DiddiPay) ; `ride` ne change pas, il continue d'appeler `payment_module.create_transaction()` |
| `driver_profiles` alimente son propre `rating_avg` | Diddi-Score cross-module (DiddiSkill) | Ajout d'un événement `ride.completed` publié sur le bus interne, consommé plus tard par DiddiSkill |

---

## 7. Prochaines étapes suggérées

1. Poser le squelette de dossiers (`app_base/modules/{auth,ride,payment}/...`) et le assembler dans `main.py`.
2. Implémenter le module `auth` en premier (dépendance de tous les autres endpoints).
3. Détailler le moteur de matching (`ride/application`, requête Redis `GEORADIUS`, appel DiddiMap pour la matrice de coûts si le volume le justifie).
4. Détailler la tarification dynamique (`surge_multiplier`, plafonné comme spécifié dans l'infra Map Core).
5. Écrire le contrat `PaymentProvider` avec les deux méthodes minimales (`create_transaction`, `confirm`) pour que le module `payment` soit remplaçable proprement.
