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
| Portail MkDocs | [docs-go-staging.diddifree.com](https://docs-go-staging.diddifree.com/) |

Le portail est publie par une stack Docker distincte. Sa disponibilite est
verifiee apres chaque deploiement Portainer ; sa configuration est documentee
dans le [guide de publication](../configuration/DOCUMENTATION_PORTAL.md).

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

## Nouvelles lectures de reprise

- `GET /v1/rides/active/current` restaure la course non terminee du passager ou du chauffeur. Un `404 ACTIVE_RIDE_NOT_FOUND` signifie qu'il n'y a rien a reprendre.
- `GET /v1/passenger/debts/{debt_id}` relit une dette precise apres un retour Mobile Money. DiddiGo expose son etat metier ; DiddiPay reste la source de verite fournisseur.
- `GET /v1/pro/metiers` est une vue **DiddiGo locale** du profil professionnel chauffeur. Elle ne remplace pas la future agregation DiddiFree Pro/DiddiFreeID.
