# Décisions — DiddiGo Rewards

## Décisions figées du plan

### D-01 — Branche de référence DiddiGo
- Date : 2026-11-24
- Phase / sous-lot : P0
- Décision : utiliser `stage` comme branche de référence DiddiGo et partir de `origin/stage`.
- Pourquoi : le dépôt DiddiGo utilise `stage` comme niveau de référence pour ce travail.
- Alternatives écartées : `main` comme base de ce run.
- Source : Utilisateur
- Impact : Git et branche `codex/diddigo-rewards-improvements-2026-11-24`.

### D-02 — Authentification Rewards
- Date : 2026-11-24
- Phase / sous-lot : P0
- Décision : utiliser le client S2S DiddiGo, les scopes dédiés, `X-Request-ID` et l’idempotence lorsque requise.
- Pourquoi : le contrat Rewards et le client existant imposent une authentification de service.
- Alternatives écartées : clé utilisateur ou authentification navigateur.
- Source : Plan ; code existant `app_base/modules/ride/infra/diddirewards_client.py`.
- Impact : client Rewards, tests et configuration.

### D-03 — Résilience Rewards
- Date : 2026-11-24
- Phase / sous-lot : P0
- Décision : une indisponibilité de DiddiRewards ne bloque ni la course ni le paiement.
- Pourquoi : le comportement de dégradation est déjà codé et constitue une contrainte du plan.
- Alternatives écartées : rendre Rewards bloquant.
- Source : Plan ; commit `2d3678e`.
- Impact : quote, réservation, paiement et worker.

### D-04 — Outbox et livraison Redis
- Date : 2026-11-24
- Phase / sous-lot : P0
- Décision : persister les événements dans l’outbox puis les livrer par lots avec retry borné.
- Pourquoi : c’est le mécanisme existant et résilient du module.
- Alternatives écartées : publication Redis synchrone dans la transaction métier.
- Source : Plan ; commits `c015530`, `e1c7785`.
- Impact : paiement, worker Rewards et Redis.

### D-05 — Montants exposés
- Date : 2026-11-24
- Phase / sous-lot : P2
- Décision : exposer le tarif brut, la remise et le montant payable net au passager et au chauffeur autorisés.
- Pourquoi : le chauffeur doit connaître le montant cash après remise, sans perdre le tarif brut.
- Alternatives écartées : remplacer `final_fare` par le montant net ; masquer la remise.
- Source : Plan ; message équipe DiddiGo, section « Cash amount invisible ».
- Impact : détail de course et paiement cash.

### D-06 — Endpoint release à créer
- Date : 2026-11-24
- Phase / sous-lot : P0/P1
- Décision : créer le contrat `POST /internal/v1/rewards/integrations/diddigo/benefits/release` avec `reservation_id`, `ride_id` et `reason`.
- Pourquoi : une réservation non consommée doit être libérée après absence de chauffeur ou annulation.
- Alternatives écartées : attendre seulement l’expiration ; corriger une consommation qui n’existe pas.
- Source : Utilisateur ; message équipe DiddiGo, section « Reservation never released ».
- Impact : contrat externe, client DiddiRewards, annulation et matching.

### D-07 — Réconciliation automatique
- Date : 2026-11-24
- Phase / sous-lot : P3
- Décision : utiliser l’outbox/worker comme mécanisme automatique principal et conserver la route admin comme secours.
- Pourquoi : réduire les reprises manuelles tout en gardant une intervention opérateur.
- Alternatives écartées : route admin uniquement ; appel synchrone bloquant.
- Source : Utilisateur ; plan.
- Impact : paiement, outbox, worker et administration.

### D-08 — Release ou correction
- Date : 2026-11-24
- Phase / sous-lot : P1/P3
- Décision : release avant consommation ; correction après consommation confirmée.
- Pourquoi : une réservation non consommée est un hold à annuler, tandis qu’une consommation confirmée est une opération financière append-only.
- Alternatives écartées : correction systématique ; attente systématique de l’expiration.
- Source : Utilisateur ; contrat Rewards v1.
- Impact : cycle de vie Rewards et traitement des annulations/remboursements.

### D-09 — Observabilité existante
- Date : 2026-11-24
- Phase / sous-lot : P4
- Décision : conserver la configuration DiddiObserve déjà implémentée et ne pas modifier la plateforme centrale.
- Pourquoi : ce run valide le raccordement ; il ne redéploie pas Portainer ni DiddiObserve.
- Alternatives écartées : changer l’URL sans nouvelle valeur centrale ; déclarer l’ingestion validée localement.
- Source : Utilisateur ; protocole Diddi Observability v1.
- Impact : configuration et recette staging.

## Décisions d’exécution

### D-10 — Contrat de réponse release
- Date : 2026-11-24
- Phase / sous-lot : P0-A
- Décision : le nouvel endpoint `POST /internal/v1/rewards/integrations/diddigo/benefits/release` utilise `204` en succès, est idempotent, renvoie `409` si la réservation est déjà consommée et `404` si elle est inconnue. Une indisponibilité Rewards reste non bloquante pour DiddiGo.
- Pourquoi : ce contrat est simple, réversible et compatible avec le cycle de vie déjà décidé.
- Alternatives écartées : réponse asynchrone `202` ; absence de contrat de statut.
- Source : Agent, à valider ; utilisateur a demandé l’implémentation autonome le 2026-11-24.
- Impact : client Rewards, contrat d’intégration, tests et traitement des erreurs.
