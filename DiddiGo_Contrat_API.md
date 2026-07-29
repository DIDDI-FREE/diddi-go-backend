# DiddiGo — Contrat API

**Destiné à :** équipes Frontend / Mobile (app passager, app chauffeur)
**Base URL (dev) :** `https://api-dev.diddigo.app/v1`
**Format :** JSON exclusivement · `Content-Type: application/json`
**Référence architecture :** DiddiFree — Architecture applicative modulaire & Conception DiddiGo (v4)

Ce document est un **contrat** : les champs, types et codes ci-dessous sont ce que le frontend peut
attendre dès aujourd'hui, indépendamment de l'état d'avancement réel du backend. Toute évolution
incompatible sera versionnée (`/v2`), jamais poussée en silence sur `/v1`.

---

## 0. Conventions générales

### Authentification

Toutes les routes sauf `POST /auth/otp/request`, `POST /auth/otp/verify`, `POST /auth/register` exigent :

```
Authorization: Bearer <access_token>
```

- `access_token` : JWT, durée de vie **15 min**.
- `refresh_token` : durée de vie **30 jours**, utilisé uniquement sur `POST /auth/refresh`.
- Un `access_token` expiré renvoie `401` avec `error.code = "TOKEN_EXPIRED"` — le front doit alors
  appeler `/auth/refresh` automatiquement et rejouer la requête une fois, sans intervention utilisateur.

### Format d'erreur (uniforme sur toutes les routes)

```json
{
  "error": {
    "code": "RIDE_NOT_FOUND",
    "message": "Aucune course trouvée avec cet identifiant.",
    "details": null
  }
}
```

`code` est stable et destiné à la logique du front (switch/case) ; `message` est destiné à l'affichage
direct à l'utilisateur, déjà en français. `details` porte des informations structurées optionnelles
(ex. liste des champs invalides sur un `422`).

### Codes HTTP utilisés

| Code | Signification |
|---|---|
| `200` | Succès (lecture ou action) |
| `201` | Ressource créée |
| `400` | Requête malformée |
| `401` | Non authentifié / token invalide ou expiré |
| `403` | Authentifié mais non autorisé sur cette ressource |
| `404` | Ressource inexistante |
| `409` | Conflit d'état (ex. annuler une course déjà terminée) |
| `422` | Validation de champs échouée |
| `429` | Trop de requêtes (ex. OTP demandé trop souvent) |
| `500` | Erreur serveur |

### Pagination (routes de liste)

Query params : `?page=1&page_size=20` (défaut `page_size=20`, max `100`).

```json
{
  "data": [ /* ... */ ],
  "pagination": { "page": 1, "page_size": 20, "total_items": 47, "total_pages": 3 }
}
```

### Dates et unités

- Toutes les dates : ISO 8601 UTC, ex. `"2026-08-04T14:20:00Z"`.
- Montants : `NUMERIC`, en unité entière de la devise (XOF n'a pas de sous-unité) — jamais de centimes.
- Distances : kilomètres (`NUMERIC`, 2 décimales). Durées : secondes (`INTEGER`).

---

## 1. Module `auth`

### `POST /auth/register`

Inscription initiale (numéro + nom). Ne connecte pas encore l'utilisateur — l'OTP le fait.

**Requête**
```json
{ "phone": "+2250700000000", "full_name": "Awa Koné", "role": "passenger" }
```
`role` : `"passenger"` ou `"driver"`.

**Réponse `201`**
```json
{ "user_id": "b3e1...", "phone": "+2250700000000", "status": "pending_verification" }
```

**Erreurs** : `422` (`INVALID_PHONE_FORMAT`), `409` (`PHONE_ALREADY_REGISTERED`)

---

### `POST /auth/otp/request`

**Requête**
```json
{ "phone": "+2250700000000" }
```

**Réponse `200`**
```json
{ "expires_in_seconds": 300, "retry_after_seconds": 60 }
```
Le front doit désactiver le bouton "renvoyer" pendant `retry_after_seconds`.

**Erreurs** : `429` (`OTP_RATE_LIMITED`, avec `details.retry_after_seconds`)

---

### `POST /auth/otp/verify`

**Requête**
```json
{ "phone": "+2250700000000", "code": "482913" }
```

**Réponse `200`**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "user": {
    "id": "b3e1...",
    "phone": "+2250700000000",
    "full_name": "Awa Koné",
    "role": "passenger",
    "status": "active"
  }
}
```

**Erreurs** : `400` (`OTP_INVALID`), `410` (`OTP_EXPIRED`)

---

### `POST /auth/refresh`

**Requête** : `{ "refresh_token": "..." }`
**Réponse `200`** : `{ "access_token": "...", "refresh_token": "..." }`
**Erreurs** : `401` (`REFRESH_TOKEN_INVALID`) → le front doit rediriger vers l'écran de connexion.

---

### `GET /auth/me`

**Réponse `200`**
```json
{ "id": "b3e1...", "phone": "+2250700000000", "full_name": "Awa Koné", "role": "passenger", "status": "active" }
```

---

## 2. Module `ride`

### Machine à états (à connaître impérativement côté front)

```
requested → matched → driver_en_route → in_progress → completed
    ↓            ↓
no_driver_found  cancelled_by_passenger / cancelled_by_driver
```

Le front ne doit jamais essayer de "deviner" une transition non listée ici (ex. `in_progress` ne peut
pas revenir à `matched`). Toute transition inconnue reçue par WebSocket doit être journalée et ignorée
sans crasher l'UI — l'API pourra ajouter des statuts intermédiaires plus tard (ex. `payment_pending`)
sans que ce soit une rupture de contrat.

### `POST /pricing/estimate`

À appeler **avant** la création de la course, pour afficher le prix estimé au passager.

**Requête**
```json
{
  "pickup": { "lat": 5.3599, "lng": -4.0083 },
  "dropoff": { "lat": 5.3167, "lng": -4.0333 },
  "vehicle_category": "standard"
}
```

**Réponse `200`**
```json
{
  "estimated_fare": 2500,
  "currency": "XOF",
  "distance_km": 8.4,
  "duration_seconds": 1140,
  "surge_multiplier": 1.0
}
```
Si `surge_multiplier > 1.0`, le front doit l'afficher explicitement à l'utilisateur avant réservation
(exigence produit : pas de surge caché).

**Erreurs** : `422` (`LOCATION_OUT_OF_SERVICE_AREA`)

---

### `POST /rides`

Crée une demande de course. Déclenche le matching côté serveur ; la réponse ne contient **pas** encore
de chauffeur assigné — le front doit écouter le WebSocket (section 4) pour la suite.

**Requête**
```json
{
  "pickup": { "lat": 5.3599, "lng": -4.0083, "address": "Carrefour Anador, Yopougon" },
  "dropoff": { "lat": 5.3167, "lng": -4.0333, "address": "Plateau, Rue du Commerce" },
  "vehicle_category": "standard",
  "scheduled_at": null
}
```
`scheduled_at` : `null` pour une course immédiate, sinon ISO 8601 pour une course programmée.

**Réponse `201`**
```json
{
  "ride_id": "c7f2...",
  "status": "requested",
  "estimated_fare": 2500,
  "currency": "XOF",
  "requested_at": "2026-07-28T10:15:00Z"
}
```

**Erreurs** : `422` (`INVALID_LOCATION`), `409` (`ACTIVE_RIDE_ALREADY_EXISTS` — un passager ne peut pas
avoir deux courses actives simultanément)

---

### `GET /rides/{ride_id}`

**Réponse `200`**
```json
{
  "id": "c7f2...",
  "status": "driver_en_route",
  "passenger": { "id": "b3e1...", "full_name": "Awa Koné" },
  "driver": {
    "id": "d891...",
    "full_name": "Yves Koffi",
    "rating_avg": 4.8,
    "phone": "+2250701111111",
    "vehicle": { "make": "Toyota", "model": "Yaris", "color": "gris", "plate_number": "CI-4429-AB" }
  },
  "pickup": { "lat": 5.3599, "lng": -4.0083, "address": "Carrefour Anador, Yopougon" },
  "dropoff": { "lat": 5.3167, "lng": -4.0333, "address": "Plateau, Rue du Commerce" },
  "estimated_fare": 2500,
  "final_fare": null,
  "currency": "XOF",
  "distance_km": 8.4,
  "duration_seconds": 1140,
  "requested_at": "2026-07-28T10:15:00Z",
  "matched_at": "2026-07-28T10:15:42Z",
  "started_at": null,
  "completed_at": null
}
```
`driver` est `null` tant que `status = "requested"` ou `"no_driver_found"`.

**Erreurs** : `404` (`RIDE_NOT_FOUND`), `403` (`RIDE_NOT_OWNED_BY_USER`)

---

### `GET /rides?role=passenger&status=completed`

Historique. Filtres optionnels : `role` (`passenger` \| `driver`, déduit du token sinon), `status`,
`from_date`, `to_date`. Réponse paginée (voir section 0).

```json
{
  "data": [
    { "id": "c7f2...", "status": "completed", "final_fare": 2500, "completed_at": "2026-07-28T10:35:00Z",
      "pickup_address": "Carrefour Anador, Yopougon", "dropoff_address": "Plateau, Rue du Commerce" }
  ],
  "pagination": { "page": 1, "page_size": 20, "total_items": 47, "total_pages": 3 }
}
```
Vue allégée volontairement — pas de détail chauffeur/véhicule dans la liste, seulement sur `GET /rides/{id}`.

---

### `PATCH /rides/{ride_id}/status`

Réservé au **chauffeur** (transitions `matched → driver_en_route → in_progress → completed`). Le front
passager n'appelle jamais cette route directement — il reçoit les changements par WebSocket.

**Requête**
```json
{ "status": "driver_en_route" }
```

**Réponse `200`** : la course mise à jour (même format que `GET /rides/{ride_id}`).

**Erreurs** : `409` (`INVALID_STATUS_TRANSITION`, avec `details.current_status` et `details.attempted_status`)

---

### `POST /rides/{ride_id}/cancel`

Appelable par passager ou chauffeur, selon le rôle du token.

**Requête**
```json
{ "reason": "passenger_no_show" }
```
Valeurs de `reason` : `"passenger_changed_mind"`, `"passenger_no_show"`, `"driver_unavailable"`,
`"found_alternative"`, `"other"`.

**Réponse `200`**
```json
{ "id": "c7f2...", "status": "cancelled_by_passenger", "cancelled_at": "2026-07-28T10:16:10Z" }
```

**Erreurs** : `409` (`RIDE_ALREADY_COMPLETED`, `RIDE_ALREADY_CANCELLED`)

---

### `POST /rides/{ride_id}/rating`

Un seul appel autorisé par rôle et par course (contrainte `UNIQUE(ride_id, rater_role)` en base).

**Requête**
```json
{ "rating": 5, "comment": "Trajet rapide, chauffeur ponctuel." }
```

**Réponse `201`** : `{ "id": "...", "ride_id": "c7f2...", "rating": 5 }`

**Erreurs** : `409` (`RATING_ALREADY_SUBMITTED`), `422` (`RATING_OUT_OF_RANGE`)

---

## 3. Module `payment` (cash au lancement)

### `POST /payments/{ride_id}/confirm-cash`

Appelé par le chauffeur à la fin de la course, après encaissement en espèces.

**Requête**
```json
{ "amount_collected": 2500 }
```

**Réponse `200`**
```json
{ "ride_id": "c7f2...", "status": "collected", "amount": 2500, "currency": "XOF", "collected_at": "2026-07-28T10:35:20Z" }
```

**Erreurs** : `409` (`RIDE_NOT_COMPLETED` — impossible de confirmer un paiement avant la fin de course),
`422` (`AMOUNT_MISMATCH`, si `amount_collected` diverge fortement de `final_fare` — tolérance à définir
avec le produit)

---

### `GET /payments/{ride_id}`

```json
{ "ride_id": "c7f2...", "status": "collected", "method": "cash", "amount": 2500, "currency": "XOF" }
```
`status` : `"pending"` \| `"collected"` \| `"disputed"`. `method` reste `"cash"` pour toutes les courses
au lancement — le champ existe déjà pour ne pas casser le contrat le jour où `mobile_money`/`wallet`
seront ajoutés.

---

## 4. WebSocket — temps réel

Connexion : `wss://api-dev.diddigo.app/v1/ws?token=<access_token>`

Un seul socket par session app, multiplexé par type d'événement (`event.type`) plutôt que des canaux
séparés — plus simple à gérer côté client qu'une reconnexion par canal.

### Événements reçus par le **passager** (une fois une course active)

```json
{ "event": "ride.status_changed", "ride_id": "c7f2...", "status": "driver_en_route", "at": "2026-07-28T10:15:42Z" }
```
```json
{ "event": "ride.driver_location", "ride_id": "c7f2...", "location": { "lat": 5.3601, "lng": -4.0090 }, "heading": 134, "at": "2026-07-28T10:16:00Z" }
```
```json
{ "event": "ride.no_driver_found", "ride_id": "c7f2..." }
```

### Événements reçus par le **chauffeur**

```json
{
  "event": "ride.new_request",
  "ride_id": "c7f2...",
  "pickup": { "lat": 5.3599, "lng": -4.0083, "address": "Carrefour Anador, Yopougon" },
  "dropoff_address": "Plateau, Rue du Commerce",
  "estimated_fare": 2500,
  "expires_in_seconds": 15
}
```
Le chauffeur a `expires_in_seconds` pour répondre via `POST /rides/{id}/accept` ou `/decline` (routes à
détailler avec le module matching) — passé ce délai, la demande est automatiquement réattribuée.

### Événement envoyé par le **chauffeur** (client → serveur)

```json
{ "event": "driver.location_push", "location": { "lat": 5.3601, "lng": -4.0090 }, "heading": 134 }
```
Fréquence attendue côté front : toutes les 3 à 5 secondes pendant une course active, arrêté en dehors.

### Reconnexion

En cas de coupure réseau (fréquent sur le terrain), le front doit reconnecter avec backoff exponentiel
(1s, 2s, 4s, 8s, plafond 30s) et rappeler `GET /rides/{ride_id}` une fois reconnecté pour resynchroniser
l'état — le WebSocket ne rejoue pas les événements manqués.

---

## 5. Enums de référence (à coder en dur côté front, pas en config distante pour l'instant)

| Enum | Valeurs |
|---|---|
| `ride.status` | `requested`, `matched`, `driver_en_route`, `in_progress`, `completed`, `cancelled_by_passenger`, `cancelled_by_driver`, `no_driver_found` |
| `vehicle_category` | `standard`, `comfort`, `van` |
| `user.role` | `passenger`, `driver`, `admin` |
| `cancel.reason` | `passenger_changed_mind`, `passenger_no_show`, `driver_unavailable`, `found_alternative`, `other` |
| `payment.status` | `pending`, `collected`, `disputed` |

---

## 6. Ce qui n'est volontairement pas encore dans ce contrat

- `POST /rides/{id}/accept` / `/decline` côté chauffeur — dépend du détail du moteur de matching, à
  spécifier dans une v1.1 de ce document.
- Endpoints d'administration (validation KYC chauffeur, suspension de compte).
- Tout endpoint `mobile_money`/`wallet` — le module `payment` reste cash-only jusqu'à nouvel ordre.

Si le front a besoin d'un de ces éléments plus tôt que prévu pour débloquer une maquette, dites-le —
mieux vaut l'ajouter ici proprement que de le improviser côté client.
