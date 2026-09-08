# DiddiGo - Contrat API v3.2

**Destine a :** equipes Frontend / Mobile / Backend DiddiGo
**Base URL staging :** `https://go-staging.diddifree.com/v1`
**Auth staging :** `https://auth-staging.diddifree.com`
**DiddiFiles :** `https://diddifiles.diddifree.com/v1`
**DiddiMap staging :** `http://abidjanmaps-backend-staging.diddifree.com`

Important : le prefixe HTTP reste `/v1`. Le terme `v3.2` designe la version du
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

Les roles partenaires sont locaux a DiddiGo. DiddiFreeID continue a porter
seulement les roles globaux `user` et `admin`.

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
| `wallet.direction` | `credit`, `debit` |
| `wallet.entry_type` | `ride_payout`, `platform_commission`, `topup`, `adjustment` |
| `wallet.entry_status` | `pending`, `confirmed`, `failed` |
| `topup.status` | `pending`, `requires_action`, `processing`, `succeeded`, `failed`, `cancelled` |
| `partner.type` | `company`, `fleet_owner` |
| `partner.status` | `pending_verification`, `active`, `suspended`, `rejected` |
| `partner.member_role` | `partner_manager`, `partner_operator`, `partner_viewer` |
| `partner.commission_mode` | `percentage`, `fixed` |
| `vehicle.verification_status` | `pending_verification`, `active`, `suspended`, `rejected` |

Note produit : on garde les categories vehicule existantes cote backend.
Pour reduire la friction MVP, le frontend passager peut omettre
`vehicle_category`; DiddiGo applique alors `standard`. `comfort_level` devient
le seul choix commercial visible au passager.

---

## 3. Driver KYC

### `POST /drivers/profile`

Creer le dossier chauffeur DiddiGo. La creation ne valide plus le chauffeur.
Les documents KYC obligatoires pour validation admin sont :

| Document | Champ DiddiGo | Purpose DiddiFiles |
|---|---|---|
| Permis recto | `license_document_file_id` | `diddigo_driver_kyc_license` |
| Permis verso | `license_back_document_file_id` | `diddigo_driver_kyc_license_back` |
| CNI recto | `national_id_document_file_id` | `diddigo_driver_kyc_national_id` |
| CNI verso | `national_id_back_document_file_id` | `diddigo_driver_kyc_national_id_back` |
| Selfie | `selfie_document_file_id` | `diddigo_driver_kyc_selfie` |

Les champs legacy `*_document_url` restent acceptes temporairement, mais le
frontend doit privilegier les `file_id` DiddiFiles.

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
  "license_back_document_file_id": "c43b7a07-b28b-48ca-a380-4565e0d9fb11",
  "national_id_document_file_id": "45a14448-7bc7-4a21-972b-ff61585a571f",
  "national_id_back_document_file_id": "7504fa3f-4d1e-4f93-8e94-9a491d3b5acf",
  "selfie_document_file_id": "f9ac4c34-9c51-4772-a2d0-38bfb55bf3d9",
  "license_document_url": "https://cdn.example/license-front.jpg",
  "license_back_document_url": "https://cdn.example/license-back.jpg",
  "national_id_document_url": "https://cdn.example/national-id-front.jpg",
  "national_id_back_document_url": "https://cdn.example/national-id-back.jpg",
  "selfie_document_url": "https://cdn.example/selfie.jpg"
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
    "license_document_file_id": "8a1a0f2e-30e7-4436-a8ea-c12a1f76f3c1",
    "license_back_document_file_id": "c43b7a07-b28b-48ca-a380-4565e0d9fb11",
    "national_id_document_file_id": "45a14448-7bc7-4a21-972b-ff61585a571f",
    "national_id_back_document_file_id": "7504fa3f-4d1e-4f93-8e94-9a491d3b5acf",
    "selfie_document_file_id": "f9ac4c34-9c51-4772-a2d0-38bfb55bf3d9"
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
        "license_back_document_file_id": "file-id",
        "national_id_document_file_id": "file-id",
        "national_id_back_document_file_id": "file-id",
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
    "license_back_document_file_id": "file-id",
    "national_id_document_file_id": "file-id",
    "national_id_back_document_file_id": "file-id",
    "selfie_document_file_id": "file-id",
    "license_document_url": null,
    "license_back_document_url": null,
    "national_id_document_url": null,
    "national_id_back_document_url": null,
    "selfie_document_url": null,
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
L'approbation refuse un dossier incomplet avec `422 INVALID_KYC_DOCUMENTS`.
Pour etre valide, le dossier doit contenir permis recto/verso, CNI recto/verso
et selfie, soit en `file_id`, soit temporairement en URL legacy.

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
actif, un KYV vehicule valide et, si la variable `DRIVER_MIN_BALANCE` est
superieure a zero, un solde chauffeur suffisant.

Si le vehicule n'est pas valide :

```json
{
  "error": {
    "code": "VEHICLE_NOT_VERIFIED",
    "message": "Votre vehicule n'est pas encore valide.",
    "details": {
      "vehicle_id": "vehicle-id",
      "status": "pending_verification"
    }
  }
}
```

Erreurs KYC principales :

| HTTP | Code | Sens |
|---|---|---|
| `403` | `FORBIDDEN_ROLE` | Le token n'est pas admin pour une route admin |
| `403` | `DRIVER_NOT_VERIFIED` | Le chauffeur n'est pas valide pour passer en ligne |
| `403` | `DRIVER_BALANCE_TOO_LOW` | Solde chauffeur insuffisant pour passer en ligne |
| `404` | `DRIVER_PROFILE_NOT_FOUND` | Aucun profil chauffeur pour ce compte ou cet identifiant |
| `409` | `DRIVER_PROFILE_ALREADY_EXISTS` | Un profil chauffeur existe deja pour ce compte |
| `422` | `DRIVER_KYC_STATUS_INVALID` | Filtre `status` invalide sur la file KYC |
| `422` | `INVALID_KYC_DOCUMENTS` | Dossier KYC incomplet : permis recto/verso, CNI recto/verso ou selfie absent |
| `422` | `INVALID_LICENSE_NUMBER` | Numero de permis vide ou invalide |
| `403` | `VEHICLE_NOT_VERIFIED` | Vehicule non valide par l'admin KYV |
| `404` | `VEHICLE_NOT_FOUND` | Vehicule introuvable |
| `422` | `INVALID_VEHICLE_KYV_DOCUMENTS` | Dossier KYV vehicule incomplet |

### Vehicle KYV

Le KYV vehicule est separe du KYC chauffeur. Il s'applique aux vehicules solo
et aux vehicules partenaires.

### `POST /drivers/vehicle`

Le payload accepte maintenant des documents vehicule supplementaires :

```json
{
  "plate_number": "CE-123-AA",
  "make": "Toyota",
  "model": "Yaris",
  "color": "gris",
  "category": "standard",
  "comfort_level": "standard",
  "registration_document_file_id": "file-id",
  "insurance_document_file_id": "file-id",
  "technical_inspection_document_file_id": "file-id",
  "transport_authorization_document_file_id": "file-id",
  "vehicle_front_photo_file_id": "file-id",
  "vehicle_back_photo_file_id": "file-id",
  "vehicle_left_photo_file_id": "file-id",
  "vehicle_right_photo_file_id": "file-id",
  "vehicle_interior_photo_file_id": "file-id"
}
```

Documents obligatoires pour validation admin :

| Document | Champ DiddiGo | Purpose DiddiFiles recommande |
|---|---|---|
| Carte grise / immatriculation | `registration_document_file_id` | `diddigo_vehicle_registration` |
| Assurance | `insurance_document_file_id` | `diddigo_vehicle_insurance` |
| Visite technique | `technical_inspection_document_file_id` | `diddigo_vehicle_technical_inspection` |
| Photo avant vehicule | `vehicle_front_photo_file_id` | `diddigo_vehicle_photo_front` |
| Photo arriere vehicule | `vehicle_back_photo_file_id` | `diddigo_vehicle_photo_back` |
| Photo cote gauche vehicule | `vehicle_left_photo_file_id` | `diddigo_vehicle_photo_left` |
| Photo cote droit vehicule | `vehicle_right_photo_file_id` | `diddigo_vehicle_photo_right` |
| Photo interieur vehicule | `vehicle_interior_photo_file_id` | `diddigo_vehicle_photo_interior` |

Document optionnel :

| Document | Champ DiddiGo | Purpose DiddiFiles recommande |
|---|---|---|
| Autorisation transport | `transport_authorization_document_file_id` | `diddigo_vehicle_transport_authorization` |

La creation vehicule retourne `verification_status=pending_verification`. Le
vehicule ne permet pas au chauffeur de passer en ligne tant que l'admin ne l'a
pas approuve.

Les champs legacy `*_document_url` et `vehicle_photo_file_id` /
`vehicle_photo_url` restent acceptes temporairement pour compatibilite, mais
ils ne remplacent pas les 5 vues photo obligatoires du KYV. Le frontend doit
privilegier les `file_id` DiddiFiles.

### `POST /drivers/vehicles/{vehicle_id}/kyv/resubmit`

Route chauffeur authentifie. Corrige ou complete le dossier KYV du vehicule.
Le vehicule repasse en `pending_verification`.

### `POST /drivers/vehicles/{vehicle_id}/kyv/approve`

Route admin. Valide le KYV vehicule.

Requete :

```json
{
  "notes": "Vehicule OK"
}
```

### `POST /drivers/vehicles/{vehicle_id}/kyv/reject`

Route admin. Rejette le KYV vehicule et desactive le vehicule.

Requete :

```json
{
  "notes": "Assurance expiree"
}
```

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
  "comfort_level": "standard"
}
```

`vehicle_category` est optionnel et vaut `standard` par defaut. Le frontend
passager doit surtout envoyer `comfort_level`.

Reponse :

```json
{
  "estimated_fare": 3100,
  "currency": "XOF",
  "distance_km": 11.876,
  "duration_seconds": 983,
  "surge_multiplier": 1.0,
  "surge_cap": 1.6,
  "comfort_multiplier": 1.0,
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
comfort_multiplier = standard:1.00, comfort:1.15, premium:1.30
commission_rate = 0.08
```

Dynamic pricing MVP :

```text
La variation dynamique livree en v3 passe par ride.pricing_rules.surge_multiplier.
Elle est appliquee avant acceptation passager et reste plafonnee par
surge_cap=1.6. Une fois le passager confirme la course, le prix est verrouille.
Les champs actual_* et actual_pricing_fare servent ensuite a ameliorer les
futures regles dynamiques, pas a refacturer le client.
```

Le prix accepte au depart est le prix facture au client. En v3, si DiddiGo a
recu des points GPS chauffeur, il envoie la trace a DiddiMap Core au moment de
terminer la course, recupere `actual_distance_km` et
`actual_duration_seconds`, puis calcule `actual_pricing_fare` et
`pricing_delta` pour analytics. DiddiGo ne remplace pas le prix facture par ce
prix theorique reel.

Si aucun point GPS n'a ete recu, DiddiGo garde le prix estime et logge
explicitement `ride_actual_pricing_skipped reason=no_route_samples`. Si des
points GPS existent mais que DiddiMap trace/analyze echoue, DiddiGo retourne
une erreur explicite et ne fait pas de fallback silencieux.

Regle commerciale :

```text
estimated_fare = prix affiche/accepte au depart
final_fare = prix facture, verrouille sur estimated_fare
actual_pricing_fare = prix theorique calcule depuis la trace reelle
pricing_delta = actual_pricing_fare - final_fare
```

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
  "comfort_level": "standard",
  "payment_method": "cash",
  "scheduled_at": null
}
```

`payment_method` accepte `cash`, `wave`, `diddipay`. `cash` reste confirme
localement par le chauffeur. `wave` et `diddipay` passent par DiddiPay
PaymentIntent en service-to-service.

`vehicle_category` reste accepte pour compatibilite et pour des evolutions
futures, mais il est optionnel. Si absent, DiddiGo utilise `standard`.

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
position dans le rayon de matching
```

`comfort_level` est maintenant un filtre de matching hierarchique :

```text
course standard -> vehicule standard, comfort ou premium
course comfort  -> vehicule comfort ou premium
course premium  -> vehicule premium uniquement
```

Un vehicule d'un niveau superieur peut servir une demande inferieure, mais pas
l'inverse. Cela evite de faire payer `premium` au passager pour envoyer une
voiture `standard`.

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
    "comfort_multiplier": 1.0,
    "commission_rate": 0.08,
    "platform_commission": 248,
    "driver_payout_estimate": 2852,
    "actual_distance_km": null,
    "actual_duration_seconds": null,
    "actual_pricing_fare": null,
    "pricing_delta": null
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

Decision v3 : DiddiMap Core expose maintenant un contrat REST de traces via
`/api/v1/map-traces/*`. DiddiGo stocke les samples localement, demarre une
trace DiddiMap quand la course passe `in_progress`, puis envoie les samples et
analyse la trace quand la course passe `completed`.

Le backend logge `ride_map_trace_started` au debut de course,
`ride_actual_pricing_applied` quand le prix final reel est calcule, ou
`ride_actual_pricing_skipped reason=no_route_samples` si aucune trace chauffeur
n'a ete recue.

### Pipeline DiddiMap Core retenu

Decision produit/architecture :

```text
1. DiddiGo recoit les positions temps reel chauffeur
2. DiddiGo stocke ou bufferise les positions liees au ride
3. Quand la course commence, DiddiGo demarre une trace DiddiMap:
   POST /api/v1/map-traces/start
4. Pendant ou apres la course, DiddiGo envoie les positions:
   POST /api/v1/map-traces/{trace_id}/positions
5. A la fin du ride, DiddiGo termine la trace:
   POST /api/v1/map-traces/{trace_id}/finish
6. DiddiGo demande l'analyse:
   POST /api/v1/map-traces/{trace_id}/analyze
7. DiddiMap Core produit distance/duree reelles, qualite GPS et insights
8. Un admin valide ou rejette ces insights
9. Les routes, le scoring et les futures optimisations s'ameliorent
```

Responsabilites :

```text
DiddiGo = collecte, stockage ride_id, statut metier, lien avec course/paiement
DiddiMap = map-matching, analyse geographique, insights, amelioration reseau
Admin = validation/rejet des insights avant impact durable
```

Important : le WebSocket DiddiMap pour positions n'est pas encore implemente
cote DiddiMap. DiddiGo doit donc commencer par REST batch :

```text
POST /api/v1/map-traces/start
POST /api/v1/map-traces/{trace_id}/positions
POST /api/v1/map-traces/{trace_id}/finish
POST /api/v1/map-traces/{trace_id}/analyze
```

DiddiGo ne doit pas recalculer silencieusement la distance reelle ni le prix
final. Si DiddiMap trace/analyze echoue, DiddiGo garde les donnees locales et
retourne/logge une erreur explicite selon le contexte.

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
  "business_reference": "diddigo:ride:ride-id",
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

### `GET /payments/return`

Route publique de retour navigateur apres checkout. Elle existe pour eviter un
404 lorsque `DIDDIGO_PAYMENT_CALLBACK_URL` pointe vers DiddiGo.

Important : cette route ne confirme jamais le paiement. Elle affiche seulement
une page demandant a l'utilisateur de revenir dans l'application. L'application
doit relire `GET /v1/payments/{ride_id}`.

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

Effet wallet V1 :

```text
cash = le chauffeur garde le cash physiquement
DiddiGo debite le wallet chauffeur du montant de la commission plateforme
```

Pour `wave` et `diddipay`, le callback `succeeded` credite le wallet chauffeur
du montant net chauffeur (`driver_payout_estimate`) lorsque la course a un
chauffeur assigne.

---

## 10.1 Wallet chauffeur

### `GET /drivers/me/wallet`

Route chauffeur authentifie. Retourne le solde DiddiGo du chauffeur.

Reponse :

```json
{
  "driver_id": "driver-profile-id",
  "balance": -248,
  "currency": "XOF",
  "min_balance": 0,
  "can_go_online": true
}
```

Visibilite prix :

```text
passager -> voit le prix estime puis le prix facture verrouille
chauffeur avant in_progress -> ne voit pas estimated_fare, final_fare,
commission ni payout
chauffeur a partir de in_progress -> voit le montant de la course
admin/support -> voit aussi actual_pricing_fare et pricing_delta
```

`min_balance` vient de la configuration backend `DRIVER_MIN_BALANCE`. Si
`min_balance > 0` et que `balance < min_balance`, `POST /drivers/online`
retourne `403 DRIVER_BALANCE_TOO_LOW`.

### `GET /drivers/me/wallet/ledger`

Route chauffeur authentifie. Liste les mouvements du wallet.

Query params :

```text
page      defaut 1
page_size defaut 20, max 100
```

Reponse :

```json
{
  "data": [
    {
      "id": "ledger-entry-id",
      "driver_id": "driver-profile-id",
      "amount": 248,
      "currency": "XOF",
      "direction": "debit",
      "type": "platform_commission",
      "status": "confirmed",
      "reference_type": "ride",
      "reference_id": "ride-id",
      "description": "Commission DiddiGo sur course cash",
      "created_at": "2026-08-28T22:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

### `POST /drivers/me/wallet/topups`

Route chauffeur authentifie. Initialise une recharge chauffeur via DiddiPay ou
Wave.

Requete :

```json
{
  "amount": 5000,
  "method": "wave",
  "customer_email": "driver@example.com",
  "customer_phone": "+2250700000000",
  "callback_url": "https://go-staging.diddifree.com/wallet/return"
}
```

Reponse :

```json
{
  "id": "topup-id",
  "driver_id": "driver-profile-id",
  "amount": 5000,
  "currency": "XOF",
  "method": "wave",
  "status": "requires_action",
  "provider": "diddipay",
  "provider_status": "requires_action",
  "payment_intent_id": "payment-intent-id",
  "business_reference": "diddigo:driver_topup:topup-id",
  "paid_at": null,
  "next_action": {
    "type": "redirect",
    "url": "https://checkout.paystack.com/example"
  }
}
```

Important :

```text
La recharge ne credite le solde chauffeur qu'apres callback DiddiPay succeeded.
Un callback rejoue ne double pas le solde.
```

### `GET /drivers/me/wallet/topups/{topup_id}`

Route chauffeur authentifie. Retourne le statut d'une recharge. Tant que la
recharge reste en `requires_action`, DiddiGo renvoie le dernier `next_action`
connu pour permettre a l'application de reprendre le checkout.

### `GET /wallet/return`

Route publique de retour navigateur apres checkout de recharge chauffeur.
Comme `/payments/return`, elle ne confirme jamais la recharge; l'application
doit relire `GET /v1/drivers/me/wallet/topups/{topup_id}` puis
`GET /v1/drivers/me/wallet`.

---

## 10.2 Admin/support financier

### `GET /admin/drivers/{driver_id}/wallet`

Route admin. Retourne le wallet d'un chauffeur.

### `GET /admin/drivers/{driver_id}/wallet/ledger`

Route admin. Retourne le ledger financier d'un chauffeur.

### `POST /admin/payments/reconcile`

Route admin. Force une reconciliation des paiements et recharges DiddiPay non
finaux (`pending`, `requires_action`, `processing`).

### `POST /admin/payments/rides/{ride_id}/reconcile`

Route admin. Force la reconciliation d'un paiement course precis.

### `POST /admin/payments/topups/{topup_id}/reconcile`

Route admin. Force la reconciliation d'une recharge chauffeur precise.

Objectif support :

```text
repondre rapidement a la question : qui doit quoi a qui ?
```

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

Payload offre chauffeur `ride.new_request` :

```json
{
  "event": "ride.new_request",
  "ride_id": "ride-id",
  "pickup": {
    "lat": 5.3599,
    "lng": -4.0083,
    "address": "Carrefour Anador, Yopougon"
  },
  "dropoff_address": "Plateau, Rue du Commerce",
  "vehicle_category": "standard",
  "comfort_level": "comfort",
  "payment_method": "cash",
  "expires_in_seconds": 15
}
```

Ce payload ne contient pas `estimated_fare`, `final_fare`, `platform_commission`
ni `driver_payout_estimate`. Le chauffeur recupere ces champs via
`GET /v1/rides/{ride_id}` seulement a partir du statut `in_progress`.

---

## 12. Partenaires et flottes

Le module partenaire appartient a DiddiGo, car il impacte chauffeurs,
vehicules, matching, reporting et commissions metier VTC.

### Principes

```text
DiddiFreeID = identite globale user/admin
DiddiGo = roles partenaire locaux, affiliation chauffeur, vehicule partenaire
```

Un chauffeur peut avoir un seul partenaire actif. Un vehicule peut appartenir
au chauffeur solo ou a un partenaire. Un vehicule partenaire peut etre assigne
a un seul chauffeur actif a la fois.

Si un partenaire actif d'affiliation devient `suspended` ou `rejected`, ses
chauffeurs encore affilies ne peuvent pas passer en ligne et ne sont plus
eligibles au matching.

La commission partenaire est configurable par partenaire. En v3.2, DiddiGo
prepare le calcul/reporting; le payout automatique partenaire reste hors scope.

### `POST /admin/partners`

Route admin. Cree un partenaire en `pending_verification`.

Requete :

```json
{
  "name": "Fleet Abidjan Nord",
  "partner_type": "fleet_owner",
  "legal_name": "Fleet Abidjan Nord SARL",
  "contact_phone": "+2250700000000",
  "contact_email": "ops@example.com",
  "partner_commission_enabled": true,
  "partner_commission_mode": "percentage",
  "partner_commission_rate": 0.05,
  "registration_document_file_id": "file-id",
  "tax_document_file_id": "file-id",
  "representative_id_document_file_id": "file-id",
  "fleet_ownership_document_file_id": "file-id"
}
```

Reponse `201` :

```json
{
  "id": "partner-id",
  "name": "Fleet Abidjan Nord",
  "partner_type": "fleet_owner",
  "status": "pending_verification",
  "legal_name": "Fleet Abidjan Nord SARL",
  "contact_phone": "+2250700000000",
  "contact_email": "ops@example.com",
  "partner_commission_enabled": true,
  "partner_commission_mode": "percentage",
  "partner_commission_rate": 0.05,
  "kyc": {
    "registration_document_file_id": "file-id",
    "tax_document_file_id": "file-id",
    "representative_id_document_file_id": "file-id",
    "fleet_ownership_document_file_id": "file-id",
    "registration_document_url": null,
    "tax_document_url": null,
    "representative_id_document_url": null,
    "fleet_ownership_document_url": null,
    "submitted_at": "2026-09-07T09:00:00Z",
    "reviewed_at": null,
    "review_notes": null
  },
  "created_at": "2026-09-07T09:00:00Z",
  "updated_at": "2026-09-07T09:00:00Z"
}
```

### `GET /admin/partners`

Route admin. Liste les partenaires.

Query params :

```text
status       optionnel: pending_verification | active | suspended | rejected
partner_type optionnel: company | fleet_owner
page         defaut 1
page_size    defaut 20, max 100
```

### `GET /admin/partners/{partner_id}`

Route admin. Detail partenaire.

### `PATCH /admin/partners/{partner_id}`

Route admin. Modifie les informations et la commission partenaire.

Champs acceptes : memes champs que `POST /admin/partners`, tous optionnels.

### `POST /admin/partners/{partner_id}/activate`

Route admin. Passe le partenaire a `active`.

Depuis v3.2, cette route exige un KYC partenaire complet. Si le dossier est
incomplet, DiddiGo retourne `422 INVALID_PARTNER_KYC_DOCUMENTS`.

Documents obligatoires pour activation :

| Document | Champ DiddiGo | Purpose DiddiFiles recommande |
|---|---|---|
| Registre / immatriculation | `registration_document_file_id` | `diddigo_partner_kyc_registration` |
| Document fiscal | `tax_document_file_id` | `diddigo_partner_kyc_tax` |
| Piece representant | `representative_id_document_file_id` | `diddigo_partner_kyc_representative_id` |

Document optionnel :

| Document | Champ DiddiGo | Purpose DiddiFiles recommande |
|---|---|---|
| Justificatif propriete flotte | `fleet_ownership_document_file_id` | `diddigo_partner_kyc_fleet_ownership` |

Les champs legacy `*_document_url` restent acceptes temporairement pour le
backoffice, mais la source de verite doit etre le `file_id` DiddiFiles.

### `PATCH /admin/partners/{partner_id}/kyc`

Route admin. Soumet ou corrige le dossier KYC partenaire. Le partenaire repasse
en `pending_verification`.

Requete :

```json
{
  "registration_document_file_id": "file-id",
  "tax_document_file_id": "file-id",
  "representative_id_document_file_id": "file-id",
  "fleet_ownership_document_file_id": "file-id",
  "registration_document_url": "https://legacy.example/registration.pdf",
  "tax_document_url": "https://legacy.example/tax.pdf",
  "representative_id_document_url": "https://legacy.example/representative-id.jpg",
  "fleet_ownership_document_url": "https://legacy.example/fleet.pdf"
}
```

### `POST /admin/partners/{partner_id}/kyc/approve`

Route admin. Valide le KYC partenaire et active le partenaire.

Requete :

```json
{
  "notes": "Dossier partenaire OK"
}
```

### `POST /admin/partners/{partner_id}/kyc/reject`

Route admin. Rejette le KYC partenaire et passe le partenaire en `rejected`.

Requete :

```json
{
  "notes": "Document fiscal manquant"
}
```

### `POST /admin/partners/{partner_id}/suspend`

Route admin. Passe le partenaire a `suspended`.

Impact :

```text
chauffeurs affilies -> ne peuvent plus passer en ligne
matching -> filtre ces chauffeurs avec reason=partner_not_active:suspended
```

### `POST /admin/partners/{partner_id}/reject`

Route admin. Passe le partenaire a `rejected`.

### `POST /admin/partners/{partner_id}/members`

Route admin. Ajoute un utilisateur comme membre local du partenaire.

Requete :

```json
{
  "user_id": "identity-user-id",
  "role": "partner_manager"
}
```

Roles autorises :

```text
partner_manager
partner_operator
partner_viewer
```

### `GET /admin/partners/{partner_id}/members`

Route admin. Liste les membres du partenaire.

### `DELETE /admin/partners/{partner_id}/members/{member_id}`

Route admin. Desactive le membre, sans supprimer l'historique.

### `GET /partners/me`

Route utilisateur authentifie. Retourne les partenaires auxquels l'utilisateur
appartient.

Reponse :

```json
{
  "partners": [
    {
      "id": "partner-id",
      "name": "Fleet Abidjan Nord",
      "partner_type": "fleet_owner",
      "status": "active",
      "role": "partner_manager",
      "membership_id": "membership-id"
    }
  ]
}
```

### `POST /admin/partners/{partner_id}/drivers`

Route admin. Affilie un chauffeur au partenaire.

Requete :

```json
{
  "driver_id": "driver-profile-id"
}
```

Regle : un chauffeur ne peut avoir qu'une affiliation partenaire active.

### `GET /admin/partners/{partner_id}/drivers`

Route admin. Liste les affiliations chauffeur actives.

### `DELETE /admin/partners/{partner_id}/drivers/{driver_id}`

Route admin. Termine l'affiliation active.

### `POST /admin/partners/{partner_id}/vehicles/{vehicle_id}/assign`

Route admin. Marque le vehicule comme vehicule partenaire et l'assigne a un
chauffeur deja affilie a ce partenaire.

Requete :

```json
{
  "driver_id": "driver-profile-id"
}
```

Regles :

```text
partenaire doit etre active
chauffeur doit etre affilie au partenaire
vehicule ne doit pas avoir une assignation active
```

### `POST /admin/partners/{partner_id}/vehicles`

Route admin. Cree directement un vehicule appartenant au partenaire et
l'assigne au chauffeur cible.

Requete :

```json
{
  "driver_id": "driver-profile-id",
  "plate_number": "CE-987-AA",
  "make": "Toyota",
  "model": "Corolla",
  "color": "noir",
  "category": "standard",
  "comfort_level": "comfort",
  "registration_document_file_id": "file-id",
  "insurance_document_file_id": "file-id",
  "technical_inspection_document_file_id": "file-id",
  "transport_authorization_document_file_id": "file-id",
  "vehicle_front_photo_file_id": "file-id",
  "vehicle_back_photo_file_id": "file-id",
  "vehicle_left_photo_file_id": "file-id",
  "vehicle_right_photo_file_id": "file-id",
  "vehicle_interior_photo_file_id": "file-id"
}
```

Reponse :

```json
{
  "vehicle": {
    "id": "vehicle-id",
    "driver_id": "driver-profile-id",
    "owner_type": "partner",
    "partner_id": "partner-id",
    "verification_status": "pending_verification"
  },
  "assignment": {
    "id": "assignment-id",
    "partner_id": "partner-id",
    "vehicle_id": "vehicle-id",
    "driver_id": "driver-profile-id",
    "active": true
  }
}
```

Regles :

```text
partenaire doit etre active
chauffeur doit exister dans driver_profiles
si chauffeur non affilie, DiddiGo cree l'affiliation automatiquement
si chauffeur deja affilie ailleurs, 409 DRIVER_ALREADY_AFFILIATED
vehicule cree avec owner_type=partner, partner_id=partner_id
vehicule cree avec verification_status=pending_verification
le chauffeur ne peut pas passer en ligne tant que le KYV vehicule n'est pas approuve
```

### `POST /admin/partners/{partner_id}/vehicles/{vehicle_id}/unassign`

Route admin. Termine l'assignation active du vehicule.

### Erreurs partenaires

| HTTP | Code | Sens |
|---|---|---|
| `403` | `PARTNER_SUSPENDED` | Chauffeur bloque car partenaire non actif |
| `404` | `PARTNER_NOT_FOUND` | Partenaire introuvable |
| `404` | `PARTNER_MEMBER_NOT_FOUND` | Membre partenaire introuvable |
| `404` | `VEHICLE_NOT_FOUND` | Vehicule introuvable |
| `404` | `VEHICLE_ASSIGNMENT_NOT_FOUND` | Assignation vehicule introuvable |
| `409` | `PARTNER_NOT_ACTIVE` | Operation reservee a un partenaire actif |
| `409` | `DRIVER_ALREADY_AFFILIATED` | Chauffeur deja affilie a un partenaire actif |
| `409` | `DRIVER_NOT_AFFILIATED` | Chauffeur non affilie au partenaire requis |
| `409` | `VEHICLE_ALREADY_ASSIGNED` | Vehicule deja assigne a un chauffeur actif |
| `409` | `PLATE_ALREADY_REGISTERED` | Plaque vehicule deja enregistree |
| `422` | `INVALID_PARTNER_TYPE` | Type partenaire invalide |
| `422` | `INVALID_PARTNER_STATUS` | Statut partenaire invalide |
| `422` | `INVALID_PARTNER_ROLE` | Role partenaire invalide |
| `422` | `INVALID_PARTNER_COMMISSION` | Commission partenaire invalide |
| `422` | `INVALID_PARTNER_KYC_DOCUMENTS` | Dossier KYC partenaire incomplet |
| `422` | `INVALID_VEHICLE_CATEGORY` | Categorie vehicule invalide |
| `422` | `INVALID_COMFORT_LEVEL` | Niveau de confort invalide |
| `500` | `PARTNER_VEHICLE_REPOSITORY_MISSING` | Configuration backend incomplete pour creation vehicule partenaire |

---

## 13. Hors Scope v3.2

```text
DiddiSend
DiddiScore
dispatch urgence complet
wallet partenaire complet
payout automatique partenaire
contrat physique /v2 ou /v3 dans l'URL
```
