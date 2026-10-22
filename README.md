# DiddiGo

Backend FastAPI modulaire pour le service de course DiddiGo. La version applicative et les dépendances sont définies dans [`pyproject.toml`](pyproject.toml) ; la surface HTTP est générée par l'application elle-même.

## Documentation active

- Portail staging : [docs-go-staging.diddifree.com](https://docs-go-staging.diddifree.com/)
- [Contrat HTTP et WebSocket](docs/api/API_CONTRACT.md)
- [OpenAPI](docs/api/openapi.yaml), [AsyncAPI](docs/api/asyncapi.yaml) et [questions ouvertes](docs/api/open-questions.md)
- [MVP figé](docs/product/DIDDIGO-MVP-FIGE.md)
- [Brief frontend du 10 octobre 2026](docs/frontend/DIDDIGO_FRONTEND_BRIEF_2026-10-10.md)
- [Architecture d'exécution](docs/architecture/RUNTIME_ARCHITECTURE.md)
- [Référence de configuration](docs/configuration/CONFIGURATION_REFERENCE.md)

Les notes, briefs et contrats précédents sont conservés dans [`docs/archive/2026-10-10-pre-code-derived-regeneration`](docs/archive/2026-10-10-pre-code-derived-regeneration).

Le portail est un service Docker distinct : le guide de publication locale et
Portainer est dans [`docs/configuration/DOCUMENTATION_PORTAL.md`](docs/configuration/DOCUMENTATION_PORTAL.md).

## Contrat API

Le contrat est centralisé dans `docs/api/`. Les spécifications sont dérivées du code et enrichies par le générateur documentaire :

```powershell
.venv\Scripts\python.exe tools\generate_api_contract.py
```

Cette commande régénère les deux YAML et les blocs d'inventaire du contrat et des questions ouvertes, sans écraser les décisions humaines. Exécuter la commande après toute modification HTTP ou WebSocket. Le JSON servi à `/openapi.json` reste un export runtime distinct ; ses écarts sont suivis dans les questions ouvertes.

## Vérification locale

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\ruff check .
```
