# Architecture d'exécution DiddiGo

**Sources :** `app_base/main.py`, `app_base/core/lifespan.py`, `app_base/core/auth_deps.py`, `app_base/core/settings.py`.
Ce document décrit l'implémentation présente dans ce dépôt ; il ne définit pas de fonctionnalités produit nouvelles.

## Entrée HTTP

`app_base.main:app` crée l'application FastAPI, applique CORS, logs structurés et gestion d'erreurs, puis monte les routeurs. Les endpoints d'infrastructure sont :

- `GET /health` : disponibilité du processus ;
- `GET /ready` : disponibilité PostgreSQL et Redis ;
- `GET /metrics` : métriques Prometheus, hors OpenAPI.

L'inventaire des opérations HTTP est généré dans le [contrat API](../api/API_CONTRACT.md#inventaire-http).

## Modules exposés

| Module | Responsabilité exposée |
|---|---|
| Auth et notifications | OTP, session, appareils et notifications push. |
| Ride | recherche de lieux, devis, course, matching, chauffeur, véhicule, WebSocket, résumé et endpoints internes. |
| Payment | paiement, callbacks, retours navigateur, wallet chauffeur et administration financière. |
| Partner | partenaires, flottes, véhicules et administration associée. |
| Observability | recherche de logs et diagnostics administratifs. |

Les routeurs sont montés explicitement dans `app_base/main.py`. Les chemins, schémas et réponses restent ceux de l'OpenAPI généré, pas ceux de ce résumé.

## Données et cycle de vie

PostgreSQL/PostGIS est la base relationnelle et Redis est utilisé par l'application au runtime. Au démarrage, le lifespan initialise les clients d'intégration, le pool Redis et les tâches de fond configurées ; la readiness vérifie PostgreSQL et Redis.

## Authentification et autorisation

Les routes protégées utilisent `Authorization: Bearer <token>`. `get_current_user` accepte soit les JWT locaux, soit les JWT DiddiFreeID lorsque `IDENTITY_JWKS_URL` ou `IDENTITY_BASE_URL` est configuré. Les routes de service à service exigent aussi `X-Client-ID`, avec audience et scope contrôlés. Les routes Backoffice utilisent le sujet de service attendu et peuvent exiger `X-Backoffice-Actor` ; `X-User-ID` est l'alias legacy documenté par le code.

## Dépendances externes

| Système | Usage dans le code |
|---|---|
| DiddiFreeID | validation JWT/JWKS, profil, jetons de service et projection de capacités chauffeur. |
| DiddiMap | géocodage, itinéraires, ETA et traces de course. |
| DiddiPay | PaymentIntent, callback signé, retour client/pro, wallet et réconciliation. |
| DiddiFiles | liens publics et fichiers KYC/KYV. |
| FCM | notifications push lorsque `PUSH_ENABLED=true`. |

Les URL, clients et secrets sont configurés par environnement. Voir la [référence de configuration](../configuration/CONFIGURATION_REFERENCE.md).
