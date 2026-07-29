# Git Flow DiddiGo

Convention de branches du projet :

- `main` : production
- `stage` : intégration, QA, UI/UX, validation des changements
- `feat/*` : branches de travail créées depuis `stage`

## Règles

- Tout travail de développement part de `stage`.
- Toute fonctionnalité ou correction passe par une branche `feat/*`.
- Les merges vers `main` ne se font qu’après validation sur `stage`.
- `main` reste la référence de production.

## Exemples

```bash
git checkout stage
git checkout -b feat/auth-refresh-token
git checkout -b feat/ride-matching
```

## Déploiement

- `stage` peut être consommée par les équipes QA, front et UI/UX.
- `main` sert aux déploiements de production.
