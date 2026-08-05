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

---

## 2. Enums

| Enum | Valeurs |
|---|---|
| `identity.role` | `user`, `admin` |
| `vehicle.category` | `standard`, `comfort`, `van` |
| `comfort_level` | `standard`, `comfort`, `premium` |
| `payment_method` | `cash`, `wave`, `diddipay` |
| `ride.status` | `requested`, `matched`, `driver_en_route`, `in_progress`, `completed`, `cancelled_by_passenger`, `cancelled_by_driver`, `no_driver_found` |
| `payment.status` | `pending`, `collected`, `disputed` |

Note produit : on garde les categories vehicule existantes. `comfort_level`
devient le niveau commercial de confort.

---

## 3. Places

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

## 4. Pricing

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

## 5. Rides

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

`payment_method` accepte deja `cash`, `wave`, `diddipay`. En production initiale,
le paiement operationnel reste `cash`; `wave` et `diddipay` sont prepares mais
pas encore connectes a un provider.

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

## 6. Traces GPS REST

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

---

## 7. Share Ride

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

## 8. Urgence

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

## 9. Paiements

### `GET /payments/{ride_id}`

Si aucune transaction n'existe encore, DiddiGo retourne une transaction logique
pending avec la methode demandee sur la course.

### `POST /payments/{ride_id}/prepare`

Prepare la transaction avant connexion provider.

Requete :

```json
{
  "method": "wave"
}
```

Reponse :

```json
{
  "ride_id": "ride-id",
  "status": "pending",
  "method": "wave",
  "amount": 3100,
  "currency": "XOF",
  "provider": "wave",
  "provider_status": "not_connected"
}
```

Pour `cash`, `provider_status` vaut `local`.

### `POST /payments/{ride_id}/confirm-cash`

Confirme l'encaissement cash par le chauffeur.

---

## 10. WebSocket et push

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

## 11. Hors Scope v3

```text
DiddiSend
DiddiScore
provider Wave reel
provider DiddiPay reel
dispatch urgence complet
map-matching DiddiMap Core officiel
contrat physique /v2 ou /v3 dans l'URL
```
