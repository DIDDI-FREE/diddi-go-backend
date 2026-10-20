# Écarts entre le code DiddiGo et la cible produit

Date de relevé : 9 octobre 2026. Branche : `feat/pilotage-finance-summary-v1`.

Confrontation de `CARTE_CODE_DIDDIGO.md` (état du code) et `CARTE_CIBLE_MVP_DIDDIGO.md` (décisions
produit). Les deux cartes ont été établies séparément avant cette comparaison.

**Ce document ne décide rien.** Il constate des différences entre deux sources. Trois rappels que les
sources portent elles-mêmes :

- une décision produit définit la cible, **pas** l'état de livraison ;
- les montants de `PARAMETRES_METIER.md` sont des **repères de cadrage révisables**, pas des valeurs
  finales ni une preuve de configuration active — un écart de valeur n'est donc pas automatiquement un
  défaut du code ;
- un test qui passe prouve le comportement testé ; un ticket fermé ne prouve rien sur la version
  déployée.

## Verdicts employés

| Verdict | Sens |
| --- | --- |
| **conforme** | le code réalise la règle décidée |
| **écart de valeur** | même comportement, valeur numérique différente |
| **écart structurel** | le modèle du code ne permet pas la règle telle qu'énoncée |
| **non implémenté** | aucune trace du mécanisme dans le code |
| **hors MVP, présent** | le code porte quelque chose que le produit place en V1 ou Later |
| **à vérifier** | je n'ai pas l'élément pour trancher |

---

## 1. Synthèse

| | Nombre |
| --- | --- |
| conforme | 9 |
| écart de valeur | 4 |
| écart structurel | 3 |
| non implémenté | 6 |
| hors MVP, présent | 2 |
| à vérifier | 5 |

Les trois écarts structurels se concentrent tous sur **la même zone : la fin de l'approche et le début de
course** — arrivée du chauffeur, attente de prise en charge, fin anticipée. C'est le bloc `BE015`
(« Attente facturée, escales, annulation et signalement urgent », MVP P0, 14→23 oct, état *à engager*).

L'écart le plus lourd en conséquence financière est le **taux de commission : 8 % dans le code contre
18 % dans les décisions**.

---

## 2. Tarification et commission

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-004` — commission Go sur le **montant total encaissé, attente et suppléments compris** | `final_fare = base + waiting_fee + supplements_total` puis `platform_commission = final_fare × commission_rate` (`services.py:349-350`) | **conforme** — l'assiette correspond |
| `go.commission_rate = 18 %` | `_COMMISSION_RATE = Decimal("0.08")` → **8 %** (`services.py:51`) | **écart de valeur** |
| `go.surge_cap = 1,5` (V1) | `_SURGE_CAP = Decimal("1.60")` (`services.py:50`) | **écart de valeur** |
| `PROD-015` — **aucune majoration automatique** au MVP, activation V1 plafonnée | pas de calcul offre/demande ; un `surge_multiplier` stocké en règle tarifaire est appliqué, borné par `_SURGE_CAP` (`services.py:104`) | **conforme** sur l'absence d'automatisme ; le multiplicateur manuel reste à qualifier → **à vérifier** |
| `PROD-004` — « règles d'arrondi à finaliser » | `quantize(Decimal("1"))` sur la commission, `round()` sur l'estimation (`services.py:350`, `services.py:1000`) | **à vérifier** — la règle cible n'est pas encore arrêtée |
| `PROD-015` — le **prix de référence est conservé après confirmation** | taux et barème figés sur la course à la création (`commission_rate=`, `services.py:160`) ; `locked_fare` conservé si le recalcul DiddiMap échoue (`services.py:775-783`) | **conforme** |
| `PROD-015` — **trois niveaux de confort** | `ComfortLevel` à trois valeurs + `_comfort_multiplier` | **conforme** |

Note sur la commission : le taux est **figé sur chaque course**, donc un alignement à 18 % ne réécrirait
pas l'historique. C'est cohérent avec la gouvernance demandée par `PARAMETRES_METIER.md` (« conserver les
montants et règles acceptés pour les opérations déjà engagées ; aucune réécriture d'historique »). En
revanche, un changement de taux modifie les contrôles comptables de `finance-summary`
(`platform_commission + driver_earnings == completed_fare_total`) pour les courses postérieures
seulement — à instruire avant l'arbitrage **P02 du 13 octobre**.

---

## 3. Arrivée, attente de prise en charge, démarrage

C'est la zone la plus divergente.

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-012` — le chauffeur **indique son arrivée**, validée si distance **< 50 m** du point de prise en charge | aucun statut d'arrivée dans `ALLOWED_TRANSITIONS` ; `driver_en_route → in_progress` directement (`entities.py:44-48`) ; aucun contrôle de distance | **écart structurel** |
| `PROD-012` — l'attente de prise en charge **démarre à l'arrivée**, avec **3 minutes gratuites** puis `montant = tarif × floor(max(0, t−180)/60)` | `waiting` n'est atteignable que depuis `in_progress` (`entities.py:49-54`) ; `start_waiting` exige `in_progress` sinon `409 WAITING_INVALID_RIDE_STATUS` (`services.py:378-380`) ; **aucune franchise** | **écart structurel** — l'attente du code est une attente *en course*, pas une attente de prise en charge |
| `go.pickup_wait_rate = 100` XOF/min | `waiting_price_per_minute_xof = 100` (`settings.py:129`) | **conforme** en valeur ; s'applique toutefois à l'attente en course |
| `PROD-026` — escale : **1 minute gratuite**, puis prorata **à la seconde** arrondi au franc | `add_stop` existe (`services.py:454`) ; la facturation d'attente est au tarif/minute sans franchise ni prorata seconde distinct par escale | **à vérifier** — lire `add_stop` et `_stop_waiting` en détail avant de conclure |
| `PROD-013` — démarrage autorisé si **proximité ≤ 10 m**, **deux positions ≤ 30 s**, **précision ≤ 10 m** | `update_status → in_progress` ne vérifie que l'acteur puis lance la trace DiddiMap (`services.py:316-318`) | **non implémenté** |
| `PROD-013` — **code de prise en charge à 6 chiffres**, usage unique, invalidé au démarrage ou à l'annulation, blocage après **5 essais**, recours tracé | aucune occurrence dans `app_base/modules/ride` | **non implémenté** |
| `PROD-012` — « le démarrage arrête le compteur » | `waiting → in_progress` via `PATCH /status` est **refusé** (`409 WAITING_STOP_ENDPOINT_REQUIRED`, `services.py:303-308`) ; la reprise passe par la route d'arrêt d'attente | **conforme** dans son propre modèle, mais sur l'attente en course |

Le code tolère la dérive GPS par un seuil de vitesse (`waiting_stationary_speed_threshold_kmh = 3.0`) et
refuse une télémétrie plus vieille que `waiting_telemetry_ttl_seconds = 30`. La cible, elle, raisonne en
**distance et précision**, pas en vitesse. Les deux approches répondent au même risque par des moyens
différents — ce n'est pas une simple différence de valeur.

---

## 4. Annulation et fin anticipée

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-014` — annulation **avant** début de course : **aucun frais**, attente acquise comprise | `cancel` ne produit aucune facturation (`services.py:519-553`) | **conforme** |
| `PROD-014` — **après démarrage = fin anticipée** : facturer le trajet effectué au barème accepté au départ, plus attente et suppléments acquis | annuler une course `in_progress` la termine en `cancelled_by_*` sans aucun calcul ; aucune notion de fin anticipée | **écart structurel** |
| `PROD-014` — gratuit si total **strictement inférieur** à `go.early_end_free_threshold = 300` XOF, **dû au seuil** | aucun seuil de ce type dans le code | **non implémenté** |
| `PROD-014` — **malus opérationnels non activés** au MVP | `_record_priority_outcome` applique `-3` points au moteur de priorité sur annulation chauffeur (`settings.py:75`, `services.py:546`) | **à vérifier** — un bonus de dispatch est-il un « malus opérationnel » au sens de `PROD-020` ? |
| `PROD-014` / `PROD-027` — après 10 min sans démarrage, le chauffeur déclare le client absent, annulation gratuite | `VALID_CANCEL_REASONS` existe et l'annulation est gratuite ; le délai de 10 min n'est pas visible côté serveur | **à vérifier** |
| L'annulation doit indiquer **qui**, **à quelle étape**, **quelles conséquences** | statut cible distinct passager/chauffeur, `cancellation_reason` persisté, historique de transitions avec métadonnées, `log_event("ride.cancelled", …)` | **conforme** |

---

## 5. Recherche et matching

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-027` — **3 phases** : 30 s/1 km → 60 s/3 km → 180 s/5 km | élargissement par **pas uniforme** `matching_search_radius_step_km = 2.0` jusqu'à `matching_search_radius_max_km = 15.0` (`settings.py:64-65`) | **écart de valeur** sur les rayons, **écart de modèle** sur la structure en phases nommées |
| `PROD-027` — durée totale **4 min 30** (270 s) | `matching_search_budget_seconds = 120` (`settings.py:66`) | **écart de valeur** |
| `PROD-027` — continuer à considérer les chauffeurs **proches devenus disponibles** pendant les phases suivantes | `_next_candidates` + `TRIED_KEY_PREFIX` ; couvert par `test_matching_wave_dynamics.py` | **conforme** |
| `PROD-027` — à épuisement, proposer une **nouvelle recherche explicite** | `_give_up` → `no_driver_found`, terminal ; le passager doit créer une nouvelle course | **conforme** côté serveur ; la proposition est un comportement client |
| Pas de double attribution, même sur acceptation tardive concurrente à l'expiration | claim Redis `SET NX` + contrainte base ; prouvé par `test_matching.py` | **conforme** |
| `PROD-015` — enregistrer les demandes de devis avec **références de déduplication**, une seule demande par passager dans 1 km / 20 min | `estimate_pricing` est **sans état** : rien n'est persisté, aucune référence de déduplication (`services.py:84-114`) | **non implémenté** |
| `PROD-015` — devis **valable 15 minutes**, rafraîchissement obligatoire au-delà | aucune expiration de devis ; aucune occurrence de `quote`, `valid_until` ou équivalent | **non implémenté** |

Nuance relevée dans le code, à porter à l'arbitrage : le classement par ETA DiddiMap **retombe
silencieusement sur l'ordre de distance** si DiddiMap est indisponible (`settings.py:54-57`). C'est le
seul repli silencieux assumé face à DiddiMap, et il concerne le classement, non l'estimation. À
rapprocher de la règle « une panne de source ne devient jamais un zéro » — ici il ne s'agit pas d'un KPI
mais d'un ordre de priorité, donc l'arbitrage reste ouvert → **à vérifier**.

---

## 6. Éligibilité et wallet chauffeur

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `go.online_min_balance` — **non fixé**, seuil d'éligibilité distinct du retrait | `driver_min_balance = 0` et `driver_max_estimated_commission = 0` → contrôles neutralisés (`settings.py:124-125`) | **conforme** — un seuil non fixé correspond à un contrôle neutre |
| `PROD-032` — retrait **sans minimum commercial**, frais déduits, **montant débité / frais / net affichés avant confirmation** | aucune route de retrait dans les 124 routes exposées | **non implémenté** |
| `PROD-003` — retrait **demandé par le professionnel dans l'application** au MVP | idem | **non implémenté** |
| Parcours cash : le chauffeur encaisse, **la commission due est enregistrée dans son wallet** | `POST /v1/payments/{ride_id}/confirm-cash` + `DriverWallet`, `Transaction`, `/v1/drivers/me/wallet/ledger` | **à vérifier** — lire `PaymentService.confirm_cash` pour confirmer le sens de l'écriture |
| Parcours numérique : **gains crédités à partir du résultat financier confirmé** | webhook DiddiPay + réconciliation périodique (`settings.py:146-156`) | **conforme** dans le principe |

---

## 7. Paiement

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-030` — paiement **après** réalisation ou fin anticipée | `POST /v1/payments/{ride_id}/prepare` puis confirmation ; distinction préparation / encaissement présente | **conforme** |
| `PROD-030` — en cas d'échec, conserver la somme due et **bloquer une nouvelle commande payante** jusqu'à régularisation | aucun blocage de ce type visible dans `request_ride` | **non implémenté** |
| `PROD-040` — impayés **cloisonnés par module** au lancement | DiddiGo ne consulte aucune dette d'un autre module ; la règle de non-lecture croisée l'interdit structurellement | **conforme** |
| `PROD-031` — bascule Mobile Money → espèces après confirmation, enregistrée serveur, deux parties notifiées | `confirm-cash` existe ; la bascule après un intent numérique confirmé reste à tracer | **à vérifier** |
| `PROD-031` — **détecter et signaler automatiquement** un succès numérique tardif après encaissement cash | `POST /v1/admin/payments/reconcile` et ses variantes + réconciliation automatique ; la qualification « doublon » n'est pas établie par lecture | **à vérifier** |
| `PROD-042` — remboursement cash par **voie numérique** vers bénéficiaire vérifié | pas de route de remboursement dans DiddiGo ; cohérent avec `PROD-034` qui place la décision au Backoffice | **conforme** par délégation |
| `PROD-034` — remboursement décidé au Backoffice, **validé par un administrateur** | aucune route de remboursement exposée par DiddiGo | **conforme** par délégation |

---

## 8. Identité, compte et continuité

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-007` — téléphone prioritaire, OTP par SMS ou WhatsApp, email en secours | `POST /v1/auth/otp/request` et `/verify`, `otp_rate_limit_seconds = 60`, `otp_code_lifetime_seconds = 300` | **conforme** sur la forme |
| Une panne SMS ne doit pas être présentée comme une erreur utilisateur | `# TODO: replace with real SMS delivery. In dev, the OTP is logged.` (`auth/application/services.py`) — **aucun fournisseur SMS branché** | **non implémenté** |
| Identité unique DiddiFreeID, `user_id = sub` du JWT | vérification RS256 via JWKS, `identity_issuer = diddifree-id`, utilisateur fantôme `auth.users` conservé | **conforme** |
| `PROD-011` — la reprise **ne crée pas** une nouvelle mission et **ne réinitialise pas** le compteur d'attente | état lu depuis la base, `waiting_started_at` persisté, finalisation idempotente (`SCRUM-438`, terminé) | **conforme** |
| L'activation métier ne résulte pas de la seule création du compte Identity | `DriverService.get_capabilities` + projection `operational_status` vers DiddiFreeID ; KYC chauffeur et KYV véhicule distincts | **conforme** |
| Une nouvelle tentative après problème réseau **ne répète pas la mutation** | `S2SCommandStore` Redis (`reserve`/`complete`/`release`), TTL 24 h sur KYC et provisioning | **conforme** |

**Signalé par Jira, pas par ma lecture du code** : `SCRUM-565` (ouvert) indique que
`/v1/auth/otp/verify` émet un **jeton HS256 local rejeté par les routes protégées**, alors que l'identité
de référence est DiddiFreeID en RS256. Si ce diagnostic est exact, le parcours « créer son compte et
accéder au service » est rompu de bout en bout malgré des routes présentes. **À vérifier en staging** —
je n'ai pas exécuté de test.

---

## 9. Pilotage et observabilité

| Règle cible | Code | Verdict |
| --- | --- | --- |
| `PROD-010` — statistiques de base par module au MVP | 5 routes `/internal/pilotage/*` + breakdown 4 dimensions | **conforme** |
| « En cas de panne, indiquer une indisponibilité ou une donnée ancienne **plutôt qu'un résultat artificiellement nul** » | `health-summary` publie `freshness_window_seconds: 60` ; `finance-summary` et `daily-summary` **n'exposent aucun bloc `freshness`** (`summary_schemas.py:39-48`) | **non implémenté** sur les résumés de données |
| Indicateurs MVP proposés : volumes, taux d'achèvement et d'échec, montants, commissions, retraits en attente, dettes cash, tickets non résolus | 16 métriques finance + daily-summary ; **retraits en attente** et **tickets non résolus** hors périmètre DiddiGo | **à vérifier** avec Pilotage |
| `PROD-010` — reporting détaillé et ventilé en **V1** | `/internal/pilotage/breakdown` livre une ventilation par heure, moyen de paiement, type de service, statut final | **hors MVP, présent** |
| `PROD-010` — **export comptable Odoo** au MVP | aucune route ni client Odoo dans DiddiGo ; le contrat place la réconciliation chez Pilotage/Odoo | **conforme** par délégation |
| Un identifiant de mission doit permettre de retrouver le parcours entre modules | `current_request_id`, `log_event` sur 128 sites, recherche de logs Loki, `GET /v1/admin/logs/rides/{ride_id}` | **conforme** |
| `PROD-038` — GPS détaillé conservé **30 jours** puis agrégation | `ride_summary_max_age_days = 31` borne les rapports, mais **aucune purge** des traces trouvée | **non implémenté** |

---

## 10. Périmètre : ce que le code porte hors MVP

| Élément du code | Phase cible | Verdict |
| --- | --- | --- |
| `/internal/pilotage/breakdown` — ventilation par dimension | V1 (`PROD-010`, reporting ventilé) | **hors MVP, présent** |
| Module `partner` complet — 15 routes, `Partner`, `PartnerMember`, `PartnerDriverLink`, affectation de véhicules | V1 (`PROD-001`, partenaires et flottes) | **hors MVP, présent** |
| Moteur de priorité chauffeur avec points et malus | à rapprocher de `PROD-020` (score opérationnel, V1) | **à vérifier** |

Porter quelque chose en avance n'est pas un défaut. C'est un constat utile pour le gel du code du
18 novembre : ces surfaces existent et seront exposées, qu'elles soient ou non dans le périmètre
commercial annoncé.

---

## 11. Ce que le code n'a pas et que la cible ne demande pas au MVP

Pour mémoire, afin que ces absences ne soient pas relues comme des manques : course programmée
(Later, `PROD-016`), tarification par zone (V1), messagerie en course (V1), reçu client (V1,
`PROD-045`), carte bancaire (V1), fidélité et parrainage (V1), DiddiScore avec effets (V1), carte des
zones de demande (Later), retrait initié par le Backoffice (Later).

---

## 12. Ce qui reste à instruire

Par ordre de conséquence, sans recommandation d'action :

1. **Taux de commission 8 % vs 18 %** — impact direct sur les gains chauffeur et sur les contrôles
   comptables de `finance-summary`. À articuler avec l'arbitrage **P02 du 13 octobre** sur les seuils et
   commissions métiers.
2. **Le bloc arrivée / attente de prise en charge / fin anticipée** — trois écarts structurels sur le
   même périmètre, correspondant à `BE015` (MVP P0, fenêtre 14→23 oct, *à engager*). Ce n'est pas un
   réglage de paramètre : la machine à états n'a pas de statut d'arrivée.
3. **`SCRUM-565`** — si le jeton d'OTP est bien rejeté par les routes protégées, le parcours d'entrée est
   rompu. À reproduire en staging avant toute autre priorisation.
4. **Paramètres de recherche** — rayons et budget. Modification de configuration, pas de code, si le
   modèle en pas uniforme est jugé acceptable face aux trois phases nommées de `PROD-027`.
5. **Devis sans état** — ni expiration à 15 min, ni références de déduplication. Deux exigences
   explicites de `PROD-015` au MVP.
6. **Absence de fournisseur SMS** — le `TODO` dans `AuthService` signifie qu'aucun OTP n'est délivré en
   production.
7. **Pas de route de retrait** — `PROD-003` et `PROD-032` placent le retrait demandé dans l'application
   au MVP.
8. **`freshness` absent des résumés Pilotage** — la règle « jamais un zéro artificiel » n'est pas honorée
   sur les données, seulement sur la santé.
9. **Pas de purge des traces GPS à 30 jours** — `PROD-038`, sous validation juridique par ailleurs.
10. **Pas de blocage de nouvelle commande payante sur impayé** — `PROD-030`.

Les cinq lignes **à vérifier** du document nécessitent soit une lecture de code plus fine
(`add_stop`/`_stop_waiting`, `confirm_cash`), soit un arbitrage produit (malus vs bonus de dispatch,
multiplicateur manuel, repli silencieux du classement ETA), soit un test en staging. Aucune n'a été
tranchée ici.
