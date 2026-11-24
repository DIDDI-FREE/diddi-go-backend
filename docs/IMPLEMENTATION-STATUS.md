# État d’implémentation — DiddiGo Rewards

Date de démarrage : 2026-11-24  
Branche : `codex/diddigo-rewards-improvements-2026-11-24`  
Plan : `IMPLEMENTATION_PLAN-diddigo-rewards-improvements.24-11-2026.md` à la racine du dépôt.

## État global

Les phases d’implémentation P0 à P3 sont terminées. P4 est terminée pour les vérifications locales et reste en attente pour les validations de déploiement et d’intégration externes.

## Vérifications du projet

Commandes définies par `README.md`, `pyproject.toml` et `.github/workflows/tests.yml` :

```powershell
.venv\Scripts\ruff check app_base alembic tests
.venv\Scripts\python.exe -m compileall -q app_base alembic tests
.venv\Scripts\python.exe -m pytest -m unit -q
.venv\Scripts\python.exe -m pytest -q
```

Après toute modification de contrat HTTP/WebSocket :

```powershell
.venv\Scripts\python.exe tools\generate_api_contract.py
```

Les migrations seront vérifiées avec Alembic dans la phase concernée, en fonction de la disponibilité de PostgreSQL.

## Phases

| Phase | État | Notes |
|---|---|---|
| P0 | TERMINÉE | Contrat release et mécanisme outbox documentés |
| P1 | TERMINÉE | Client release, expiration, matching et annulation couverts |
| P2 | TERMINÉE | Détail course et réponses paiement enrichis |
| P3 | TERMINÉE | Outbox/worker conservés, identifiants d’événements affinés |
| P4 | EN ATTENTE DE DÉPLOIEMENT | Vérifications locales terminées ; validation centrale non exécutée |

## Vérifications de déploiement en attente

- Aucun redéploiement n’est effectué par ce run.
- Vérifier après déploiement que DiddiRewards expose le endpoint release convenu.
- Vérifier que le stream Redis configuré reçoit les événements et que le consumer Rewards les traite.
- Exécuter une course promotionnelle non destructive et vérifier devis, réservation, paiement, release/correction et montant payable.
- Faire confirmer par DiddiObserve la réception corrélée dans Loki et Tempo.
- Exécuter la suite non-unitaire dans un environnement PostgreSQL/Redis disponible ; elle n’a pas pu terminer localement.
