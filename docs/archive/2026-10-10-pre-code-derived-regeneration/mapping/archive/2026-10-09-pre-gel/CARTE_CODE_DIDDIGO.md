# Carte du code DiddiGo — état réel

Date de relevé : 9 octobre 2026. Branche : `feat/pilotage-finance-summary-v1`.

Ce document décrit **ce que le code fait**, sans le comparer à une cible produit et sans jugement de
conformité. Chaque affirmation porte un `fichier:ligne` vérifiable. La carte de la cible produit est dans
`CARTE_CIBLE_MVP_DIDDIGO.md` ; la confrontation des deux est dans `ECARTS_CODE_CIBLE_DIDDIGO.md`.

Méthode : lecture du dépôt `diddi-go` uniquement, plus la surface OpenAPI générée par
`app_base.main:app.openapi()`. Aucune valeur n'est reportée depuis un document produit.

---

## 1. Surface API

124 routes exposées, réparties en trois surfaces d'authentification distinctes.

| Surface | Nombre | Authentification |
| --- | --- | --- |
| `/v1/*` | 84 | JWT humain DiddiFreeID (`get_current_user`, `app_base/core/auth_deps.py`) |
| `/internal/*` | 36 | token S2S scopé, ou secret de callback pour le webhook |
| `/health`, `/ready`, `/payments/return`, `/wallet/return` | 4 | non authentifiées |

Montage des routeurs : `app_base/main.py:57-78`. Les routeurs `/internal` sont montés **sans préfixe**,
le chemin complet est porté par le routeur lui-même.

### 1.1 Parcours course (passager et chauffeur)

| Route | Service |
| --- | --- |
| `POST /v1/rides/pricing/estimate` | `RideService.estimate_pricing` |
| `POST /v1/rides` | `RideService.request_ride` |
| `GET /v1/rides`, `GET /v1/rides/{id}` | `RideService.list_rides`, `get_ride` |
| `POST /v1/rides/{id}/accept`, `/decline` | `MatchingService.accept`, `decline` |
| `PATCH /v1/rides/{id}/status` | `RideService.update_status` |
| `POST /v1/rides/{id}/waiting/start`, `/stop` | `RideService.start_waiting`, `stop_waiting` |
| `POST /v1/rides/{id}/stops`, `/supplements` | `RideService.add_stop`, `add_supplement` |
| `POST /v1/rides/{id}/cancel` | `RideService.cancel` |
| `POST /v1/rides/{id}/location-samples` | `RideService.add_location_samples` |
| `POST /v1/rides/{id}/rating` | `RideService.rate` |
| `POST /v1/rides/{id}/emergency` | `RideService.request_emergency` |
| `POST /v1/rides/{id}/share-link`, `GET /v1/rides/shared/{token}` | `create_share_link`, `get_shared_ride` |
| `GET /v1/rides/{id}/score`, `GET /v1/me/scores` | `ScoringService` |
| `GET /v1/ws` | WebSocket temps réel (`ride/presentation/websocket.py`) |

Il n'existe **pas** de route de messagerie en course (`/rides/{id}/messages` absent de la surface
OpenAPI) ni de route de course programmée.

### 1.2 Parcours professionnel

`POST /v1/drivers/profile`, `/vehicle`, `PUT /v1/drivers/me/vehicle`, `GET /v1/drivers/me`,
`POST /v1/drivers/online` et `/offline`, `PATCH /v1/drivers/me/profile-photo`,
`POST /v1/drivers/kyc/resubmit`, `POST /v1/drivers/vehicles/{id}/kyv/{approve,reject,resubmit}`,
`GET /v1/me/capabilities`. Revue côté opérateur : `GET /v1/drivers/kyc`, `GET /v1/admin/vehicles/kyv` et
leurs variantes de détail et de décision.

### 1.3 Parcours financier

`POST /v1/payments/{ride_id}/prepare`, `POST /v1/payments/{ride_id}/confirm-cash`,
`GET /v1/payments/{ride_id}`, `POST /v1/drivers/me/wallet/topups`,
`GET /v1/drivers/me/wallet`, `/ledger`, `/topups/{id}`. Côté opérateur :
`GET /v1/admin/drivers/{id}/wallet` et `/ledger`, `POST /v1/admin/payments/reconcile` et ses variantes
par course et par recharge. Entrée DiddiPay : `POST /internal/webhooks/diddipay`.

Aucune route de retrait (`withdrawal`) n'existe dans cette surface.

### 1.4 Surfaces internes

Pilotage — 5 routes, toutes derrière la même garde
(`app_base/modules/ride/presentation/summary_router.py:16-20`) :

```
require_identity_service_token(
    audience=DIDDIGO_AUDIENCE, required_scope=RIDE_SUMMARY_READ, expected_subject="service:pilotage")
```

`GET /internal/v1/ride-summary` (legacy), `GET /internal/pilotage/daily-summary`,
`/finance-summary`, `/breakdown`, `/health-summary`.

Backoffice — `/internal/v1/drivers/*` (provisioning, KYC), `/internal/v1/admin/partners/*` (15 routes),
`/internal/v1/admin/dispatch/*` (configuration, règles de priorité, boosts).

---

## 2. Machine à états de la course

`app_base/modules/ride/domain/entities.py:19-66`. Neuf statuts, transitions déclarées explicitement dans
`ALLOWED_TRANSITIONS` ; toute transition hors table lève `InvalidStatusTransition`, rendue
`409 INVALID_STATUS_TRANSITION` à la frontière HTTP (`entities.py:120-121`).

```
requested ──► matched ──► driver_en_route ──► in_progress ──► completed
    │                                              ▲   │
    │                                              └───┤ waiting
    │                                                  │
    ├──► no_driver_found (terminal)                    ▼
    └──► cancelled_by_passenger / cancelled_by_driver (terminal)
```

Points structurels relevés :

- **Aucun statut d'arrivée** du chauffeur au point de prise en charge. `driver_en_route` passe
  directement à `in_progress`.
- `waiting` n'est atteignable que **depuis `in_progress`** (`entities.py:49-54`). C'est donc une attente
  **en cours de course**, pas une attente de prise en charge.
- `completed`, `no_driver_found` et les deux annulations sont terminaux — ensembles vides
  (`entities.py:62-66`). Le test `test_ride_flow.py` couvre explicitement le cas « annuler un
  `no_driver_found` » qui levait auparavant hors du domaine.
- Sortie de `waiting` : `PATCH /status` vers `in_progress` est **refusée**
  (`409 WAITING_STOP_ENDPOINT_REQUIRED`, `services.py:303-308`) ; il faut passer par la route d'arrêt
  d'attente. En revanche `waiting → completed` déclenche l'arrêt d'attente automatiquement
  (`services.py:309-316`).
- Un `PATCH /status` vers `completed` sur une course déjà `completed` est **idempotent** : log
  `ride.completion.retry` en warning et renvoi du détail (`services.py:292-301`).

L'historique des transitions est persisté (`RideStatusTransition`, `entities.py:415-423`) avec
`from_status`, `to_status`, `changed_at` et des métadonnées libres.

---

## 3. Règles et valeurs effectives

Source unique : `app_base/core/settings.py`. Les valeurs ci-dessous sont les **défauts du code**,
surchargeables par variables d'environnement.

### 3.1 Tarification

**Les valeurs sont dans le registre unique** `docs/mapping/PARAMETRES_CONFIGURABLES.md`, avec leur
emplacement exact et leur mécanisme de changement. Seuls les comportements sont décrits ici.

Cinq valeurs interviennent : tarif de base, prix au kilomètre, prix à la minute, plafond de majoration et
taux de commission — toutes en **constantes de code** ou en règle tarifaire stockée en base.

Les trois premières ne s'appliquent qu'en l'absence de règle active en base
(`PricingRuleRepository.find_active(city="Abidjan", vehicle_category=...)`, `services.py:100-103`).
La majoration provient de la règle en base, bornée par `min(rule.surge_multiplier, _SURGE_CAP)`
(`services.py:104`) — il n'y a pas de calcul automatique offre/demande, seulement un multiplicateur
stocké.

La commission est appliquée deux fois dans le cycle : à l'estimation
(`platform_commission = round(total × _COMMISSION_RATE)`, `services.py:1000`) et à la complétion
(`ride.platform_commission = final_fare × ride.commission_rate`, `services.py:350`). Le taux est
**figé sur la course** à la création (`commission_rate=...`, `services.py:160`), donc une modification
du taux ne réécrit pas les courses existantes. `driver_payout_estimate = final_fare - platform_commission`
(`services.py:351`).

Le devis est **sans état** : `estimate_pricing` calcule et renvoie, sans persistance, sans identifiant
de devis, sans date de validité. Aucune occurrence de `quote`, `valid_until` ou équivalent dans
`app_base/modules/ride`. Il n'y a donc pas de mécanisme d'expiration de devis ni de référence de
déduplication des demandes.

Trois niveaux de confort existent (`ComfortLevel`, `entities.py:74+`) avec un multiplicateur
(`_comfort_multiplier`), ainsi que trois catégories de véhicule (`VehicleCategory` : `standard`,
`comfort`, `van`, `entities.py:69-73`).

### 3.2 Attente

Trois paramètres, tous pilotables par environnement et listés dans le registre : tarif par minute, seuil
de vitesse en dessous duquel le véhicule est considéré arrêté, et âge maximal de la télémétrie acceptée.

Conditions d'activation (`services.py:366-395`) : seul le chauffeur assigné ou un admin ; la course doit
être `in_progress` (sinon `409 WAITING_INVALID_RIDE_STATUS`) ; une vitesse GPS doit être fournie (sinon
`409 WAITING_TELEMETRY_REQUIRED`) ; elle doit être sous le seuil (sinon `409 VEHICLE_NOT_STOPPED`).
L'appel est idempotent si la course est déjà en attente.

Il n'y a **aucune franchise gratuite** dans ce chemin : la facturation part de `waiting_started_at` au
tarif par minute. Aucun contrôle de distance au point de prise en charge n'intervient.

### 3.3 Démarrage de course

`update_status` vers `in_progress` (`services.py:316-318`) ne vérifie que l'identité de l'acteur, puis
déclenche `_ensure_map_trace_started(ride)`. **Aucun** contrôle de proximité chauffeur/passager, aucune
exigence sur l'âge ou la précision des positions, et aucun code de prise en charge de secours.

### 3.4 Annulation

`services.py:519-553`. Le motif doit appartenir à `VALID_CANCEL_REASONS`. Autorisé pour le passager, le
chauffeur assigné ou un admin. Refusé sur `completed` (`409 RIDE_ALREADY_COMPLETED`), sur une course déjà
annulée, et sur `no_driver_found` (`409 RIDE_NOT_CANCELLABLE`). Si la course est en attente, l'attente
est arrêtée d'abord.

Le statut cible est `cancelled_by_driver` si le motif est `driver_unavailable` ou si l'acteur est le
chauffeur non-admin ; sinon `cancelled_by_passenger`.

**Aucune facturation** n'est produite par une annulation, quel que soit le statut de départ. Il n'existe
pas de notion de fin anticipée facturée : annuler une course `in_progress` la termine en `cancelled_*`
sans calcul de trajet effectué. L'issue alimente le moteur de priorité
(`_record_priority_outcome`, `services.py:546`).

### 3.5 Matching et recherche

Cinq paramètres, tous pilotables par environnement et listés dans le registre : pas d'élargissement du
rayon, rayon maximal, budget horloge total, activation du reclassement par temps de trajet, taille de la
liste courte reclassée.

Modèle : vagues d'offres. Le rayon s'élargit d'un pas à chaque nouvelle vague, plafonné, et la recherche
entière est abandonnée après le budget horloge. Il s'agit d'un **élargissement par pas uniforme**, non
d'une séquence de phases à durées et rayons nommés.

Le classement ETA est un raffinement : parmi les candidats triés par distance, une liste courte est
reclassée par ETA réel DiddiMap. Le commentaire du code est explicite —
*« If DiddiMap is unavailable the engine silently keeps the distance order, so ranking never blocks
dispatch »* (`settings.py:54-57`). C'est le seul repli silencieux assumé face à DiddiMap.

Moteur de priorité (`settings.py:71-75`) : une fenêtre glissante, un bonus plafonné, un nombre de
secondes par point, et des points gagnés ou perdus selon l'issue de la course. Ces valeurs amorcent une
configuration **stockée en base**, éditable via `PUT /internal/v1/admin/dispatch/config` — c'est le seul
bloc de paramètres métier réellement pilotable à chaud. Valeurs dans le registre.

L'exclusivité d'attribution repose sur un `SET NX` Redis (claim de l'offre) doublé d'une contrainte en
base comme dernier garde-fou — les deux sont couverts par `tests/test_matching.py`.

### 3.6 Éligibilité chauffeur

Deux contrôles existent — solde minimum et plafond de commission estimée (`settings.py:124-125`) — et
sont **neutralisés par leurs valeurs par défaut**. Un chauffeur peut donc passer en ligne sans solde
minimum. Valeurs dans le registre.

### 3.7 Rapports Pilotage

La fenêtre interrogeable est volontairement bornée (`settings.py:79`) pour qu'un appelant de service ne
transforme pas une route journalière en balayage complet. Le cache des ventilations a deux durées, plus
courte pour le jour courant que pour un jour clos (`settings.py:80-81`). Valeurs dans le registre.

La réponse `finance-summary` est typée
(`PilotageFinanceSummaryResponse`, `ride/presentation/summary_schemas.py:39-48`) avec 16 métriques et
trois contrôles comptables bloquants décrits dans `docs/contracts/PILOTAGE_FINANCE_SUMMARY_V1.md`.

Cette réponse ne contient **ni** bloc `freshness` **ni** `deep_links`. Seul `health-summary` publie
`freshness_window_seconds: 60` (`summary_router.py:61-84`).

---

## 4. Services applicatifs

| Service | Fichier | Responsabilité |
| --- | --- | --- |
| `AuthService` | `auth/application/services.py:54` | `register`, `request_otp`, `verify_otp`, `refresh` |
| `RideService` | `ride/application/services.py:65` | cycle de vie complet de la course, 18 méthodes publiques |
| `MatchingService` | `ride/application/matching_service.py:69` | `try_match`, `accept`, `decline`, `advance_expired_offer`, `release_driver` |
| `DriverService` | `ride/application/driver_service.py:36` | profil, KYC chauffeur, KYV véhicule, capacités — 19 méthodes |
| `ScoringService` | `ride/application/scoring_service.py:15` | `get_my_scores`, `get_ride_score` |
| `PaymentService` | `payment/application/services.py` | PaymentIntent, webhook DiddiPay, confirmation cash, wallet |
| `PartnerService` | `partner/application/services.py` | partenaires, membres, affiliation chauffeur, véhicules |
| `RideSummaryService` | `ride/application/summary_service.py:17` | `daily_summary`, `pilotage_daily_summary`, `pilotage_finance_summary` |
| `RideBreakdownService` | `ride/application/breakdown_service.py:36` | `breakdown` avec cache |
| `PriorityService` | `ride/application/priority_service.py` | points et bonus de dispatch |
| `EmergencyContactService` | `ride/application/emergency_contact_service.py` | contact d'urgence |
| `OperationalLogSearchService` | `observability/application/services.py` | recherche de logs via Loki |
| `DriverProvisioningService` | `ride/application/driver_provisioning_service.py` | provisioning S2S Backoffice |
| `CapabilityProjection*` | `ride/application/capability_projection*.py` | outbox + worker vers DiddiFreeID |

Il n'existe pas de service de tarification séparé : le calcul vit dans `RideService` et dans les
fonctions module de `services.py` (`_pricing_breakdown`, `_pricing_response`). `tests/test_pricing_service.py`
teste ces fonctions.

Note observabilité : `log_event()` (`app_base/core/observability.py`) est appelé depuis 128 endroits et
émet un événement métier JSON via `uvicorn.error`. C'est le second nœud le plus connecté du dépôt après
`ApiError`.

---

## 5. Intégrations

### 5.1 Sortantes

| Service | Client | Configuration | Comportement en échec |
| --- | --- | --- | --- |
| DiddiFreeID | `ride/infra/identity_capability_client.py` | `identity_base_url`, `identity_jwks_url`, `identity_issuer=diddifree-id`, `identity_service_client_{id,secret}` | codes `SERVICE_TOKEN_*`, `SERVICE_JWKS_UNAVAILABLE` |
| DiddiMap | `ride/infra/routing_client.py` | `diddimap_base_url`, `diddimap_service_audience=diddimap`, `diddimap_service_token_url` | échec explicite : `DIDDIMAP_UNAVAILABLE`, `DIDDIMAP_INVALID_RESPONSE`, `DIDDIMAP_AUTHENTICATION_FAILED`, `DIDDIMAP_BUSINESS_ERROR` |
| DiddiPay | `payment/infra/diddipay_client.py` | `diddipay_base_url`, `diddipay_client_id=diddigo`, `diddipay_callback_secret`, `diddigo_payment_callback_url` | réconciliation périodique |
| DiddiFiles | `ride/infra/diddifiles_client.py` | `diddifiles_base_url`, `diddifiles_service_client_{id,secret}` | — |
| FCM (Google) | `notification/infra/fcm.py` | `push_enabled=false` par défaut, `fcm_project_id`, `fcm_service_account_json` | désactivé |
| WhatsApp + SMTP | `ride/application/emergency_notifications.py` | `emergency_whatsapp_webhook_url`, `emergency_smtp_host`, timeout `10` s | — |
| Loki | `observability/infra/loki.py` | `loki_base_url`, `loki_diddigo_service_label` | source unique, pas de repli |

Vérification locale des JWT DiddiFreeID en RS256 via JWKS — DiddiGo ne rappelle pas DiddiFreeID à chaque
requête.

Flux sortant asynchrone : l'outbox de projection de capacités
(`ride/infra/capability_projection_repository.py`) pousse l'état des capacités chauffeur vers
DiddiFreeID. File en base avec `projection_version` et `event_id` pour l'idempotence, livraison
périodique, réconciliation de rattrapage, traitement par lots bornés, retry exponentiel borné, puis
dead-letter (`settings.py:91-97`). Active par défaut. Intervalles dans le registre.

Réconciliation paiements (`settings.py:146-156`) : activée, périodique, par lots bornés, sur les intents
compris entre un âge minimal — grâce laissée au payeur encore sur la page de paiement — et un âge maximal
au-delà duquel DiddiPay a expiré l'intent. Elle relit `GET /payment-intents/{id}` pour qu'un webhook
perdu se répare seul. Intervalles dans le registre.

### 5.2 Entrantes

| Appelant | Surface | Garde |
| --- | --- | --- |
| Applications mobiles | `/v1/*` | JWT humain DiddiFreeID |
| Pilotage | `/internal/pilotage/*`, `/internal/v1/ride-summary` | S2S `sub=service:pilotage`, scope `diddigo:ride-summary:read` |
| Backoffice | `/internal/v1/drivers/*`, `/internal/v1/admin/*` | S2S admin actor + idempotence Redis (`S2SCommandStore`) |
| DiddiPay | `POST /internal/webhooks/diddipay` | `diddipay_callback_secret` |
| Prometheus | `app:8000/metrics` | réseau |
| Promtail | logs Docker | label `diddifree_observability=diddigo` |

Idempotence des commandes S2S : `app_base/core/s2s_command_store.py`, réservation Redis
(`reserve`/`complete`/`release`), TTL `86 400` s pour les commandes KYC et de provisioning
(`settings.py:122-123`).

L'alias de scope `ride-summary:read` reste accepté par le vérificateur pendant la migration
(`app_base/core/service_scopes.py`, `canonicalize_scopes`).

### 5.3 Stockage propre

PostgreSQL + PostGIS — les positions sont des `GEOGRAPHY(POINT,4326)`, aller-retour écriture/lecture
couvert par `tests/test_ride_flow.py`. Redis — offres (`OFFER_KEY_PREFIX`), claims (`CLAIM_KEY_PREFIX`),
disponibilité, positions, vitesses, essais déjà tentés, verrous, contextes de retour paiement
(`payment_return_context_ttl_seconds = 900`).

---

## 6. Ce que les tests prouvent

52 fichiers sous `tests/`, plus un dossier `tests/e2e`.

Les tests de bout en bout contre la base réelle sont dans `tests/test_ride_flow.py` : cycle course +
paiement, survie des coordonnées PostGIS à l'aller-retour, terminalité de `no_driver_found`, garde sur
les courses réellement vivantes.

`tests/test_matching.py` prouve, par ses propres docstrings : l'onboarding chauffeur, les offres
séquentielles, la fenêtre de réponse de 15 secondes qui expire par suppression de la clé d'offre,
l'épuisement du pool quand le seul chauffeur décline, le passage à la vague suivante quand personne ne
répond, l'impossibilité du double-accept via `SET NX`, la contrainte base comme garde final, et
l'exclusion d'un chauffeur déjà en course.

Couverture par domaine : matching (`test_matching*.py` ×4, dont vagues et classement ETA), machine à
états (`test_ride_state_machine.py`), attente (`test_ride_waiting_service.py`), tarification
(`test_pricing_service.py`), scoring, KYC chauffeur, DiddiPay (`test_diddipay_*.py` ×3,
réconciliation, contextes de retour), token de service (`test_service_token_verifier.py`), contrat
OpenAPI interne (`test_internal_openapi_contract.py`), accès Backoffice
(`test_backoffice_access_contract.py`), résumés et breakdown Pilotage (×4), recherche de logs,
projection de capacités, websocket, places, urgences, notifications.

Un test qui passe est une preuve du comportement testé. Un ticket fermé n'en est pas une.

---

## 7. Ce qui est absent de la surface du code

Relevé factuel, sans préjuger de la phase produit visée : pas de statut d'arrivée chauffeur ; pas de
contrôle de proximité au démarrage ; pas de code de prise en charge de secours ; pas d'expiration de
devis ; pas de référence de déduplication des demandes de devis ; pas de calcul automatique de
majoration offre/demande ; pas de tarification par zone ; pas de route de messagerie en course ; pas de
course programmée ; pas de route de retrait professionnel ; pas de bloc `freshness` dans les réponses de
résumé Pilotage autres que `health-summary` ; pas de facturation de fin anticipée.
