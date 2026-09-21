# DiddiGo: consommation des tokens service

## Variables du service Pilotage

Ces variables appartiennent au service **Pilotage** qui appelle DiddiGo. Elles
ne doivent pas etre ajoutees a l'environnement du conteneur DiddiGo.

Exemple staging sans secret reel :

```env
DIDDIGO_BASE_URL=https://go-staging.diddifree.com
DIDDIGO_SERVICE_CLIENT_ID=pilotage-staging-diddigo
DIDDIGO_SERVICE_CLIENT_SECRET=<secret-genere-par-diddifreeid>
DIDDIGO_SERVICE_AUDIENCE=diddigo
DIDDIGO_SERVICE_SCOPE=ride-summary:read
DIDDIGO_SERVICE_TOKEN_URL=https://auth-staging.diddifree.com/identity/v1/auth/service/token
```

La valeur de `DIDDIGO_SERVICE_CLIENT_SECRET` doit exister uniquement dans le
gestionnaire de secrets ou les variables Portainer de Pilotage. Elle ne doit
jamais etre commitee, placee dans `.env.example`, transmise au frontend ou
enregistree dans les logs.

Si un secret est affiche dans une conversation, un ticket ou un journal, il
doit etre revoque puis regenere avant utilisation.

## Contrat Radar

Les endpoints backend Radar protégés par DiddiGo utilisent :

```http
Authorization: Bearer <jwt_service>
X-Client-ID: pilotage-staging-diddigo
```

Le token est émis par DiddiFreeID avec :

```text
audience=diddigo
scope=ride-summary:read
```

DiddiGo vérifie localement la signature via `IDENTITY_JWKS_URL`, puis :

- `iss=diddifree-id` ;
- `aud=diddigo` ;
- `sub=service:pilotage` ;
- `role=service` et `token_type=service` ;
- `status=active` ; ce claim est obligatoire du contrat DiddiFreeID ;
- le scope `ride-summary:read` ;
- l'égalité entre `X-Client-ID` et le claim `client_id`.

Le helper est disponible dans
`app_base.core.auth_deps.require_identity_service_token`. Il ne remplace pas
`get_current_user`, qui reste réservé aux tokens utilisateur.

`X-Service-Key` reste uniquement une compatibilité pour les intégrations
existantes et ne doit pas être ajouté aux nouveaux endpoints Radar.

## Endpoint Radar DiddiGo

```http
GET /internal/v1/ride-summary?date=YYYY-MM-DD
Authorization: Bearer <jwt_service>
X-Client-ID: pilotage-staging-diddigo
```

La date est interprétée en `Africa/Abidjan`. Pour éviter les scans coûteux,
elle doit être comprise entre aujourd'hui et les 31 derniers jours par défaut
(`RIDE_SUMMARY_MAX_AGE_DAYS` permet d'ajuster cette fenêtre).

Réponse:

```json
{
  "module": "diddigo",
  "date": "2026-09-19",
  "timezone": "Africa/Abidjan",
  "rides_requested": 12,
  "rides_completed": 8,
  "completed_fare_total_xof": 24000,
  "calculated_at": "2026-09-19T12:00:00Z"
}
```
