# DiddiFree Pro - Scores DiddiGo

**Version du contrat :** `diddi.score.v1`  
**Mise a jour :** 20 octobre 2026  
**Proprietaire des faits et de la formule :** DiddiGo

## Objet

DiddiFree Pro consomme des projections de score normalisees. Il ne calcule pas
le score et ne modifie jamais la priorite de matching DiddiGo.

Les routes publiques `GET /v1/me/scores` et `GET /v1/rides/{ride_id}/score`
restent compatibles. Les routes ci-dessous sont reservees aux integrations
internes et retournent des objets conformes a `diddi.score.v1`.

## Authentification S2S

```http
Authorization: Bearer <service-jwt>
X-Client-ID: diddifreepro-staging-diddigo
X-Request-ID: <correlation-id>
```

| Claim / valeur | Exigence |
| --- | --- |
| `iss` | `diddifree-id` |
| `sub` | `service:diddifreepro` |
| `aud` | `diddigo` |
| `scope` | contient `diddigo:scores:read` |
| `status` | `active` |
| `client_id` | identique a `X-Client-ID` |

Le client est provisionne dans DiddiFreeID. DiddiGo ne stocke pas son secret :
il configure seulement le client attendu avec `DIDDIFREEPRO_SERVICE_CLIENT_ID`.

## Routes

```http
GET /internal/v1/scores/users/{user_id}
GET /internal/v1/scores/rides/{ride_id}
```

La premiere retourne une collection `scores` comprenant toujours le score
passager et, seulement si le profil existe, le score chauffeur. La seconde
retourne un objet unique de qualite de course.

```json
{
  "contract_version": "diddi.score.v1",
  "service": "diddigo",
  "kind": "reliability",
  "subject_type": "driver",
  "subject_id": "driver-profile-uuid",
  "user_id": "diddifree-user-uuid",
  "score": {
    "value": 4.25,
    "scale": "five",
    "normalized_value": 85,
    "local_level": "good",
    "normalized_level": "good",
    "data_status": "stable",
    "sample_size": 8,
    "reason_codes": ["good_ratings", "low_cancellation"],
    "calculation_version": "diddigo_reliability_v1",
    "calculated_at": "2026-10-20T10:00:00Z"
  }
}
```

`TripScore` est retourne avec `kind=quality`, `subject_type=trip` et
`user_id=null` : il ne doit pas etre attribue artificiellement au passager ou
au chauffeur.

## Normalisation et compatibilite

| Niveau local DiddiGo | Niveau normalise |
| --- | --- |
| `new` | `unknown` |
| `excellent` | `excellent` |
| `good` | `good` |
| `fair` | `watch` |
| `risk` | `risk` |

`normalized_value` vaut toujours `value * 20`. Le score neutre d'un nouvel
utilisateur reste `4.00 / 80`, mais `data_status=insufficient_data` et
`normalized_level=unknown` interdisent de le presenter comme une reputation
etablie.

Les reason codes sont des identifiants stables, sans texte libre ni donnee
personnelle. Les anciens motifs non conformes sont reduits a
`reason_recorded` dans cette projection.

## Limites

- `PriorityScore` est exclu : il reste un signal interne du matching.
- SOS, plainte et decision Support ne changent pas la formule par eux-memes.
- Les scores n'autorisent pas une course et ne remplacent pas KYC, KYV,
  disponibilite, solde, vehicule, paiement ou securite.
- Pilotage consomme des agregats, pas les scores individuels de cette API.

## Erreurs

| HTTP | Code | Signification |
| --- | --- | --- |
| `401` | `TOKEN_MISSING`, `SERVICE_TOKEN_INVALID` | Token S2S absent ou invalide. |
| `403` | `SERVICE_CLIENT_FORBIDDEN`, `SERVICE_SCOPE_INVALID`, `SERVICE_SUBJECT_INVALID` | Client, scope ou sujet non autorise. |
| `404` | `RIDE_NOT_FOUND` | Course demandee inconnue. |
| `503` | `SERVICE_JWKS_UNAVAILABLE`, `DATABASE_UNAVAILABLE` | Dependances temporairement indisponibles. |
