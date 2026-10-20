# DiddiSupport

**Version :** `diddi.context.v1`
**Mise a jour :** 20 octobre 2026
**Proprietaire de la ressource :** DiddiGo

DiddiSupport ne lit pas les tables DiddiGo. Il obtient un contexte de course minimal, redige et versionne via l'endpoint interne ci-dessous.

## Endpoint

```http
GET /internal/v1/support/ride/{ride_id}/context
```

Base staging publique, si le reseau interne ne fournit pas une adresse de service dediee :

```text
https://go-staging.diddifree.com/internal/v1/support/ride/{ride_id}/context
```

L'URL interne effective est configuree par DiddiSupport. Le chemin et le contrat restent identiques.

## Authentification S2S

```http
Authorization: Bearer <service-jwt>
X-Client-ID: diddisupport-staging-diddigo
X-Request-ID: <uuid-ou-identifiant-de-correlation>
X-Support-Context-Scope: diddigo:support-context:read
```

| Claim / valeur | Exigence |
| --- | --- |
| `iss` | `diddifree-id` |
| `sub` | `service:diddisupport` |
| `role` | `service` |
| `token_type` | `service` |
| `aud` | `diddigo` |
| `scope` | contient `diddigo:support-context:read` |
| `client_id` | identique a `X-Client-ID` |

`X-Support-Context-Scope` est verifie comme en-tete de contrat. La permission effective reste celle du JWT : l'en-tete seul ne donne jamais un droit.

## Reponse

```json
{
  "protocol": "diddi.context.v1",
  "origin_service": "diddigo",
  "resource_type": "ride",
  "resource_id": "11111111-1111-1111-1111-111111111111",
  "data": {
    "status": "completed",
    "completion_reason": "normal",
    "cancellation_reason": null,
    "fare_amount": 3700,
    "currency": "XOF",
    "payment_method": "mobile_money",
    "participants": [
      {"user_id": "22222222-2222-2222-2222-222222222222", "role": "passenger"},
      {"user_id": "33333333-3333-3333-3333-333333333333", "role": "driver"}
    ],
    "timeline": {
      "requested_at": "2026-10-20T10:00:00Z",
      "matched_at": "2026-10-20T10:02:00Z",
      "arrived_at": "2026-10-20T10:10:00Z",
      "started_at": "2026-10-20T10:12:00Z",
      "completed_at": "2026-10-20T10:35:00Z",
      "cancelled_at": null
    }
  },
  "redacted_fields": [
    "participants.phone_e164",
    "locations.pickup",
    "locations.dropoff",
    "driver.last_location",
    "kyc",
    "payment.provider_details"
  ],
  "as_of": "2026-10-20T10:35:00Z",
  "fetched_at": "2026-10-20T10:36:01Z"
}
```

`fare_amount` est le montant final s'il est disponible ; sinon, c'est le montant estime. `as_of` est la date du dernier etat metier connu de la course, alors que `fetched_at` est la date de production de cette reponse.

## Confidentialite

Cette API ne retourne jamais de numero de telephone, adresse ou coordonnee de prise en charge/depose, position GPS, document KYC/KYV, token, secret ni detail de paiement fournisseur. Les champs volontairement exclus sont annonces dans `redacted_fields` pour que DiddiSupport ne les suppose pas disponibles.

## Erreurs

| HTTP | Code | Signification |
| --- | --- | --- |
| `401` | `TOKEN_MISSING`, `SERVICE_TOKEN_INVALID` | JWT de service absent ou invalide. |
| `403` | `SERVICE_CLIENT_FORBIDDEN`, `SERVICE_SCOPE_INVALID`, `SERVICE_SCOPE_HEADER_INVALID` | Client, scope JWT ou en-tete de protocole non autorise. |
| `404` | `RIDE_NOT_FOUND` | Course inconnue. |
| `503` | `SERVICE_JWKS_UNAVAILABLE`, `DATABASE_UNAVAILABLE` | Verification JWKS ou base temporairement indisponible. |

Chaque reponse, y compris les erreurs, propage `X-Request-ID` pour le suivi entre DiddiSupport et les logs DiddiGo.
