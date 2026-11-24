# Suivi d’implémentation — DiddiGo Rewards

Branche du run : `codex/diddigo-rewards-improvements-2026-11-24`
Référence : `IMPLEMENTATION_PLAN-diddigo-rewards-improvements.24-11-2026.md`

## Phases

- [ ] P0 — Figer les contrats externes
  - [ ] P0-A — Contrat release DiddiRewards
  - [ ] P0-B — Contrat de réconciliation et vérification de la configuration existante
- [ ] P1 — Libérer les réservations non consommées
  - [ ] P1-A — Client release et expiration
  - [ ] P1-B — Intégration aux transitions d’annulation et de matching
  - [ ] P1-C — Tests de résilience et d’idempotence
- [ ] P2 — Rendre le montant payable visible
  - [ ] P2-A — Contrat de réponse détail de course
  - [ ] P2-B — Réponses paiement/cash
  - [ ] P2-C — Tests de visibilité par rôle
- [ ] P3 — Automatiser la réconciliation sans double comptage
  - [ ] P3-A — Flux automatique de confirmation/correction
  - [ ] P3-B — Déduplication, reprise et route admin
  - [ ] P3-C — Tests de panne et reprise
- [ ] P4 — Valider l’observabilité et la recette staging
  - [ ] P4-A — Vérifications locales
  - [ ] P4-B — Préparation de la recette staging
  - [ ] P4-C — Vérification centrale Loki/Tempo en attente de plateforme

## Idées hors plan

- Aucune.

## Blocages et attentes

- Les réponses aux questions de `tasks/QUESTIONS-2026-11-24.md` sont attendues avant le premier commit d’implémentation.
- La validation Loki/Tempo dépend de la plateforme centrale et ne sera pas déclarée localement.
