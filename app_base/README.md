# DiddiGo

Base applicative modulaire FastAPI pour DiddiGo.

## Démarrage

```bash
uvicorn app_base.main:app --reload
```

## Ce qui est prêt

- `auth`, `ride`, `payment` structurés en tranches verticales
- contrats partagés dans `shared_kernel`
- couche `core` pour la DB et la configuration
- squelettes `infra` prêts pour PostgreSQL, DiddiMap et futur DiddiPay
