# Questions de préparation — 2026-11-24

## Résolution

Les questions redondantes ont été retirées après clarification utilisateur. L’agent applique le contrat prudent suivant : `204` idempotent en succès, `409` si la réservation est consommée, `404` si elle est inconnue, et indisponibilité Rewards non bloquante.

Ces questions ne remettent pas en cause les décisions déjà validées. Elles précisent uniquement les parties du contrat externe qui ne sont pas présentes dans le dépôt DiddiGo.

## Q1 — Périmètre de création du endpoint release

Contexte : le plan est limité à DiddiGo, mais l’endpoint `release` doit être servi par DiddiRewards.

- Option A — DiddiGo crée son client, sa documentation et son faux adaptateur ; DiddiRewards implémentera le endpoint dans son propre dépôt. **Recommandé.**
- Option B — modifier aussi le dépôt DiddiRewards dans ce run.
- Option C — ne coder que l’interface et attendre l’implémentation externe.

## Q2 — Réponse et idempotence du endpoint release

Contexte : l’URL et le payload sont décidés, mais le statut de réponse et le comportement d’une répétition ne sont pas documentés.

- Option A — `200` ou `204` pour une libération réussie ; répétition idempotente ; réservation déjà consommée renvoyée comme conflit métier. **Recommandé.**
- Option B — `202` asynchrone, avec statut à consulter.
- Option C — laisser DiddiRewards choisir sans contrat côté DiddiGo.

## Q3 — Rôle exact de la réconciliation automatique

Contexte : DiddiGo possède déjà un appel HTTP de confirmation/correction et un outbox qui publie les événements vers Rewards.

- Option A — garder les appels HTTP directs pour confirmation/correction, puis utiliser l’outbox/worker pour les événements et les reprises ; route admin en dernier recours. **Recommandé.**
- Option B — supprimer les appels directs et rendre le stream Redis seul responsable de la confirmation/correction.
- Option C — ajouter un second worker HTTP indépendant qui rejoue toutes les opérations.
