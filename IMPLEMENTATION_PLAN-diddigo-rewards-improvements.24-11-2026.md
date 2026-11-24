# Plan d’implémentation — DiddiGo Rewards : améliorations post-recette
Statut : VALIDÉ
Date : 2026-11-24
Branche du run : codex/diddigo-rewards-improvements-2026-11-24

## 1. Objectif et périmètre

- Inclus dans le MVP : fiabiliser la libération des avantages réservés quand une course ne trouve pas de chauffeur ou est annulée, transmettre la date d’expiration de la réservation, exposer clairement le montant brut, la remise et le montant payable, définir le traitement de la réconciliation après paiement, et préparer la validation de la télémétrie Rewards. (source : `C:\Users\Vanauld\Downloads\2026-11-24-message-equipe-diddigo.md`, sections « Remaining improvements » et « Observability`)
- Inclus dans le MVP : conserver la résilience actuelle : une indisponibilité de DiddiRewards ne doit pas bloquer la course ou le paiement. (source : `app_base/modules/ride/application/services.py`, `create_quote` et `request_ride` ; `app_base/modules/payment/application/services.py`, `_confirm_rewards_if_needed` et `_correct_rewards_if_needed`)
- Exclu du MVP : modifier la logique de recherche de chauffeur ou ajouter une nouvelle vague de matching ; le comportement actuel et le budget sont documentés. (source : `app_base/core/settings.py`, `matching_search_budget_seconds` ; `app_base/modules/ride/application/matching_service.py`, `search_budget_exceeded`)
- Exclu du MVP : modifier la propriété des campagnes, des paiements ou des bases Rewards. (source : contrat Rewards v1, sections « ownership » et « Campaigns »)
- Exclu du MVP : redeployer Portainer ou modifier DiddiRewards/DiddiObserve. (source : demande utilisateur du 24-11-2026 ; message équipe, section « Observability »)

## 2. Architecture retenue

DiddiGo reste propriétaire de la course, du tarif et du paiement. DiddiRewards reste propriétaire des avantages, réservations, consommations et corrections. DiddiGo appelle les adaptateurs HTTP Rewards pour le devis et la réservation, puis utilise le paiement confirmé et l’outbox pour transmettre les événements sur le stream Redis configuré. (source : contrat Rewards v1, sections « ownership », « lifecycle » et « events » ; `app_base/modules/ride/infra/diddirewards_client.py` ; `app_base/modules/payment/application/rewards_events.py`)

Le paiement client est calculé à partir du tarif brut diminué de la remise Rewards, tandis que la confirmation Rewards reçoit les montants de paiement, de remise et de paiement chauffeur. (source : `app_base/modules/payment/application/services.py`, `_client_payable_amount` et `_confirm_rewards_if_needed`)

## 3. Décisions figées

| ID | Décision | Source |
|---|---|---|
| D01 | L’environnement de référence de DiddiGo est `stage`; le run part de `origin/stage`. | Utilisateur, 2026-11-24 ; `git log`, révision `703c15a` |
| D02 | Toute opération Rewards distante utilise le client S2S DiddiGo, les scopes dédiés, un `X-Request-ID` et une clé d’idempotence lorsque le contrat l’exige. | `app_base/modules/ride/infra/diddirewards_client.py` ; `app_base/core/settings.py`, paramètres Rewards |
| D03 | Une panne Rewards dégrade la fonctionnalité Rewards mais ne bloque pas la course ni le paiement. | `app_base/modules/ride/application/services.py` ; `app_base/modules/payment/application/services.py` ; commit `2d3678e` |
| D04 | Les événements sont persistés dans l’outbox avant livraison Redis et livrés par lots avec retry borné. | `app_base/modules/payment/infra/models.py`, `rewards_event_outbox` ; `app_base/modules/payment/application/rewards_events.py` |
| D05 | Le montant affiché au client et au chauffeur doit permettre de régler le montant après remise, sans remplacer le tarif brut. | Message équipe DiddiGo, section « Cash amount invisible » ; `app_base/modules/payment/application/services.py`, `_client_payable_amount` |
| D06 | DiddiRewards doit exposer un endpoint de release pour annuler une réservation non consommée. | Utilisateur, 2026-11-24 |
| D07 | La réconciliation automatique est portée par l’outbox/worker avec idempotence ; la route admin reste le secours manuel. | Utilisateur, 2026-11-24 |
| D08 | Une réservation non consommée est libérée ; une consommation déjà confirmée est corrigée. | Utilisateur, 2026-11-24 |
| D09 | La configuration DiddiObserve déjà implémentée est conservée ; la validation centrale porte sur la réception effective des signaux. | Utilisateur, 2026-11-24 |

## 4. Contrats avec les autres services

| Service | Ce qu’on attend (endpoints, événements) | État : existe / à créer / à valider | Source |
|---|---|---|---|
| DiddiRewards | Quote, reserve avec `expires_at`, confirm, correct, reconciliation ; scopes S2S DiddiGo. | Existe ; release à valider | `app_base/modules/ride/infra/diddirewards_client.py` ; OpenAPI Rewards staging, endpoints d’intégration |
| DiddiRewards | Créer `POST /internal/v1/rewards/integrations/diddigo/benefits/release` pour libérer une réservation non consommée, avec `reservation_id`, `ride_id` et `reason`. | À créer | Utilisateur, 2026-11-24 ; message équipe DiddiGo, section « Reservation never released » |
| DiddiRewards | Stream Redis `diddigo.events.v1`, événements `ride.payment_confirmed`, `ride.refunded`, `ride.cancelled`, déduplication par `event_id`/`operation_id`. | Existe côté protocole ; réception centrale à valider | Contrat Rewards v1, section « events » ; `app_base/modules/payment/application/rewards_events.py` |
| DiddiPay | Paiement confirmé avec montant payable net et référence de paiement. | Existe | `app_base/modules/payment/application/services.py`, préparation cash et confirmation Rewards |
| DiddiObserve | Collecteur OTLP opérationnel, URL et authentification valides pour DiddiGo. | À fournir/valider par plateforme | Message équipe DiddiGo, section « Observability » |

## 5. Déjà fait (ne pas refaire)

- Adaptateur HTTP DiddiRewards pour quote, reserve, confirm, correct et reconciliation, avec authentification S2S, timeout et idempotence. (source : `app_base/modules/ride/infra/diddirewards_client.py`)
- Persistance des données Rewards sur les devis et les courses, avec migrations déjà présentes. (source : `app_base/modules/ride/domain/entities.py`, `app_base/modules/ride/infra/models.py`, migrations `2026_11_23-b2c3d4e5f6a7_diddirewards_ride_context.py` et `2026_11_23-c3d4e5f6a7b8_diddirewards_consumption.py`)
- Réservation à la création de course, confirmation après paiement, correction après remboursement/annulation et route d’administration de réconciliation. (source : `app_base/modules/ride/application/services.py` ; `app_base/modules/payment/application/services.py` ; `app_base/modules/payment/presentation/router.py`)
- Outbox transactionnelle et worker de livraison Redis avec retry borné. (source : commits `c015530`, `e1c7785`, `app_base/modules/payment/application/rewards_events.py`)
- Résilience du devis et correction des scopes S2S. (source : commit `2d3678e`, merge `703c15a`)
- Raccordement du conteneur DiddiGo au réseau Redis externe prévu. (source : commit `aa70967`, `docker-compose.portainer.yml`)

## 6. Phases

### P0 — Figer les contrats externes

- Objectif : disposer d’un contrat Rewards non ambigu avant toute modification de code.
- Dépend de : contrat de release et décision de réconciliation.
- Contenu : spécifier l’endpoint `POST /internal/v1/rewards/integrations/diddigo/benefits/release`, son payload, ses statuts et son idempotence ; spécifier la réconciliation automatique par outbox/worker ; reprendre la configuration DiddiObserve déjà implémentée. (source : Utilisateur, 2026-11-24 ; message équipe DiddiGo ; contrat Rewards v1)
- Hors de cette phase : aucune modification de code ni déploiement.
- Critères de fin : contrat écrit ou OpenAPI accessible contenant release, expiration et réconciliation ; réponses d’erreur attendues documentées ; configuration DiddiObserve existante référencée sans modification.
- Risques : implémenter un chemin d’URL ou une sémantique de correction incorrecte.

### P1 — Libérer les réservations non consommées

- Objectif : empêcher qu’une réservation Rewards reste bloquée après absence de chauffeur ou annulation.
- Dépend de : P0.
- Contenu : ajouter l’appel de release dans le client et les transitions `no_driver_found`, `cancelled_by_passenger`, `cancelled_by_driver` ; transmettre `expires_at` lors de la réservation ; rendre l’appel idempotent et résilient ; journaliser le statut Rewards sans secret. (source : message équipe DiddiGo, section « Reservation never released » ; `app_base/modules/ride/application/services.py`, `request_ride` et `cancel` ; `app_base/modules/ride/application/matching_service.py`, `_give_up`)
- Hors de cette phase : correction d’une consommation déjà confirmée ; elle relève de la correction financière. (source : contrat Rewards v1, section « lifecycle »)
- Critères de fin : tests unitaires couvrant les trois motifs, test de retry/indisponibilité, vérification que la course reste cohérente et qu’aucune release n’est envoyée après consommation confirmée.
- Risques : double libération ou libération après paiement ; utiliser une clé d’idempotence déterministe par course et opération.

### P2 — Rendre le montant payable visible

- Objectif : permettre au passager et au chauffeur de connaître le montant cash réellement attendu.
- Dépend de : aucune dépendance externe bloquante.
- Contenu : enrichir le détail de course et les réponses de paiement avec `discount_amount_minor` et `client_payable_amount`, en conservant `final_fare` comme montant brut ; appliquer les règles de visibilité aux rôles passager et chauffeur. (source : message équipe DiddiGo, section « Cash amount invisible » ; `app_base/modules/ride/application/services.py`, `_ride_detail_payload` ; `app_base/modules/payment/application/services.py`, `_client_payable_amount`)
- Hors de cette phase : changement de tarification, de commission ou de payout chauffeur. (source : `app_base/modules/ride/application/services.py`, calcul du tarif final ; contrat Rewards v1)
- Critères de fin : tests API passager/chauffeur vérifiant les trois montants ; test cash vérifiant que le montant attendu est le montant net ; test d’absence de remise conservant le comportement actuel.
- Risques : exposer une information à un rôle non autorisé ou diverger entre affichage et montant encaissé.

### P3 — Automatiser la réconciliation sans double comptage

- Objectif : traiter les confirmations/corrections Rewards non abouties sans dépendre exclusivement de l’action admin.
- Dépend de : P0 ; P1 pour les annulations non consommées ; P2 pour la cohérence des montants.
- Contenu : utiliser l’outbox/worker comme mécanisme automatique principal ; réutiliser l’idempotence existante ; compléter l’outbox ou le worker pour les cas de confirmation/correction différée ; conserver la route admin comme reprise opérateur. (source : Utilisateur, 2026-11-24 ; message équipe DiddiGo, section « Rewards reconciliation only manual » ; `app_base/modules/payment/application/services.py`, `reconcile_rewards` ; `app_base/modules/payment/application/rewards_events.py` ; contrat Rewards v1, section « reconciliation »)
- Hors de cette phase : modification de la comptabilité ou correction automatique d’un montant non confirmé par une règle externe. (source : contrat Rewards v1, section « reconciliation is append-only »)
- Critères de fin : test de panne Rewards puis reprise ; une confirmation/correction est rejouée sans doublon ; l’état local et l’identifiant de consommation/correction sont persistés ; la route admin reste fonctionnelle.
- Risques : deux chemins concurrents peuvent produire des opérations redondantes ; l’idempotency-key et la déduplication événementielle doivent être testées ensemble.

### P4 — Valider le raccordement d’observabilité et la recette staging

- Objectif : distinguer les preuves locales des preuves nécessitant les plateformes centrales.
- Dépend de : P1 à P3 ; endpoint DiddiObserve fourni.
- Contenu : vérifier l’export des logs/traces Rewards et l’absence de secrets ; vérifier les signaux de release, paiement, retry et échec ; exécuter une course promotionnelle non destructive et relever request-id/trace-id ; faire confirmer la réception dans Loki/Tempo. (source : message équipe DiddiGo, sections « Observability » et « Validation » ; protocole Diddi Observability v1)
- Hors de cette phase : redéploiement Portainer par ce run.
- Critères de fin : tests locaux verts ; test staging avec course complète ; preuve Loki/Tempo fournie par DiddiObserve ; aucune panne collecteur ne bloque une opération métier.
- Risques : le collecteur actuellement signalé indisponible empêche la validation centrale, sans empêcher la validation locale.

## 7. Questions ouvertes

Aucune. Les décisions ont été fournies par l’utilisateur le 2026-11-24.

## 8. Contradictions entre sources

Aucune après les décisions de l’utilisateur du 2026-11-24. L’endpoint `release` et le mécanisme automatique par outbox/worker deviennent des éléments à créer dans les phases P0 à P3.

## 9. Critère de fin du plan entier

Le plan sera considéré terminé lorsque les décisions ouvertes seront répondues, le document passera à `VALIDÉ`, les phases P1 à P4 auront des critères de test vérifiés, et la validation centrale aura explicitement confirmé la réception des logs/traces et la cohérence du parcours devis → réservation → course → paiement → événement/réconciliation. (source : demande utilisateur du 24-11-2026 ; message équipe DiddiGo, section « Validation »)
