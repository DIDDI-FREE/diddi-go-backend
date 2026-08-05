# DiddiGo - Contrat API v2

**Destine a :** equipes Frontend / Mobile / Backend DiddiGo
**Base URL staging :** `https://go-staging.diddifree.com/v1`
**Auth staging :** `https://auth-staging.diddifree.com`
**Format :** JSON exclusivement - `Content-Type: application/json`
**Version du contrat :** v2, suite au basculement vers DiddiAuth / DiddiFreeID

Ce contrat remplace le contrat v1 pour les nouveaux developpements.

Important : le prefixe HTTP reste actuellement `/v1`. Le terme "v2" designe ici
la version du contrat fonctionnel, pas encore une URL `/v2`.

---

## 0. Principe General

DiddiGo ne doit plus etre la source d'authentification.

```text
DiddiAuth / DiddiFreeID = identite, OTP, tokens, role global user/admin
DiddiGo = courses, chauffeur, vehicule, paiement, regles metier VTC
```

Le token ne dit pas si quelqu'un est chauffeur DiddiGo. Il dit seulement :

```text
sub = identifiant utilisateur DiddiAuth
role = user ou admin
status = active / suspended / pending_verification
```

DiddiGo decide ensuite les droits metier avec ses propres tables :

```text
ride.driver_profiles
ride.vehicles
ride.rides
payment.transactions
```

---

## 1. Authentification

Le frontend se connecte sur DiddiAuth, pas sur DiddiGo.

Endpoints DiddiAuth staging :

```text
POST https://auth-staging.diddifree.com/auth/register
POST https://auth-staging.diddifree.com/auth/otp/request
POST https://auth-staging.diddifree.com/auth/otp/verify
POST https://auth-staging.diddifree.com/auth/refresh
POST https://auth-staging.diddifree.com/auth/logout
```

Apres verification OTP, DiddiAuth retourne :

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiJ9...",
  "refresh_token": "opaque_refresh_token",
  "user": {
    "id": "2347c231-37f5-4f0b-ba0c-24413be9f2ab",
    "phone": "+237699000000",
    "full_name": "Awa Kone",
    "role": "user",
    "status": "active"
  }
}
```

Depuis DiddiFreeID v2.0, l'inscription peut aussi contenir `email`, et la
demande OTP peut choisir explicitement un canal :

```json
{ "phone": "+237699000000", "channel": "email" }
```

ou :

```json
{ "phone": "+237699000000", "channel": "telegram" }
```

La reponse DiddiFreeID indique le canal effectif :

```json
{
  "expires_in_seconds": 300,
  "retry_after_seconds": 60,
  "channel": "email"
}
```

Ce choix de canal ne change rien pour DiddiGo : apres verification OTP, le
frontend continue d'envoyer a DiddiGo le `access_token` DiddiFreeID.

Le frontend utilise ensuite le `access_token` DiddiAuth pour appeler DiddiGo :

```http
Authorization: Bearer <access_token>
```

Configuration backend attendue :

```env
IDENTITY_BASE_URL=https://auth-staging.diddifree.com
```

DiddiGo derive automatiquement :

```env
IDENTITY_JWKS_URL=https://auth-staging.diddifree.com/.well-known/jwks.json
IDENTITY_PROFILE_URL=https://auth-staging.diddifree.com/identity/v1/users/me
```

Si le token expire, DiddiGo repond `401 TOKEN_EXPIRED`. Le frontend doit appeler
DiddiAuth `/auth/refresh`, recevoir un nouveau `access_token`, rejouer la
requete, puis reconnecter le WebSocket si besoin.

Le frontend ne doit pas redemander un OTP toutes les 15 minutes.

---

## 2. Shadow User DiddiGo

Pour la phase 1, DiddiGo garde une table locale `auth.users`.

Mais cette table n'est plus la source d'auth. Elle devient un miroir technique
appele "shadow user".

Quand DiddiGo recoit un token DiddiAuth valide :

```text
1. DiddiGo lit sub, phone, full_name, role, status
2. DiddiGo verifie si auth.users.id = sub existe
3. Si non, DiddiGo cree la ligne
4. Si oui, DiddiGo met a jour les infos utiles
5. Les tables ride/payment peuvent utiliser cet id sans casser les FK
```

Pourquoi cette table existe encore :

```text
ride.rides.passenger_user_id pointe encore vers auth.users.id
ride.driver_profiles.user_id pointe encore vers auth.users.id
```

### Mapping Role Shadow

| Role DiddiAuth | Role shadow `auth.users` | Sens |
|---|---|---|
| `user` | `passenger` | utilisateur standard, peut utiliser le service passager |
| `admin` | `admin` | administrateur global |

Il n'y a plus besoin que DiddiAuth emette `role=driver` pour qu'un utilisateur
devienne chauffeur dans DiddiGo.

---

## 2.1 Profils Utilisateur

DiddiFreeID garde l'identite et le profil global :

```text
telephone
nom legal / nom global
nom affiche global
avatar
langue preferee
contact d'urgence general
role global user/admin
statut global du compte
```

DiddiGo ne duplique pas ces champs. DiddiGo garde seulement les extensions
metier propres au transport :

```text
ride.driver_profiles = profil chauffeur et KYC transport
ride.vehicles = vehicules chauffeur
notification.user_devices = tokens push pour alerte course
```

DiddiGo ne demande plus le role `driver` a DiddiFreeID. DiddiFreeID garde
seulement les roles globaux `user` et `admin`. Le droit chauffeur est un role
metier DiddiGo, base sur `ride.driver_profiles` et `ride.vehicles`.

---

## 3. Roles Metier DiddiGo

Les droits metier ne viennent pas du token. Ils viennent des donnees DiddiGo.

### Passager

Un utilisateur authentifie avec `role=user` peut creer une course. Il devient
passager par defaut dans DiddiGo.

### Chauffeur

Un utilisateur devient chauffeur DiddiGo uniquement quand il a :

```text
ride.driver_profiles.user_id = son user_id DiddiAuth
ride.driver_profiles.status = active
un vehicule actif dans ride.vehicles
```

Parcours chauffeur :

```text
1. login via DiddiAuth
2. creer le profil chauffeur DiddiGo
3. ajouter le vehicule
4. passer online
5. recevoir/accepter les courses
```

Le token peut rester `{ "role": "user" }`. Tant que DiddiGo trouve un profil
chauffeur actif, les actions chauffeur sont autorisees.

### Admin

Un token DiddiAuth avec `{ "role": "admin" }` permet de bypass certaines
restrictions metier. Un admin n'a pas besoin d'un `driver_profile` pour les
actions de controle.

---

## 4. Endpoints Auth Locaux DiddiGo

Ces routes existent encore pour compatibilite/dev local :

```text
POST /v1/auth/register
POST /v1/auth/otp/request
POST /v1/auth/otp/verify
POST /v1/auth/refresh
GET  /v1/auth/me
```

Mais en staging/prod, le frontend ne doit plus les utiliser pour login. Le login
staging/prod doit passer par DiddiAuth.

---

## 5. Module Driver

### `POST /drivers/profile`

Creer le profil chauffeur metier DiddiGo. Accessible a tout utilisateur
authentifie.

**Requete**

```json
{
  "license_number": "CI-123456",
  "legal_name": "Awa Kone",
  "birth_date": "1992-04-20",
  "residence_address": "Cocody, Abidjan",
  "license_document_file_id": "8a1a0f2e-30e7-4436-a8ea-c12a1f76f3c1",
  "national_id_document_file_id": "45a14448-7bc7-4a21-972b-ff61585a571f",
  "selfie_document_file_id": "f9ac4c34-9c51-4772-a2d0-38bfb55bf3d9",
  "license_document_url": "https://cdn.example/license.jpg",
  "national_id_document_url": "https://cdn.example/id.jpg",
  "selfie_document_url": "https://cdn.example/selfie.jpg"
}
```

Seul `license_number` est obligatoire pour compatibilite. Les autres champs
constituent le dossier KYC chauffeur DiddiGo.

Pour les nouveaux clients, les documents doivent etre uploades via DiddiFiles
avant cet appel. DiddiGo stocke uniquement les `*_file_id` retournes par
DiddiFiles. Les champs `*_document_url` sont conserves temporairement pour
compatibilite legacy et ne doivent plus etre la source de verite.

Important : DiddiGo n'expose pas `/v1/files/*`. Les fichiers passent par le
service separe DiddiFiles :

```text
Staging DiddiFiles: https://diddifiles-staging.diddifree.com/v1
Production DiddiFiles: https://diddifiles.diddifree.com/v1
```

Routes DiddiFiles utilisees par le frontend :

```http
POST /files/upload-session
POST /files/{file_id}/confirm
GET /files/{file_id}
POST /files/{file_id}/download-url
```

Le token DiddiFreeID reste normalement `role=user`. Le frontend ne doit pas
attendre un `role=driver` central pour continuer le parcours chauffeur.

**Reponse `201`**

```json
{
  "id": "driver-profile-id",
  "user_id": "diddiauth-user-id",
  "license_number": "CI-123456",
  "status": "active",
  "rating_avg": 5.0,
  "rating_count": 0,
  "kyc": {
    "legal_name": "Awa Kone",
    "birth_date": "1992-04-20",
    "residence_address": "Cocody, Abidjan",
    "license_document_file_id": "8a1a0f2e-30e7-4436-a8ea-c12a1f76f3c1",
    "national_id_document_file_id": "45a14448-7bc7-4a21-972b-ff61585a571f",
    "selfie_document_file_id": "f9ac4c34-9c51-4772-a2d0-38bfb55bf3d9",
    "license_document_url": "https://cdn.example/license.jpg",
    "national_id_document_url": "https://cdn.example/id.jpg",
    "selfie_document_url": "https://cdn.example/selfie.jpg",
    "submitted_at": "2026-08-04T10:00:00+00:00",
    "reviewed_at": null,
    "review_notes": null
  }
}
```

### `POST /drivers/vehicle`

Ajouter un vehicule actif au profil chauffeur.

**Requete**

```json
{
  "plate_number": "CE-123-AA",
  "make": "Toyota",
  "model": "Yaris",
  "color": "gris",
  "category": "standard",
  "registration_document_file_id": "681effc5-4176-43d0-b42f-d0855fb2a7d8"
}
```

`registration_document_file_id` vient de DiddiFiles avec le purpose
`diddigo_vehicle_registration`.

### `POST /drivers/online`

Mettre le chauffeur dans le pool de matching.

Exige :

```text
driver_profile actif
vehicule actif
```

**Requete**

```json
{
  "lat": 5.3599,
  "lng": -4.0083
}
```

**Reponse `200`**

```json
{
  "status": "online",
  "driver_id": "driver-profile-id",
  "vehicle_id": "vehicle-id",
  "location": {
    "lat": 5.3599,
    "lng": -4.0083
  }
}
```

Erreurs principales :

| Code | Sens |
|---|---|
| `404 DRIVER_PROFILE_NOT_FOUND` | aucun profil chauffeur local |
| `403 DRIVER_NOT_VERIFIED` | profil chauffeur non actif |
| `409 NO_ACTIVE_VEHICLE` | aucun vehicule actif |

### `POST /drivers/offline`

Retire le chauffeur du pool de matching. Exige un profil chauffeur actif, sauf
admin.

---

## 6. Module Ride

### `POST /rides/pricing/estimate`

Estimer le prix d'une course avant creation.

Source normale :

```text
AbidjanMaps /api/v1/route
```

DiddiGo utilise uniquement les donnees geographiques :

```text
route.distance_m -> distance_km
route.duration_s -> duration_seconds
```

Politique importante :

```text
DiddiMap / AbidjanMaps = fournisseur unique distance, duree, lieux
DiddiGo = proprietaire unique de la politique de pricing VTC
```

Si AbidjanMaps retourne aussi `price.amount`, DiddiGo l'ignore. Le prix final
vient des regles DiddiGo :

```text
ride.pricing_rules si une regle active existe
sinon formule DiddiGo documentee par defaut :
estimated_fare = base_fare + distance_km * price_per_km
```

Valeurs par defaut actuelles si aucune regle n'est seedee :

```text
base_fare = 250 XOF
price_per_km = 240 XOF
surge_multiplier = 1.0
```

Il n'y a plus de fallback geographique silencieux. Si AbidjanMaps est
indisponible ou repond avec une forme inattendue, DiddiGo retourne une erreur
documentee.

**Requete**

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
  "vehicle_category": "standard"
}
```

**Reponse `200`**

```json
{
  "estimated_fare": 3100,
  "currency": "XOF",
  "distance_km": 11.876,
  "duration_seconds": 983,
  "surge_multiplier": 1.0
}
```

Erreurs DiddiMap :

| HTTP | Code | Sens |
|---|---|---|
| `503` | `DIDDIMAP_UNAVAILABLE` | DiddiMap/AbidjanMaps indisponible ou timeout |
| `502` | `DIDDIMAP_INVALID_RESPONSE` | reponse DiddiMap invalide ou non reconnue |

### `GET /places/search`

Rechercher une adresse ou un lieu via DiddiMap/AbidjanMaps.

Cette route sert aux champs pickup/dropoff dans l'application.

Query params :

```text
q        texte recherche, min 2 caracteres
bias_lat optionnel, latitude position utilisateur
bias_lng optionnel, longitude position utilisateur
limit    optionnel, defaut 10, max 20
```

Exemple :

```text
GET /v1/places/search?q=Plateau&bias_lat=5.3599&bias_lng=-4.0083
```

Reponse `200` :

```json
[
  {
    "label": "Plateau, Abidjan",
    "lat": 5.3204,
    "lng": -4.0161
  }
]
```

Si DiddiMap/AbidjanMaps est indisponible ou repond avec un format invalide,
DiddiGo retourne une erreur documentee. Il ne retourne pas une liste vide
silencieuse.

Erreurs DiddiMap :

| HTTP | Code | Sens |
|---|---|---|
| `503` | `DIDDIMAP_UNAVAILABLE` | DiddiMap/AbidjanMaps indisponible ou timeout |
| `502` | `DIDDIMAP_INVALID_RESPONSE` | reponse DiddiMap invalide ou non reconnue |

### `POST /rides`

Creer une demande de course. Accessible a tout utilisateur authentifie `user`
ou `admin`.

**Requete**

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
  "scheduled_at": null
}
```

**Reponse `201`**

```json
{
  "ride_id": "ride-id",
  "status": "requested",
  "estimated_fare": 2500,
  "currency": "XOF",
  "requested_at": "2026-07-28T10:15:00Z"
}
```

Au moment de cette requete, le shadow user est cree automatiquement si besoin.

### `POST /rides/{ride_id}/accept`

Accepter une course proposee.

Exige :

```text
profil chauffeur DiddiGo actif
offre Redis encore valide
offre attribuee a ce chauffeur
```

**Reponse `200`**

```json
{
  "ride_id": "ride-id",
  "status": "matched",
  "driver_id": "driver-profile-id",
  "vehicle_id": "vehicle-id",
  "matched_at": "2026-07-28T10:15:42Z"
}
```

### `POST /rides/{ride_id}/decline`

Refuser une course proposee. Memes exigences metier que `accept`.

**Reponse `200`**

```json
{
  "ride_id": "ride-id",
  "reoffered": true
}
```

### `PATCH /rides/{ride_id}/status`

Mettre a jour l'etat d'une course.

Exige :

```text
profil chauffeur DiddiGo actif
ou token admin
```

**Requete**

```json
{
  "status": "driver_en_route"
}
```

### `GET /rides/{ride_id}`

Detail course.

### `GET /rides`

Historique pagine. Query params :

```text
page
page_size
role
status
from_date
to_date
```

---

## 7. Module Payment

### `POST /payments/{ride_id}/confirm-cash`

Confirmer le paiement cash.

Exige un profil chauffeur DiddiGo actif.

DiddiGo enregistre :

```text
payment.transactions.collected_by = ride.driver_profiles.id
```

Pas :

```text
auth.users.id
```

**Requete**

```json
{
  "amount_collected": 2500
}
```

**Reponse `200`**

```json
{
  "ride_id": "ride-id",
  "status": "collected",
  "amount": 2500,
  "currency": "XOF",
  "collected_at": "2026-07-28T10:35:20Z"
}
```

---

## 8. WebSocket

Connexion :

```text
wss://go-staging.diddifree.com/v1/ws?token=<access_token_diddiauth>
```

Le token est le meme `access_token` DiddiAuth que pour les routes HTTP.

Si le client fait un appel HTTP classique `GET /v1/ws`, DiddiGo retourne :

```json
{
  "code": "WEBSOCKET_UPGRADE_REQUIRED",
  "message": "Use ws:// or wss:// with an Upgrade: websocket handshake.",
  "path": "/v1/ws?token=<access_token>"
}
```

### Client vers serveur

Passager :

```json
{
  "event": "ride.subscribe",
  "ride_id": "ride-id"
}
```

Chauffeur :

```json
{
  "event": "driver.location_push",
  "ride_id": "ride-id",
  "location": {
    "lat": 5.3601,
    "lng": -4.0090
  },
  "heading": 134
}
```

`driver.location_push` exige un profil chauffeur actif si le token a
`role=user`.

### Serveur vers client

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
  "estimated_fare": 2500,
  "expires_in_seconds": 15
}
```

```json
{
  "event": "ride.status_changed",
  "ride_id": "ride-id",
  "status": "driver_en_route",
  "at": "2026-07-28T10:15:42Z"
}
```

```json
{
  "event": "ride.driver_location",
  "ride_id": "ride-id",
  "location": {
    "lat": 5.3601,
    "lng": -4.0090
  },
  "heading": 134,
  "at": "2026-07-28T10:16:00Z"
}
```

```json
{
  "event": "ride.no_driver_found",
  "ride_id": "ride-id"
}
```

Si le WebSocket ferme avec `4401`, le frontend doit refresh le token via
DiddiAuth, ouvrir un nouveau WebSocket, puis rappeler `GET /rides/{ride_id}`.

Le WebSocket ne rejoue pas les evenements manques.

### Limite mobile et notifications push v2.0

Le WebSocket est un canal temps reel, mais il ne garantit pas la reception des
demandes de course quand l'application chauffeur est suspendue, fermee, ou tuee
par le systeme.

Phase test :

```text
Android foreground service + WebSocket + driver.location_push regulier
```

Le front Android doit afficher une notification persistante pendant que le
chauffeur est en ligne, puis envoyer `driver.location_push` toutes les 3 a 5
secondes.

iOS et les apps tuees/force-stopped ne peuvent pas garder un WebSocket fiable.

Version 2.0 backend prevue :

```text
WebSocket = canal rapide quand l'app est active
FCM = canal push pour alerter/reveiller l'app quand le WebSocket n'est pas fiable
```

Chantiers backend v2.0 :

```text
driver_devices
device push_token
platform android/ios
push_provider fcm
ride offer push + websocket
offer timeout / accepted / declined / expired
```

Le matching ne devra pas dependre uniquement d'un WebSocket connecte pour
alerter un chauffeur.

### Devices et push tokens

Le frontend doit enregistrer le token FCM apres login, puis a chaque rotation
du token FCM. Sur iOS, il faut envoyer le token FCM emis par Firebase
Messaging, pas le token APNs brut.

#### `POST /devices/register`

**Requete**

```json
{
  "platform": "android",
  "push_provider": "fcm",
  "push_token": "fcm-device-token",
  "device_id": "optional-stable-device-id"
}
```

`push_provider` est optionnel :

```text
android -> fcm
ios     -> fcm
```

`fcm` est le seul provider supporte par DiddiGo. Pour iOS, Firebase utilise
APNs en interne si le projet Firebase et l'app iOS sont bien configures cote
Apple/Firebase.

**Reponse `200`**

```json
{
  "status": "registered",
  "id": "device-row-id",
  "platform": "android",
  "push_provider": "fcm"
}
```

#### `POST /devices/unregister`

Appeler au logout ou quand un token devient invalide.

```json
{
  "push_token": "fcm-device-token"
}
```

**Reponse `200`**

```json
{
  "status": "unregistered"
}
```

### Envoi ride.new_request

Quand le matching trouve un chauffeur, DiddiGo tente :

```text
1. WebSocket ride.new_request si le socket chauffeur est connecte
2. Push notification FCM pour les devices fcm enregistres
```

Payload push data :

```json
{
  "event": "ride.new_request",
  "ride_id": "ride-id",
  "expires_in_seconds": "15"
}
```

Note iOS : l'envoi iOS passe aussi par FCM. Firebase relaie ensuite vers APNs
en interne si l'app iOS et le projet Firebase sont configures correctement.
DiddiGo ne stocke pas de token APNs brut et ne configure pas de credentials
Apple APNs.

---

## 9. Format Erreur

Toutes les erreurs HTTP DiddiGo gardent ce format :

```json
{
  "error": {
    "code": "RIDE_NOT_FOUND",
    "message": "Aucune course trouvee avec cet identifiant.",
    "details": null
  }
}
```

Codes importants ajoutes ou clarifies en v2 :

| Code | Sens |
|---|---|
| `TOKEN_MISSING` | aucun token transmis |
| `TOKEN_INVALID` | token invalide |
| `TOKEN_EXPIRED` | token expire |
| `USER_NOT_VERIFIED` | compte DiddiAuth non actif |
| `DRIVER_PROFILE_NOT_FOUND` | l'utilisateur n'a pas de profil chauffeur DiddiGo |
| `DRIVER_NOT_VERIFIED` | profil chauffeur non actif |
| `NO_ACTIVE_VEHICLE` | chauffeur sans vehicule actif |
| `WEBSOCKET_UPGRADE_REQUIRED` | `/ws` appele en HTTP au lieu de WebSocket |

---

## 10. Enums Frontend

| Enum | Valeurs |
|---|---|
| `identity.role` | `user`, `admin` |
| `shadow_user.role` | `passenger`, `admin` |
| `driver_profile.status` | `pending_verification`, `active`, `suspended`, `offline` |
| `vehicle.category` | `standard`, `comfort`, `van` |
| `ride.status` | `requested`, `matched`, `driver_en_route`, `in_progress`, `completed`, `cancelled_by_passenger`, `cancelled_by_driver`, `no_driver_found` |
| `payment.status` | `pending`, `collected`, `disputed` |

---

## 11. Notes de Migration v1 vers v2

### Pour Flutter

Changer le login :

```text
ancien : DiddiGo /v1/auth/*
nouveau : DiddiAuth https://auth-staging.diddifree.com/auth/*
```

Garder pour DiddiGo :

```text
Authorization: Bearer <access_token_diddiauth>
wss://go-staging.diddifree.com/v1/ws?token=<access_token_diddiauth>
```

Ne pas essayer de transformer `role=user` en `driver` cote Flutter.

Pour savoir si l'utilisateur est chauffeur DiddiGo :

```text
appeler /v1/drivers/me
si 404 DRIVER_PROFILE_NOT_FOUND => afficher onboarding chauffeur
si status active + vehicle => chauffeur operationnel
```

### Pour Backend

Phase 1 :

```text
auth.users reste present
auth.users devient shadow technique
DiddiAuth reste source de verite auth
driver_profiles devient source de verite role chauffeur
```

Phase 2 future :

```text
retirer progressivement les FK vers auth.users
remplacer par identity_user_id dans chaque module
supprimer les endpoints auth locaux de DiddiGo en prod
```

---

## 12. Hors Scope v2

Pas encore inclus :

```text
back-office admin complet
validation KYC manuelle
mobile money / wallet
suppression totale de auth.users
endpoint /v2 physique
```
