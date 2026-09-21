# Brief frontend - recherche de logs DiddiGo

Date : 2026-09-21
Version API : v3.5

## User journey admin/support

1. L'admin ouvre une course ou une fiche chauffeur dans Radar DG.
2. Il choisit `Journaux` et, si necessaire, une periode ou un niveau.
3. Le frontend appelle la route correspondant a l'objet consulte.
4. Il affiche les evenements du plus recent au plus ancien.
5. Le bouton `Charger plus` renvoie `next_cursor` sans recalculer le curseur.

## Routes

```http
GET /v1/admin/logs/rides/{ride_id}
GET /v1/admin/logs/drivers/{driver_id}
Authorization: Bearer <admin_access_token>
```

Filtres : `from`, `to`, `level`, `limit`, `cursor`. Par defaut, DiddiGo renvoie
les dernieres 24 heures, par pages de 100.

## Regles frontend

- Ne jamais envoyer de role dans l'URL ou le body.
- Afficher `timestamp`, `level`, `event`, `message`, `request_id` et `metadata`.
- Conserver les filtres lors de la pagination.
- Sur `503 LOG_SEARCH_UNAVAILABLE`, afficher que les journaux sont temporairement
  indisponibles; ne pas afficher une liste vide comme si aucun evenement n'existait.
- Sur `403 FORBIDDEN_ROLE`, masquer cette fonction et journaliser le refus.
