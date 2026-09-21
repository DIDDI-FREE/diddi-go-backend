# SCRUM-269 - Recherche operationnelle des logs

Date : 2026-09-21

## Livrable

- collecte Docker DiddiGo avec Promtail;
- indexation Loki avec retention de 30 jours;
- datasource Loki provisionnee dans Grafana;
- recherche admin par `ride_id` ou `driver_id`;
- filtres temporels et niveau;
- pagination par curseur;
- erreur explicite lorsque Loki est indisponible;
- contrat API v3.5 et brief Radar DG.

## Securite

Les routes utilisent exclusivement le role du jeton DiddiFreeID verifie via
`require_role("admin")`. Aucun role transmis par query string ou body ne peut
accorder l'acces.

## Validation

- Ruff : passe;
- tests cibles : 8 passes;
- suite complete avec PostGIS et Redis Docker : 281 passes;
- rendu Docker Compose : valide;
- demarrage Loki/Promtail teste; la collecte a ensuite ete restreinte au label
  `diddifree_observability=diddigo` apres detection d'une collecte Docker trop
  large lors du premier essai.
