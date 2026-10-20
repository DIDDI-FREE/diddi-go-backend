# Parcours DiddiGo — tels que le code les réalise

Date de relevé : 9 octobre 2026. Branche : `feat/pilotage-finance-summary-v1`.

Catalogue de ce qui existe dans le code : fonctionnalités, flux, cas limites, exigences non
fonctionnelles. Le pendant côté produit est `PARCOURS_CIBLE_DIDDIGO.md`, de structure identique.

**Aucun montant ici.** Les valeurs, seuils et plafonds sont dans `PARAMETRES_CONFIGURABLES.md` ; ce
document ne décrit que le comportement et nomme la clé de paramètre quand une valeur intervient. Les
chiffres bougeront ; le comportement est ce qui doit être compris.

Méthode : lecture du dépôt, surface OpenAPI générée, codes d'erreur exhaustifs, docstrings des tests,
événements WebSocket. Pas de lecture du document produit pendant ce relevé. Rapprochement Jira en
section 6.

---

## 1. Inventaire des fonctionnalités

### 1.1 Passager

| Fonctionnalité | Surface | Jira |
| --- | --- | --- |
| Estimer le prix d'une course | `POST /v1/rides/pricing/estimate` | UC-009 ✅ |
| Choisir un niveau de confort parmi trois | paramètre `comfort_level` de l'estimation et de la demande | UC-017 ○ |
| Choisir son moyen de paiement | paramètre de la demande de course | UC-254 ✅ |
| Commander une course | `POST /v1/rides` | UC-010 ✅ |
| Suivre l'état de sa course | `GET /v1/rides/{id}` + WebSocket `ride.status_changed` | UC-011 ✅ |
| Voir la position du chauffeur | WebSocket `ride.driver_location` | UC-012 ○ |
| Être informé qu'aucun chauffeur n'est disponible | WebSocket `ride.no_driver_found`, statut terminal | UC-253 ○ |
| Annuler une course | `POST /v1/rides/{id}/cancel` | UC-013 ✅ |
| Partager un lien de suivi | `POST /v1/rides/{id}/share-link`, `GET /v1/rides/shared/{token}` | UC-014 ✅ |
| Déclencher une alerte d'urgence | `POST /v1/rides/{id}/emergency` | UC-015 ✅ |
| Gérer son contact d'urgence | `GET`/`PUT`/`DELETE /v1/me/emergency-contact` | — |
| Noter la course | `POST /v1/rides/{id}/rating` | UC-016 ✅ |
| Consulter son historique | `GET /v1/rides` | — |
| Consulter ses scores | `GET /v1/me/scores`, `GET /v1/rides/{id}/score` | — |
| Rechercher un lieu | `GET /v1/places/search` | — |
| Payer une course | `POST /v1/payments/{ride_id}/prepare`, `GET /v1/payments/{ride_id}` | — |

### 1.2 Chauffeur

| Fonctionnalité | Surface | Jira |
| --- | --- | --- |
| Créer son profil chauffeur | `POST /v1/drivers/profile` | UC-018 ✅ |
| Soumettre et resoumettre ses documents KYC | `POST /v1/drivers/kyc/resubmit` | UC-019 ✅ |
| Ajouter et mettre à jour un véhicule | `POST /v1/drivers/vehicle`, `PUT /v1/drivers/me/vehicle` | UC-020 ✅ |
| Soumettre les documents du véhicule, dont les quatre côtés | `POST /v1/drivers/vehicles/{id}/kyv/resubmit` | UC-021 ✅ · UC-270 ✅ |
| Suivre l'état de validation de son dossier | `GET /v1/drivers/me`, `GET /v1/me/capabilities` | UC-022 ✅ |
| Passer en ligne et hors ligne | `POST /v1/drivers/online`, `/offline` | UC-023 ✅ · UC-024 ✅ |
| Recevoir une offre de course | WebSocket `ride.new_request` | UC-025 ✅ |
| Accepter ou refuser une course | `POST /v1/rides/{id}/accept`, `/decline` | UC-026 ✅ · UC-027 ✅ |
| Envoyer sa position pendant la course | `POST /v1/rides/{id}/location-samples`, WebSocket `driver.location_push` | UC-028 ✅ |
| Faire avancer les étapes de la course | `PATCH /v1/rides/{id}/status` | UC-029 ✅ |
| Activer le mode attente, bloqué si le véhicule roule | `POST /v1/rides/{id}/waiting/start`, `/stop` | UC-271 ✅ |
| Enregistrer une escale et un supplément | `POST /v1/rides/{id}/stops`, `/supplements` | UC-272 ✅ |
| Annuler sans pénalité quand le passager est absent | `POST /v1/rides/{id}/cancel` avec motif | UC-273 ✅ |
| Mettre à jour sa photo de profil | `PATCH /v1/drivers/me/profile-photo` | — |
| Consulter ses gains et son historique | `GET /v1/drivers/me/wallet`, `/ledger` | UC-030 ✅ · UC-031 ✅ |
| Recharger son wallet | `POST /v1/drivers/me/wallet/topups`, `GET …/topups/{id}` | — |
| Faire confirmer un encaissement cash | `POST /v1/payments/{ride_id}/confirm-cash` | — |

### 1.3 Opérateur et services internes

| Fonctionnalité | Surface |
| --- | --- |
| Revue KYC chauffeur, approbation et rejet | `GET /v1/drivers/kyc`, `/{id}/kyc`, `POST …/kyc/{approve,reject}` et doublons S2S en `/internal/v1/drivers/*` |
| Revue KYV véhicule | `GET /v1/admin/vehicles/kyv`, `POST /v1/drivers/vehicles/{id}/kyv/{approve,reject}` |
| Provisionner un chauffeur | `POST /internal/v1/drivers/provision` |
| Gérer partenaires, membres, affiliations et véhicules de flotte | 15 routes, en `/v1/admin/partners/*` et `/internal/v1/admin/partners/*` |
| Configurer le dispatch et les règles de priorité | `GET`/`PUT /internal/v1/admin/dispatch/config`, `/priority-rules`, `POST …/priority-boosts` |
| Consulter wallet et grand livre d'un chauffeur | `GET /v1/admin/drivers/{id}/wallet`, `/ledger` |
| Rapprocher des paiements | `POST /v1/admin/payments/reconcile` et variantes par course et par recharge |
| Rechercher les logs d'une course ou d'un chauffeur | `GET /v1/admin/logs/rides/{id}`, `/drivers/{id}` |
| Résumés Pilotage | `/internal/pilotage/{daily-summary,finance-summary,breakdown,health-summary}` + `/internal/v1/ride-summary` |
| Recevoir les notifications DiddiPay | `POST /internal/webhooks/diddipay` |

124 routes au total : 84 en `/v1`, 36 en `/internal`, 4 non authentifiées.

---

## 2. Flux

### 2.1 Entrée dans le service

```
POST /v1/auth/register            → compte créé
POST /v1/auth/otp/request         → code généré, limité par go.otp_rate_limit
POST /v1/auth/otp/verify          → jetons d'accès et de rafraîchissement
POST /v1/auth/refresh             → renouvellement
GET  /v1/auth/me                  → profil
```

L'OTP n'est pas envoyé : `# TODO: replace with real SMS delivery. In dev, the OTP is logged.`
(`auth/application/services.py`). Les codes consommés ou expirés sont conservés pour l'audit. Les jetons
DiddiFreeID entrants sont vérifiés localement en RS256 via JWKS, sans rappel à DiddiFreeID ; un
utilisateur fantôme est maintenu côté DiddiGo pour les intégrités référentielles.

### 2.2 Activation du chauffeur

```
POST /v1/drivers/profile       → profil créé, en attente
POST /v1/drivers/vehicle       → véhicule créé, en attente
      documents déposés chez DiddiFiles ; DiddiGo ne stocke que des file_id
opérateur : approbation KYC chauffeur   ─┐
opérateur : approbation KYV véhicule    ─┴→ capacités recalculées
                                           → projection poussée vers DiddiFreeID
POST /v1/drivers/online        → disponible pour le matching
```

La mise en ligne est refusée si le profil n'est pas vérifié (`403 DRIVER_NOT_VERIFIED`) ou s'il n'y a pas
de véhicule actif (`409 NO_ACTIVE_VEHICLE`). Les deux contrôles sont rejoués à l'acceptation d'une course
(`matching_service.py:222,232`), donc une révocation entre la mise en ligne et l'acceptation est prise en
compte. Deux contrôles de solde existent mais sont neutres par défaut
(`go.online_min_balance`, plafond de commission estimée).

La projection des capacités vers DiddiFreeID passe par une **outbox en base**, pas par un appel
synchrone : file avec version de projection et identifiant d'événement, livraison périodique,
réconciliation, réessai exponentiel, puis lettre morte. Un échec de DiddiFreeID ne bloque donc pas
l'approbation.

### 2.3 Cycle de vie d'une course

```
estimation  POST /v1/rides/pricing/estimate
            → DiddiMap estime distance et durée
            → barème lu en base, sinon défauts de code
            → réponse non persistée, sans identifiant de devis

demande     POST /v1/rides   → requested
            barème, taux de commission et niveau de confort figés sur la course

matching    vagues d'offres, rayon élargi par pas, budget horloge global
            offre poussée en WebSocket ride.new_request
            claim Redis SET NX → exclusivité
            → matched            si un chauffeur accepte
            → no_driver_found    si le budget est épuisé (terminal)

approche    PATCH /status → driver_en_route
            positions poussées, trace DiddiMap ouverte au démarrage

course      PATCH /status → in_progress
            └ waiting/start → waiting   (exige in_progress, véhicule arrêté)
              waiting/stop  → in_progress
              stops, supplements → s'ajoutent au total
            PATCH /status → completed
            → recalcul réel du trajet ; en cas d'échec DiddiMap, tarif verrouillé conservé
            → total = base + attente + suppléments
            → commission et gain chauffeur calculés sur ce total

paiement    POST /v1/payments/{ride}/prepare → DiddiPay
            ou POST /v1/payments/{ride}/confirm-cash
            webhook DiddiPay, réconciliation périodique en filet
```

### 2.4 Machine à états

```
requested ──► matched ──► driver_en_route ──► in_progress ⇄ waiting ──► completed
    │                                              │            │
    ├──► no_driver_found (terminal)                 └──► cancelled_by_* (terminal)
    └──► cancelled_by_* (terminal)
```

Toute transition hors table lève `409 INVALID_STATUS_TRANSITION`. Il n'existe **pas** de statut
d'arrivée du chauffeur : `driver_en_route` passe directement à `in_progress`. `waiting` n'est atteignable
que depuis `in_progress`, donc après démarrage. Chaque transition est historisée avec son origine, sa
destination, son horodatage et des métadonnées libres.

### 2.5 Urgence

`POST /v1/rides/{id}/emergency` déclenche une notification vers un webhook WhatsApp et un envoi SMTP,
avec un délai d'expiration propre. L'adresse de support et l'expéditeur sont configurés par
environnement. Le contact d'urgence du passager est stocké séparément et modifiable.

### 2.6 Collecte Pilotage

Les cinq routes `/internal/pilotage/*` partagent la même garde : audience `diddigo`, scope
`diddigo:ride-summary:read`, sujet `service:pilotage`. L'alias de scope historique reste accepté pendant
la migration. La profondeur interrogeable est bornée. Les ventilations sont mises en cache avec un TTL
plus long pour les journées closes. Le résumé financier applique trois contrôles comptables bloquants et
échoue plutôt que de publier des chiffres incohérents.

---

## 3. Cas limites réellement traités

Relevé à partir des **60 codes d'erreur** émis par le code et des docstrings des tests. C'est la
meilleure preuve de ce qui a été pensé.

### 3.1 Authentification et session

| Cas | Traitement |
| --- | --- |
| Code OTP erroné | `400 OTP_INVALID` |
| Code OTP expiré | `410 OTP_EXPIRED` — distinct de l'invalide |
| Jeton absent, invalide, expiré | `401 TOKEN_MISSING` / `TOKEN_INVALID` / `TOKEN_EXPIRED` |
| Jeton de rafraîchissement invalide | `401 REFRESH_TOKEN_INVALID` |
| Numéro déjà inscrit | `409 PHONE_ALREADY_REGISTERED` |
| Rôle inattendu | `403 FORBIDDEN_ROLE`, `422 INVALID_ROLE` |
| Utilisateur non vérifié ou suspendu | `403 USER_NOT_VERIFIED` / `USER_SUSPENDED` |
| DiddiFreeID non configuré | `500 IDENTITY_NOT_CONFIGURED` |

### 3.2 Appels de service à service

Huit cas distingués : identifiant client manquant ou invalide, jeton invalide, expiré ou inactif, scope
insuffisant, sujet inattendu, JWKS injoignable. La granularité permet de diagnostiquer sans deviner.

### 3.3 Matching et attribution

| Cas | Traitement | Preuve |
| --- | --- | --- |
| Deux chauffeurs acceptent simultanément | claim Redis `SET NX` : un seul gagne ; contrainte en base comme garde final | `test_matching.py` |
| Offre expirée pendant la réponse | `409 OFFER_EXPIRED` ; la fenêtre se termine par suppression de la clé d'offre | `test_matching.py` |
| Offre adressée à un autre chauffeur | `403 OFFER_NOT_YOURS` | — |
| Course déjà attribuée | `409 RIDE_ALREADY_MATCHED` | — |
| Le seul chauffeur refuse | le vivier est épuisé, pas de boucle de retour sur lui | `test_matching.py` |
| Personne ne répond à la première vague | la fenêtre expire, la course est proposée à la vague suivante | `test_matching.py` |
| Un chauffeur déjà en course | exclu des offres | `test_matching.py` |
| Chauffeur devenu libre pendant une vague ultérieure | redevient candidat | `test_matching_wave_dynamics.py` |
| Budget de recherche épuisé | `no_driver_found`, terminal, événement WebSocket dédié | `test_ride_flow.py` |
| DiddiMap indisponible pour le reclassement | **repli silencieux** sur l'ordre de distance, le dispatch n'est jamais bloqué | `settings.py:54-57` |

### 3.4 Cycle de vie de la course

| Cas | Traitement |
| --- | --- |
| Course inexistante | `404 RIDE_NOT_FOUND` |
| Acteur non concerné par la course | `403 RIDE_NOT_OWNED_BY_USER` |
| Transition d'état interdite | `409 INVALID_STATUS_TRANSITION` |
| Annuler une course déjà terminée ou déjà annulée | `409 RIDE_ALREADY_COMPLETED` / `RIDE_ALREADY_CANCELLED` |
| Annuler une course sans chauffeur trouvé | `409 RIDE_NOT_CANCELLABLE` — levait auparavant hors du domaine, cas couvert explicitement |
| Terminer une course déjà terminée | **idempotent** : journal d'avertissement `ride.completion.retry`, détail renvoyé |
| Motif d'annulation inconnu | `422 INVALID_CANCEL_REASON` |
| Note déjà soumise, note hors bornes | `409 RATING_ALREADY_SUBMITTED`, `422 RATING_OUT_OF_RANGE` |
| Lien de partage inconnu | `404 SHARE_LINK_NOT_FOUND` |
| Reprise après fermeture de l'application | état relu depuis la base, début d'attente persisté, aucune nouvelle mission créée |

### 3.5 Attente et suppléments

| Cas | Traitement |
| --- | --- |
| Attente demandée hors course en cours | `409 WAITING_INVALID_RIDE_STATUS` |
| Attente demandée sans télémétrie | `409 WAITING_TELEMETRY_REQUIRED` |
| Véhicule encore en mouvement | `409 VEHICLE_NOT_STOPPED`, avec la vitesse mesurée et le maximum admis dans la réponse |
| Télémétrie trop ancienne | refusée via le TTL Redis des positions |
| Attente déjà active | appel **idempotent**, état renvoyé tel quel |
| Reprise de course depuis l'attente par la route d'état | refusée, `409 WAITING_STOP_ENDPOINT_REQUIRED` — la route d'arrêt est obligatoire |
| Fin de course pendant une attente active | l'attente est arrêtée automatiquement avant la complétion |
| Attente arrêtée automatiquement | événement WebSocket `ride.waiting.auto_stopped` |
| Montant de supplément invalide | `422 INVALID_SUPPLEMENT_AMOUNT` |

### 3.6 Tarification et DiddiMap

| Cas | Traitement |
| --- | --- |
| Distance nulle ou négative renvoyée par DiddiMap | `502 DIDDIMAP_INVALID_RESPONSE` |
| DiddiMap injoignable | `503 DIDDIMAP_UNAVAILABLE` |
| Erreur d'authentification DiddiMap | code dédié, distinct de l'indisponibilité |
| Erreur **métier** DiddiMap | code dédié, distinct de l'indisponibilité — ticket SCRUM-439 |
| Recalcul réel du trajet en échec à la complétion | **la course se termine quand même** avec le tarif verrouillé ; le statut d'analyse de trace est marqué en erreur et journalisé — SCRUM-437 |
| Trace GPS inexploitable | journalisée explicitement — SCRUM-440 |
| Niveau de confort ou catégorie de véhicule inconnus | `422 INVALID_COMFORT_LEVEL` / `INVALID_VEHICLE_CATEGORY` |
| Aucune règle tarifaire active en base | repli sur les constantes de code |

### 3.7 Argent

| Cas | Traitement |
| --- | --- |
| Montant ne correspondant pas à l'attendu | `422 AMOUNT_MISMATCH` |
| Moyen de paiement inconnu | `422 INVALID_PAYMENT_METHOD` |
| Webhook DiddiPay perdu | réconciliation périodique relisant l'intent, avec grâce initiale et âge maximal |
| Webhook répété | contexte de retour consommable une fois, idempotence |
| Webhook répondant 500 après traitement réussi | corrigé, SCRUM-514 |
| Incohérence d'allocation détectée | `500 FARE_ALLOCATION_MISMATCH`, `PAYMENT_ALLOCATION_MISMATCH`, `DRIVER_PAYMENT_MISMATCH`, `INVALID_FINANCE_AMOUNT` — **le système refuse de publier un chiffre faux** |
| Retours passager et pro confondus | séparés et sécurisés, SCRUM-461 |

### 3.8 Rapports internes

Date malformée (`422 INVALID_DATE`), date future (`SUMMARY_DATE_IN_FUTURE`), date hors fenêtre
(`SUMMARY_DATE_OUT_OF_RANGE`), base indisponible (`503 RIDE_SUMMARY_UNAVAILABLE`), Loki indisponible
(`503 LOG_SEARCH_UNAVAILABLE`), curseur ou plage de temps invalides. Les contrôles comptables du résumé
financier échouent explicitement plutôt que de publier des chiffres qui ne s'équilibrent pas.

### 3.9 Cas limites non traités

Pas d'arrivée chauffeur, donc pas de cas limite associé. Pas de contrôle de proximité au démarrage, donc
pas de secours quand le GPS est inexploitable — aucun code de prise en charge, aucun compteur d'essais.
Pas d'expiration de devis, donc pas de cas « devis périmé ». Pas de déduplication des demandes de devis.
Pas de fin anticipée facturée. Pas de blocage de nouvelle commande en cas d'impayé. Pas de purge des
traces GPS.

---

## 4. Exigences non fonctionnelles observables dans le code

### 4.1 Idempotence et rejeu

Trois mécanismes distincts. **Verrou d'exclusivité** : claim Redis `SET NX` sur l'attribution, doublé
d'une contrainte en base. **Réservation de commande S2S** : `S2SCommandStore` avec réservation,
confirmation et libération, appliqué aux commandes KYC et au provisioning chauffeur, avec TTL.
**Idempotence applicative** : complétion de course rejouable, démarrage d'attente rejouable, contexte de
retour de paiement consommable une seule fois, projection de capacités portant une version et un
identifiant d'événement.

Un ticket ouvert signale une faille sur ce terrain : SCRUM-529, commandes KYC et annulation en échec pour
identifiant de requête non conforme et clé d'idempotence manquante.

### 4.2 Authentification et cloisonnement

Trois surfaces séparées : jeton humain, jeton de service scopé, secret de callback. Vérification RS256
locale via JWKS, sans dépendance synchrone à DiddiFreeID à chaque requête. Scopes canonicalisés avec
alias de compatibilité pendant la migration. Vérification du sujet attendu en plus du scope, donc un
service tiers correctement scopé mais mal identifié est refusé. Visibilité de l'argent conditionnée au
rôle de l'appelant dans le détail de course (`_money_visible`). Les réponses de ventilation Pilotage sont
sans donnée personnelle.

Dette signalée : un en-tête `X-User-ID` historique reste accepté, SCRUM-485 en revue.

### 4.3 Résilience aux pannes de dépendances

| Dépendance | Comportement en panne |
| --- | --- |
| DiddiMap, estimation | échec **explicite**, quatre codes distincts |
| DiddiMap, reclassement par temps de trajet | **repli silencieux** sur l'ordre de distance |
| DiddiMap, recalcul à la complétion | la course se termine avec le tarif verrouillé, erreur journalisée |
| DiddiPay | réconciliation périodique auto-réparatrice |
| DiddiFreeID, projection | outbox persistante, réessai exponentiel, lettre morte |
| Loki | `503` explicite, **pas de repli silencieux** |
| Redis | sondé par `/ready` |
| PostgreSQL | sondé par `/ready`, lecture sans journalisation à chaque échec de sonde |
| FCM | désactivé par défaut |

### 4.4 Bornes et protection contre l'abus

Limite de renvoi d'OTP. Durée de vie du code OTP. Fenêtre interrogeable des rapports bornée, pour qu'un
appelant de service ne transforme pas une route journalière en balayage complet. Liste courte de
reclassement bornée. Taille de lot bornée sur la projection et la réconciliation. Budget horloge global
sur la recherche de chauffeur, pour qu'une course ne cherche pas indéfiniment. TTL sur toutes les clés
Redis. Pagination par curseur sur la recherche de logs.

### 4.5 Observabilité

Événement métier JSON émis depuis **128 points** du code, via le canal `uvicorn.error` pour que la sortie
soit toujours capturée. Identifiant de requête propagé dans le contexte. Historique de transitions d'état
persisté en base. Métriques exposées pour Prométhée. Logs collectés par Promtail sur le label
d'observabilité du service, interrogeables via Loki, exposés par `GET /v1/admin/logs/rides/{id}` et
`/drivers/{id}` — un identifiant de course permet de retrouver son parcours. Métriques de projection
exposées. Statut d'analyse de trace persisté sur la course avec son code d'erreur.

Choix explicite documenté dans le code : les étiquettes de métriques restent à faible cardinalité, et
Loki est la source unique sans repli muet.

### 4.6 Intégrité financière

Six codes d'erreur en `500` dédiés aux incohérences d'allocation. Le principe est constant : **refuser de
répondre plutôt que publier un chiffre faux**. Les contrôles comptables du résumé financier sont
bloquants. Le taux de commission et le barème sont figés sur chaque course, donc aucune réécriture
d'historique. DiddiPay reste l'autorité sur les captures, remboursements partiels exacts, frais
processeur, règlements et payouts.

### 4.7 Données personnelles

Documents KYC et KYV délégués à DiddiFiles ; DiddiGo ne conserve que des identifiants de fichier.
Visibilité de l'argent selon le rôle. Ventilations Pilotage sans donnée personnelle. Codes OTP consommés
conservés pour l'audit. **Aucune purge automatique** des traces GPS n'a été trouvée.

### 4.8 Exploitation

`/health` et `/ready` séparés, la seconde sondant base et Redis. Origines CORS configurables avec
expression régulière par défaut limitée au développement local. Journalisation structurée en JSON avec
niveau configurable. Quatre fichiers de composition Docker : base, développement, observabilité,
Portainer — ce dernier exigeant les secrets et gardant Redis interne. Migrations Alembic, avec un service
d'initialisation jouant la migration comme préalable dans l'overlay local.

### 4.9 Preuve par les tests

52 fichiers de test. Un test de bout en bout contre la vraie base couvre le cycle course et paiement, la
survie des coordonnées PostGIS à l'aller-retour, la terminalité de l'absence de chauffeur. Quatre
fichiers couvrent le matching, dont la dynamique des vagues et le reclassement par temps de trajet. Trois
couvrent DiddiPay. Un couvre le contrat OpenAPI interne, un autre le contrat d'accès Backoffice. Les
docstrings de `test_matching.py` énoncent les invariants attendus en clair.

---

## 5. Ce qui n'existe pas dans le code

Course programmée. Tarification par zone. Majoration automatique offre/demande. Messagerie en course.
Reçu client. Lieux favoris. Carte de chaleur de la demande. Mode retour maison et mode ma destination.
Contrôle selfie d'inactivité. Points de priorité consultables par le chauffeur. Route de retrait
professionnel. Fournisseur SMS. Purge des traces. Bloc de fraîcheur sur les résumés de données.

---

## 6. Rapprochement Jira

48 tickets de cas d'usage sous les deux lots DiddiGo, plus 37 tickets techniques et transverses portant
l'étiquette ou le nom DiddiGo.

### 6.1 Cas d'usage réalisés et présents dans le code

Chauffeur : UC-018 à UC-031 (profil, KYC, véhicule, KYV, suivi de validation, en ligne et hors ligne,
réception d'offre, acceptation, refus, positions, étapes, gains, historique), UC-270 photos du véhicule,
UC-271 mode attente bloqué véhicule roulant, UC-272 escale et supplément, UC-273 annulation sans pénalité
sur absence du passager. Passager : UC-009 estimation, UC-010 commande, UC-011 suivi, UC-013 annulation,
UC-014 lien de suivi, UC-015 urgence, UC-016 notation, UC-254 choix du moyen de paiement.

### 6.2 Cas d'usage ouverts dont le code porte déjà une partie

| Ticket | Sujet | Ce que le code a déjà |
| --- | --- | --- |
| UC-012 ○ | Le passager voit la position du chauffeur | événement WebSocket `ride.driver_location` présent ; bloqué par SCRUM-536 côté contrat DiddiMap |
| UC-017 ○ | Comparer les trois niveaux de confort | trois niveaux et leurs multiplicateurs existent ; la comparaison est un parcours client |
| UC-253 ○ | Informer qu'aucun chauffeur n'est disponible et réessayer | statut terminal et événement WebSocket présents ; la reprise est un parcours client |
| UC-258 ○ | Le passager demande un arrêt et voit le surcoût | attente et suppléments existent côté chauffeur, pas de demande côté passager |
| UC-259 ○ | Le passager ajoute une escale, voit le surcoût et le valide | escale et supplément existent côté chauffeur ; la validation passager n'existe pas |
| UC-257 ○ | Annuler sans frais quand le chauffeur est silencieux au-delà du délai | annulation gratuite présente ; aucun délai de silence côté serveur |
| UC-255 ○ | Heure de la dernière position connue du chauffeur | positions horodatées en Redis ; non exposé comme tel |
| UC-256 ○ | Distinguer sa propre perte de connexion de celle du chauffeur | non traité |

### 6.3 Cas d'usage ouverts sans aucune contrepartie dans le code

UC-260 adresses favorites, UC-263 carte de chaleur, UC-264 badge sortie de zone, UC-265 mode retour
maison, UC-266 mode ma destination, UC-268 et UC-269 contrôle selfie d'inactivité, UC-274 points de
priorité consultables. Reclassés V2 : UC-261 commander pour autrui, UC-262 course programmée, UC-267
zones de préférence, UC-276 déclaration de préjudice, UC-277 chauffeur remplaçant avec gains isolés.

UC-275 ✦ *à tester* — renouvellement d'un document arrivé à expiration avant blocage : un calcul de
statut d'expiration des documents existe dans le service chauffeur.

### 6.4 Tickets techniques dont l'effet est visible dans le code

| Ticket | État | Trace dans le code |
| --- | --- | --- |
| SCRUM-419 | ✅ | vérificateur de jeton de service scopé, avec sujet attendu |
| SCRUM-420 | ✅ | route interne de résumé de courses |
| SCRUM-431 | ✅ | publication du statut opérationnel chauffeur vers DiddiFreeID |
| SCRUM-436 | ✅ | authentification de service DiddiMap pour les traces |
| SCRUM-437 | ✅ | la fin de course n'est pas bloquée par un trajet ignoré au scoring |
| SCRUM-438 | ✅ | complétion idempotente |
| SCRUM-439 | ✅ | erreurs métier DiddiMap distinguées des indisponibilités |
| SCRUM-440 | ✅ | journalisation des traces inexploitables |
| SCRUM-461 | ✅ | retours passager et professionnel séparés |
| SCRUM-514 | ✅ | webhook ne répondant plus 500 après succès |
| SCRUM-510 ✦ | à tester | outbox de projection avec réessai et réconciliation |
| SCRUM-513 ✦ | à tester | lettre morte sur utilisateur inconnu |
| SCRUM-466 ✦ | à tester | contrat d'accès Backoffice |
| SCRUM-569 ✦ | à tester | routes partenaires en S2S, legacy conservé |
| SCRUM-524 ✦ | à tester | escales et suppléments — le code les référence explicitement |
| SCRUM-485 ○ | en revue | en-tête utilisateur historique encore accepté |

### 6.5 Défauts ouverts touchant des parcours présents

| Ticket | Parcours concerné | Nature |
| --- | --- | --- |
| SCRUM-565 | entrée dans le service | le jeton émis par la vérification d'OTP serait rejeté par les routes protégées |
| SCRUM-567 | entrée dans le service | les comptes consommateur ne sont pas auto-provisionnés depuis DiddiFreeID |
| SCRUM-564 | toutes surfaces authentifiées | un jeton non vérifiable produirait un 500 au lieu d'un 401 |
| SCRUM-566 | commande de course | une violation d'intégrité serait classée en indisponibilité de base |
| SCRUM-536 | suivi du véhicule | contrat idempotent DiddiMap non livré |
| SCRUM-576 | traces de course | routes de traces à migrer vers des scopes S2S |
| SCRUM-529 ✦ | KYC et annulation par le Backoffice | identifiant de requête non conforme, clé d'idempotence manquante |
| SCRUM-549 ✦ | recharge et paiement | blocage de bout en bout côté DiddiPay |

Ces huit lignes viennent de Jira, pas de ma lecture du code. Aucun test n'a été exécuté en staging ; une
route présente ne prouve pas un parcours fonctionnel.

**Légende** — ✅ terminé · ✦ à tester · ○ ouvert ou en revue
