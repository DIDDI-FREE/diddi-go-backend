# DiddiGo - Brief frontend ajouts recents

Ce brief resume les changements recents a consommer cote mobile/frontend.

## 1. Auth DiddiFreeID

Le frontend se connecte sur DiddiFreeID, puis appelle DiddiGo avec :

```http
Authorization: Bearer <access_token>
```

Le token DiddiFreeID indique seulement le role global :

```text
user
admin
```

Ne pas attendre `role=driver` dans le JWT pour afficher le parcours chauffeur.
DiddiGo decide les droits chauffeur avec son profil metier local.

DiddiFreeID v2.0 supporte aussi l'OTP par e-mail. Cote frontend, le login peut
demander explicitement le canal :

```json
{ "phone": "+237699000000", "channel": "email" }
```

La reponse DiddiFreeID retourne le canal effectif (`email`, `telegram` ou
`logging`). Pour DiddiGo, rien ne change : une fois l'OTP verifie, le frontend
utilise toujours le meme `access_token` Bearer.

## 2. Profil global utilisateur

Ces champs appartiennent a DiddiFreeID, pas a DiddiGo :

```text
full_name
email
language
photo_url
status global
```

Pour modifier ces champs, utiliser DiddiFreeID :

```http
PATCH /identity/v1/users/me
```

## 3. KYC chauffeur DiddiGo

Le dossier chauffeur est cree dans DiddiGo :

```http
POST /v1/drivers/profile
```

Payload :

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

`license_number` reste obligatoire. Les autres champs sont optionnels mais
recommandes pour le dossier KYC.

Nouveau flux fichiers :
- uploader les documents dans DiddiFiles avec `module_owner=diddigo`
- utiliser les purposes `diddigo_driver_kyc_license`,
  `diddigo_driver_kyc_national_id`, `diddigo_driver_kyc_selfie`
- appeler `POST /v1/files/{file_id}/confirm`
- envoyer ensuite les `*_document_file_id` a DiddiGo

Les champs `*_document_url` restent acceptes uniquement pour compatibilite
temporaire. Le frontend ne doit plus construire d'URL permanente comme source
de verite.

Apres creation, DiddiGo ne demande pas `role=driver` a DiddiFreeID. Le droit
chauffeur est local a DiddiGo et depend du profil chauffeur DiddiGo.

Pour le vehicule, `POST /v1/drivers/vehicle` accepte aussi :

```json
{
  "registration_document_file_id": "681effc5-4176-43d0-b42f-d0855fb2a7d8"
}
```

Ce fichier doit etre cree dans DiddiFiles avec le purpose
`diddigo_vehicle_registration`.

## 4. Recherche de lieux

Utiliser :

```http
GET /v1/places/search?q=plateau&bias_lat=5.3599&bias_lng=-4.0083&limit=10
```

DiddiGo relaie vers AbidjanMaps/DiddiMap :

```text
/api/v1/geocoding/search
```

Regles frontend :

- Debounce avant appel API.
- Envoyer `bias_lat` et `bias_lng` si la position utilisateur existe.
- Utiliser `limit` pour limiter les suggestions.
- Afficher `label`.
- Utiliser `lat` et `lng` retournes pour pickup/dropoff.

## 5. Push notifications

Le backend DiddiGo utilise FCM uniquement, Android et iOS.

```http
POST /v1/devices/register
POST /v1/devices/unregister
```

Sur iOS, l'application doit envoyer un token FCM Firebase Messaging, pas un
token APNs brut. Firebase relaie ensuite vers APNs en interne.

## 6. WebSocket chauffeur

Le WebSocket reste le canal temps reel quand l'application est active.

```text
GET /v1/ws?token=<access_token>
```

En phase test Android, garder aussi le foreground service et envoyer :

```text
driver.location_push toutes les 3 a 5 secondes
```

## 7. Messaging et appels

Pas encore implemente dans DiddiGo. A traiter comme un futur module separe,
probablement `communication`, avec acces limite aux rides concernees.
