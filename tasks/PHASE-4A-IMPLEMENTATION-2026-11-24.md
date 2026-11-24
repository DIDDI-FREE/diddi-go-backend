# Journal P4-A — Vérifications locales

- État : TERMINÉ
- `ruff check app_base alembic tests` : vert.
- `python -m compileall -q app_base alembic tests` : vert.
- `python -m pytest -m unit -q` : 453 passés, 176 deselected.
- `tools/generate_api_contract.py` : exécuté ; contrats API régénérés.
- `pytest -m "not unit"` : non terminé localement, car l’environnement d’intégration externe n’est pas disponible et le processus reste sans sortie ; interrompu sans modifier le code.
