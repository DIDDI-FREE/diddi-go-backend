# DiddiGo - Contrat API v3

**Destine a :** equipes Frontend / Mobile / Backend DiddiGo
**Base URL staging :** `https://go-staging.diddifree.com/v1`
**Auth staging :** `https://auth-staging.diddifree.com`
**DiddiFiles :** `https://diddifiles.diddifree.com/v1`
**DiddiMap staging :** `http://abidjanmaps-backend-staging.diddifree.com`

Important : le prefixe HTTP reste `/v1`. Le terme `v3` designe la version du
contrat fonctionnel.

---

## 1. Principes v3

```text
DiddiFreeID = identite, OTP, JWT, role global user/admin
DiddiGo = chauffeur, vehicule, course, pricing VTC, paiement ride, securite
DiddiMap = fournisseur unique des donnees geographiques
DiddiFiles = fournisseur unique des fichiers/documents
```

DiddiGo ne doit pas inventer de fallback geographique silencieux. Si DiddiMap
echoue, DiddiGo retourne une erreur documentee.

Le token DiddiFreeID ne porte pas le role chauffeur. Le role chauffeur est une
qualification metier DiddiGo via `driver_profiles` + `vehicles`.

Les erreurs DiddiGo suivent toujours le format `{"error":{"code","message","details"}}`.
Le catalogue complet des codes est maintenu dans `DiddiGo_Error_Catalog.md`.

---

## 2. Enums

| Enum | Valeurs |
|---|---|
| `identity.role` | `user`, `admin` |
| `vehicle.category` | `standard`, `comfort`, `van` |
| `comfort_level` | `standard`, `comfort`, `premium` |
| `payment_method` | `cash`, `wave`, `diddipay` |
| `ride.status` | `requested`, `matched`, `driver_en_route`, `in_progress`, `completed`, `cancelled_by_passenger`, `cancelled_by_driver`, `no_driver_found` |
| `payment.status` | `pending`, `requires_action`, `processing`, `succeeded`, `failed`, `cancelled`, `partially_refunded`, `refunded`, `collected`, `disputed` |

Note produit : on garde les categories vehicule existantes. `comfort_level`
devient le niveau commercial de confort.

---

## 3. Driver KYC

### `POST /drivers/profile`

Creer le dossier chauffeur DiddiGo. La creation ne valide plus le chauffeur.

Reponse :

```json
{
  "id": "driver-profile-id",
  "user_id": "identity-user-id",
  "license_number": "CI-123456",
  "status": "pending_verification",
  "kyc": {
    "submitted_at": "2026-08-06T10:00:00Z",
    "reviewed_at": null,
    "review_notes": null
  }
}
```

Tant que le statut reste `pending_verification`, le chauffeur peut completer son
dossier et son vehicule, mais il ne peut pas passer en ligne.

### `POST /drivers/kyc/resubmit`

Route chauffeur authentifie. Permet de renvoyer un dossier KYC apres rejet ou
correction sans recreer le profil chauffeur.

Requete :

```json
{
  "license_number": "CI-654321",
  "legal_name": "Awa Kone",
  "birth_date": "1992-04-20",
  "residence_address": "Cocody, Abidjan",
  "license_document_file_id": "8a1a0f2e-30e7-4436-a8ea-c12a1f76f3c1",
  "national_id_document_file_id": "45a14448-7bc7-4a21-972b-ff61585a571f",
  "selfie_document_file_id": "f9ac4c34-9c51-4772-a2d0-38bfb55bf3d9"
}
```

Reponse :

```json
{
  "id": "driver-profile-id",
  "status": "pending_verification",
  "kyc": {
    "reviewed_at": null,
    "review_notes": null,
    "license_document_file_id": "8a1a0f2e-30e7-4436-a8ea-c12a1f76f3c1"
  }
}
```

### `GET /drivers/kyc`

Route admin. Liste les dossiers KYC chauffeur pour revue.

Query params :

```text
status    pending_verification | active | suspended | all
page      defaut 1
page_size defaut 20, max 100
```

Reponse :

```json
{
  "data": [
    {
      "id": "driver-profile-id",
      "user_id": "identity-user-id",
      "license_number": "CI-123456",
      "status": "pending_verification",
      "kyc": {
        "legal_name": "Awa Kone",
        "license_document_file_id": "file-id",
        "national_id_document_file_id": "file-id",
        "selfie_document_file_id": "file-id",
        "submitted_at": "2026-08-06T10:00:00Z",
        "reviewed_at": null,
        "review_notes": null
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### `GET /drivers/{driver_id}/kyc`

Route admin. Retourne le dossier KYC complet connu par DiddiGo, avec les
`file_id` des documents et le vehicule actif si disponible.

Important : DiddiGo ne genere pas les URLs signees lui-meme. Les documents sont
references par `file_id`; les URLs temporaires restent fournies par DiddiFiles.

Reponse :

```json
{
  "id": "driver-profile-id",
  "user_id": "identity-user-id",
  "license_number": "CI-123456",
  "status": "pending_verification",
  "kyc": {
    "legal_name": "Awa Kone",
    "birth_date": "1992-04-20",
    "residence_address": "Cocody, Abidjan",
    "license_document_file_id": "file-id",
    "national_id_document_file_id": "file-id",
    "selfie_document_file_id": "file-id",
    "submitted_at": "2026-08-06T10:00:00Z",
    "reviewed_at": null,
    "review_notes": null
  },
  "vehicle": {
    "id": "vehicle-id",
    "plate_number": "CI-123-AA",
    "category": "standard",
    "comfort_level": "standard",
    "registration_document_file_id": "file-id",
    "active": true
  }
}
```

### `POST /drivers/{driver_id}/kyc/approve`

Route admin. Exige un token DiddiFreeID avec `role=admin`.

Requete :

```json
{
  "notes": "Documents OK"
}
```

Reponse :

```json
{
  "id": "driver-profile-id",
  "status": "active",
  "kyc": {
    "reviewed_at": "2026-08-06T10:15:00Z",
    "review_notes": "Documents OK (reviewed_by=admin-user-id)"
  }
}
```

### `POST /drivers/{driver_id}/kyc/reject`

Route admin. Exige un token DiddiFreeID avec `role=admin`.

Requete :

```json
{
  "notes": "Permis illisible"
}
```

Reponse :

```json
{
  "id": "driver-profile-id",
  "status": "suspended",
  "kyc": {
    "reviewed_at": "2026-08-06T10:15:00Z",
    "review_notes": "Permis illisible (reviewed_by=admin-user-id)"
  }
}
```

### `POST /drivers/online`

Avant validation admin, retourne :

```json
{
  "error": {
    "code": "DRIVER_NOT_VERIFIED",
    "message": "Votre profil chauffeur n'est pas encore valide.",
    "details": {
      "status": "pending_verification"
    }
  }
}
```

Apres validation admin, le chauffeur peut passer online s'il a aussi un vehicule
actif.

Erreurs KYC principales :

| HTTP | Code | Sens |
|---|---|---|
| `403` | `FORBIDDEN_ROLE` | Le token n'est pas admin pour une route admin |
| `403` | `DRIVER_NOT_VERIFIED` | Le chauffeur n'est pas valide pour passer en ligne |
| `404` | `DRIVER_PROFILE_NOT_FOUND` | Aucun profil chauffeur pour ce compte ou cet identifiant |
| `409` | `DRIVER_PROFILE_ALREADY_EXISTS` | Un profil chauffeur existe deja pour ce compte |
| `422` | `DRIVER_KYC_STATUS_INVALID` | Filtre `status` invalide sur la file KYC |
| `422` | `INVALID_LICENSE_NUMBER` | Numero de permis vide ou invalide |

---

## 4. Places

### `GET /places/search`

Recherche de lieux via DiddiMap.

Query params :

```text
q        obligatoire, min 2 caracteres
bias_lat optionnel
bias_lng optionnel
limit    optionnel, defaut 10, max 20
```

Exemple :

```http
GET /v1/places/search?q=plateau&bias_lat=5.3599&bias_lng=-4.0083&limit=10
```

Reponse :

```json
[
  {
    "label": "Plateau, Abidjan",
    "lat": 5.3204,
    "lng": -4.0161
  }
]
```

Erreurs :

| HTTP | Code | Sens |
|---|---|---|
| `503` | `DIDDIMAP_UNAVAILABLE` | DiddiMap indisponible ou timeout |
| `502` | `DIDDIMAP_INVALID_RESPONSE` | reponse DiddiMap invalide |

---

## 5. Pricing

### `POST /rides/pricing/estimate`

DiddiMap fournit uniquement distance/duree. DiddiGo applique sa propre politique
de pricing.

Requete :

```json
{
  "pickup": {
    "lat": 5.3599,
    "lng": -4.0083,
    "address": "Carrefour Anador, Yopougon"
  },
  "dropoff": {
    "lat": 5.3167,
    "lng": -4.0333,
    "address": "Plateau, Rue du Commerce"
  },
  "vehicle_category": "standard",
  "comfort_level": "standard"
}
```

Reponse :

```json
{
  "estimated_fare": 3100,
  "currency": "XOF",
  "distance_km": 11.876,
  "duration_seconds": 983,
  "surge_multiplier": 1.0,
  "surge_cap": 1.6,
  "base_fare": 250,
  "distance_fare": 2850,
  "duration_fare": 0,
  "commission_rate": 0.08,
  "platform_commission": 248,
  "driver_payout_estimate": 2852
}
```

Valeurs par defaut si aucune regle tarifaire active n'est seedee :

```text
base_fare = 250 XOF
distance_fare = distance_km * 240 XOF
duration_fare = duration_minutes * 0 XOF
surge_multiplier = min(rule.surge_multiplier, 1.6)
commission_rate = 0.08
```

Le prix final sera attache a la course terminee. En v3, DiddiGo stocke deja les
champs necessaires pour basculer sur la distance/duree reellement parcourues,
mais `actual_distance_km` et `actual_duration_seconds` restent `null` tant que
DiddiMap Core ne fournit pas le calcul officiel.

---

## 6. Rides

### `POST /rides`

Requete :

```json
{
  "pickup": {
    "lat": 5.3599,
    "lng": -4.0083,
    "address": "Carrefour Anador, Yopougon"
  },
  "dropoff": {
    "lat": 5.3167,
    "lng": -4.0333,
    "address": "Plateau, Rue du Commerce"
  },
  "vehicle_category": "standard",
  "comfort_level": "standard",
  "payment_method": "cash",
  "scheduled_at": null
}
```

`payment_method` accepte `cash`, `wave`, `diddipay`. `cash` reste confirme
localement par le chauffeur. `wave` et `diddipay` passent par DiddiPay
PaymentIntent en service-to-service.

Reponse :

```json
{
  "ride_id": "ride-id",
  "status": "requested",
  "estimated_fare": 3100,
  "currency": "XOF",
  "payment_method": "cash",
  "requested_at": "2026-08-05T10:15:00Z"
}
```

Matching :

```text
chauffeur actif
vehicule actif
vehicle.category == ride.vehicle_category
vehicle.comfort_level == ride.comfort_level
position dans le rayon de matching
```

### `GET /rides/{ride_id}`

Reponse partielle :

```json
{
  "id": "ride-id",
  "status": "matched",
  "vehicle_category": "standard",
  "comfort_level": "standard",
  "estimated_fare": 3100,
  "final_fare": null,
  "currency": "XOF",
  "distance_km": 11.876,
  "duration_seconds": 983,
  "pricing": {
    "base_fare": 250,
    "distance_fare": 2850,
    "duration_fare": 0,
    "surge_multiplier": 1.0,
    "surge_cap": 1.6,
    "commission_rate": 0.08,
    "platform_commission": 248,
    "driver_payout_estimate": 2852,
    "actual_distance_km": null,
    "actual_duration_seconds": null
  },
  "payment": {
    "method": "cash",
    "transaction_id": null
  },
  "emergency": {
    "status": null,
    "requested_at": null
  }
}
```

---

## 7. Traces GPS REST

### `POST /rides/{ride_id}/location-samples`

Endpoint reserve au chauffeur assigne. Sert a stocker les traces GPS chauffeur.
Le partage public de course utilise la derniere position chauffeur stockee.

Requete :

```json
{
  "samples": [
    {
      "lat": 5.352,
      "lng": -3.997,
      "recorded_at": "2026-08-05T10:20:00Z",
      "heading": 90,
      "speed_kmh": 25,
      "accuracy_m": 8,
      "source": "driver"
    }
  ]
}
```

Reponse :

```json
{
  "ride_id": "ride-id",
  "accepted_samples": 1
}
```

Decision v3 : tant que DiddiMap Core ne fournit pas un contrat REST officiel de
map-matching / distance reelle, DiddiGo stocke les samples localement et garde
le prix final base sur l'estimation initiale. Aucun fallback cache n'est fait.
Le backend logge `ride_actual_pricing_pending` a la completion si des samples
existent mais que le recalcul fournisseur n'est pas encore disponible.

### Pipeline DiddiMap Core cible

Decision produit/architecture :

```text
1. DiddiGo recoit les positions temps reel chauffeur
2. DiddiGo stocke ou bufferise les positions liees au ride
3. A la fin du ride, DiddiGo envoie la trace complete a DiddiMap Core
4. DiddiMap Core analyse la trace
5. DiddiMap Core produit des insights route/distance/qualite/scoring
6. Un admin valide ou rejette ces insights
7. Les routes, le scoring et les futures optimisations s'ameliorent
```

Responsabilites :

```text
DiddiGo = collecte, stockage ride_id, statut metier, lien avec course/paiement
DiddiMap = map-matching, analyse geographique, insights, amelioration reseau
Admin = validation/rejet des insights avant impact durable
```

Tant que DiddiMap Core ne publie pas son contrat REST d'analyse de trace,
DiddiGo ne doit pas recalculer silencieusement la distance reelle ni le prix
final. Les traces restent stockees cote DiddiGo et pretes a etre envoyees.

---

## 8. Share Ride

### `POST /rides/{ride_id}/share-link`

Accessible au passager, au chauffeur assigne, ou admin.

Reponse :

```json
{
  "ride_id": "ride-id",
  "share_token": "opaque-token",
  "expires_at": "2026-08-06T10:15:00Z",
  "public_path": "/v1/rides/shared/opaque-token"
}
```

### `GET /rides/shared/{token}`

Route publique sans login. Elle ne retourne pas de donnees sensibles. La
position affichee est celle du chauffeur, car pendant la course on considere
que passager et chauffeur sont dans le meme vehicule.

Reponse :

```json
{
  "ride_id": "ride-id",
  "status": "in_progress",
  "driver_location": {
    "lat": 5.352,
    "lng": -3.997
  },
  "last_location_at": "2026-08-05T10:20:00Z",
  "pickup": {
    "lat": 5.3599,
    "lng": -4.0083,
    "address": "Carrefour Anador, Yopougon"
  },
  "dropoff": {
    "lat": 5.3167,
    "lng": -4.0333,
    "address": "Plateau, Rue du Commerce"
  }
}
```

---

## 9. Urgence

### `POST /rides/{ride_id}/emergency`

Accessible au passager, au chauffeur assigne, ou admin.

Requete :

```json
{
  "note": "Besoin assistance"
}
```

Reponse :

```json
{
  "ride_id": "ride-id",
  "status": "open",
  "requested_at": "2026-08-05T10:25:00Z"
}
```

DiddiGo ecrit aussi un log serveur `ride_emergency` avec `ride_id` et
`actor_user_id`. La phase back-office/dispatch d'urgence sera separee.

---

## 10. Paiements

### `GET /payments/{ride_id}`

Si aucune transaction n'existe encore, DiddiGo retourne une transaction logique
pending avec la methode demandee sur la course.

### `POST /payments/{ride_id}/prepare`

Prepare la transaction. Pour `cash`, DiddiGo cree une transaction locale
pending. Pour `wave` et `diddipay`, DiddiGo cree un `PaymentIntent` dans
DiddiPay via service-to-service.

Requete :

```json
{
  "method": "wave",
  "customer_email": "client@example.com",
  "customer_phone": "+2250700000000",
  "callback_url": "https://go-staging.diddifree.com/payments/return"
}
```

`customer_email` est obligatoire pour `wave` et `diddipay`, car le PSP actif
derriere DiddiPay/Paystack l'exige. DiddiGo ne doit pas inventer d'email si
l'identite ne le fournit pas.

Reponse :

```json
{
  "ride_id": "ride-id",
  "status": "requires_action",
  "method": "wave",
  "amount": 3100,
  "currency": "XOF",
  "provider": "diddipay",
  "provider_status": "requires_action",
  "payment_intent_id": "payment-intent-id",
  "business_reference": "ride:ride-id",
  "next_action": {
    "type": "redirect",
    "url": "https://checkout.paystack.com/example",
    "instructions": null,
    "expires_at": null
  }
}
```

Pour `cash`, `provider_status` vaut `local`.

Important : une redirection frontend ne prouve jamais le paiement. Le paiement
est considere confirme seulement quand DiddiGo recoit le callback signe DiddiPay
ou reconcilie le statut `succeeded` depuis DiddiPay.

### `POST /internal/webhooks/diddipay`

Endpoint interne appele par DiddiPay, sans prefixe `/v1`.

Headers :

```http
X-DiddiPay-Event-ID: event-id
X-DiddiPay-Signature: hmac-sha256-hex
```

DiddiGo verifie la signature sur le corps brut avec
`DIDDIPAY_CALLBACK_SECRET`, deduplique l'evenement et met a jour la transaction
locale par `payment_intent_id`.

### `POST /payments/{ride_id}/confirm-cash`

Confirme l'encaissement cash par le chauffeur.

---

## 11. WebSocket et push

Le WebSocket reste le canal temps reel quand l'app est active :

```text
wss://go-staging.diddifree.com/v1/ws?token=<access_token_diddifreeid>
```

Le frontend chauffeur doit continuer a envoyer `driver.location_push` toutes les
3 a 5 secondes quand il est en ligne ou en course. Pour fiabiliser la phase
test Android, utiliser un foreground service.

DiddiGo envoie aussi les offres chauffeur via FCM si un device est enregistre :

```http
POST /v1/devices/register
POST /v1/devices/unregister
```

---

## 12. Hors Scope v3

```text
DiddiSend
DiddiScore
reconciliation periodique DiddiPay
dispatch urgence complet
map-matching DiddiMap Core officiel
contrat physique /v2 ou /v3 dans l'URL
```
