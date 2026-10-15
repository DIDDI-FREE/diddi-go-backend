# API DiddiGo

La documentation API repose sur deux niveaux complémentaires :

- le portail MkDocs explique les parcours, règles métier, permissions et intégrations ;
- FastAPI publie la spécification exacte des routes et schémas déployés.

## Environnements

| Ressource | Staging |
|---|---|
| Swagger UI | [go-staging.diddifree.com/docs](https://go-staging.diddifree.com/docs) |
| OpenAPI JSON | [go-staging.diddifree.com/openapi.json](https://go-staging.diddifree.com/openapi.json) |
| Health | [go-staging.diddifree.com/health](https://go-staging.diddifree.com/health) |

## Surfaces

| Surface | Préfixe | Consommateur |
|---|---|---|
| Publique | `/v1/*` | Applications passager et chauffeur |
| Backoffice | `/v1/admin/*` | Administration et support |
| Service-to-service | `/internal/*` | Services DiddiFree autorisés |
| Temps réel | `/v1/ws` | Applications authentifiées |

!!! warning "Version déployée"
    Le contrat réellement disponible dans un environnement est toujours celui de son endpoint `openapi.json`. Une fonctionnalité documentée localement mais absente de cet endpoint n'est pas encore déployée.

## Maintenance

Après toute modification de route ou de schéma :

```bash
python tools/generate_api_contract.py
mkdocs build --strict
```

Le changelog du jour et le guide métier concerné doivent être mis à jour dans la même pull request.
