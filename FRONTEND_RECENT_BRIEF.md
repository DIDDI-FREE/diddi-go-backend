# DiddiGo - Brief frontend ajouts recents

Ce brief resume les changements recents a consommer cote mobile/frontend.

## 0. Contrat API v3

Le nouveau contrat de reference est :

```text
DiddiGo_Contrat_API_v3.md
```

Le prefixe public reste `/v1`. `v3` est la version fonctionnelle du contrat,
pas encore une URL `/v3`.

Ajouts majeurs :

- `comfort_level` sur pricing et creation de course.
- `vehicle_category` reste cote backend mais le frontend passager peut l'omettre
  pour le MVP; DiddiGo applique `standard` par defaut.
- pricing detaille avec commission plateforme et payout chauffeur estime.
- preparation `cash`, `wave`, `diddipay`.
- wallet chauffeur : solde, ledger, recharge DiddiPay/Wave.
- traces GPS chauffeur via REST.
- lien public de partage de course sans login.
- endpoint urgence course.

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

Important KYC :

- `POST /v1/drivers/profile` retourne maintenant `status=pending_verification`.
- Le chauffeur peut ajouter son vehicule pendant que le dossier est en attente.
- `POST /v1/drivers/online` retourne `403 DRIVER_NOT_VERIFIED` tant que l'admin
  n'a pas valide le dossier.
- L'ecran "Dossier KYC en cours de verification" doit etre affiche sur ce cas.
- Il n'y a plus d'auto-approbation en staging.

Nouveau flux fichiers :
- utiliser DiddiFiles sur son URL dediee, pas sur `go-staging`
- URL DiddiFiles : `https://diddifiles.diddifree.com/v1`
- uploader les documents dans DiddiFiles avec `module_owner=diddigo`
- utiliser les purposes `diddigo_driver_kyc_license`,
  `diddigo_driver_kyc_national_id`, `diddigo_driver_kyc_selfie`
- appeler `POST /v1/files/{file_id}/confirm`
- envoyer ensuite les `*_document_file_id` a DiddiGo

Important : `go-staging.diddifree.com` ne doit pas exposer `/v1/files/*`.
Les routes fichiers appartiennent au service separe DiddiFiles :

```http
POST https://diddifiles.diddifree.com/v1/files/upload-session
POST https://diddifiles.diddifree.com/v1/files/{file_id}/confirm
GET  https://diddifiles.diddifree.com/v1/files/{file_id}
POST https://diddifiles.diddifree.com/v1/files/{file_id}/download-url
```

Les champs `*_document_url` restent acceptes uniquement pour compatibilite
temporaire. Le frontend ne doit plus construire d'URL permanente comme source
de verite.

Apres creation, DiddiGo ne demande pas `role=driver` a DiddiFreeID. Le droit
chauffeur est local a DiddiGo et depend du profil chauffeur DiddiGo.

Routes admin KYC ajoutees :

```http
GET  /v1/drivers/kyc?status=pending_verification&page=1&page_size=20
GET  /v1/drivers/{driver_id}/kyc
POST /v1/drivers/{driver_id}/kyc/approve
POST /v1/drivers/{driver_id}/kyc/reject
```

Ces routes exigent un token DiddiFreeID `role=admin`.

Route chauffeur de correction/resoumission KYC :

```http
POST /v1/drivers/kyc/resubmit
```

Elle repasse le dossier a `pending_verification`, efface la derniere revue
admin et garde le meme `driver_profile_id`.

Catalogue d'erreurs DiddiGo :

```text
DiddiGo_Error_Catalog.md
```

Le frontend doit utiliser `error.code` pour piloter les etats UI. Exemples :

- `DRIVER_NOT_VERIFIED` : afficher "Dossier KYC en cours de verification".
- `DRIVER_PROFILE_NOT_FOUND` : proposer de creer le dossier chauffeur.
- `NO_ACTIVE_VEHICLE` : demander au chauffeur d'ajouter un vehicule.
- `DRIVER_KYC_STATUS_INVALID` : erreur de filtre back-office.

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

## 4.1 Pricing et comfort level

`POST /v1/rides/pricing/estimate` accepte maintenant :

```json
{
  "pickup": {"lat": 5.3599, "lng": -4.0083, "address": "Carrefour Anador"},
  "dropoff": {"lat": 5.3167, "lng": -4.0333, "address": "Plateau"},
  "comfort_level": "standard"
}
```

`vehicle_category` est optionnel. Pour reduire la friction UX, ne pas afficher
de choix categorie vehicule au passager pour le MVP: envoyer seulement
`comfort_level`.

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

Important :

- DiddiMap donne distance/duree.
- DiddiGo calcule le prix, la commission et le payout.
- Le prix varie avec `comfort_level` : `standard=1.00`, `comfort=1.15`,
  `premium=1.30`.
- Pas de fallback silencieux si DiddiMap echoue.
- Le prix final utilise la distance/duree reellement parcourues si le frontend
  a envoye des points GPS chauffeur pendant la course.

## 4.2 Creation de course

`POST /v1/rides` accepte maintenant aussi :

```json
{
  "comfort_level": "standard",
  "payment_method": "cash"
}
```

Le frontend peut omettre `vehicle_category`; DiddiGo mettra `standard` par
defaut. Pour la vague actuelle, l'ecran passager doit proposer uniquement :

```text
Standard
Confort
Premium
```

`payment_method` peut etre `cash`, `wave`, ou `diddipay`.

Regle importante :

```text
cash      = encaissement physique, confirme par le chauffeur dans DiddiGo
wave      = paiement numerique initialise par DiddiGo via DiddiPay
diddipay  = paiement numerique initialise par DiddiGo via DiddiPay
```

Le frontend n'appelle jamais DiddiPay directement.

Le matching exige maintenant :

```text
vehicle.category == ride.vehicle_category
```

`comfort_level` n'est plus un filtre dur de matching dans le MVP. Si
l'utilisateur choisit `premium`, le prix augmente, mais un chauffeur eligible
avec vehicule `standard` peut quand meme recevoir la course.

La reponse contient maintenant :

```json
{
  "payment_method": "cash"
}
```

## 4.3 Traces GPS chauffeur

Nouveau endpoint REST :

```http
POST /v1/rides/{ride_id}/location-samples
```

Reserve au chauffeur assigne.

Payload :

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

Le frontend peut continuer a utiliser le WebSocket `driver.location_push` pour
le temps reel. Cette route REST sert de canal controle/documente pour stocker
les traces et alimenter le partage public.

DiddiGo recalcule maintenant le prix final depuis ces traces. Le frontend doit
envoyer les samples chauffeur pendant la course; DiddiGo demarre la trace
DiddiMap, envoie les samples au moment de terminer, analyse la trace, puis
remplit `actual_distance_km`, `actual_duration_seconds`, `final_fare`,
`platform_commission` et le montant net chauffeur.

Pipeline retenu avec DiddiMap Core :

```text
DiddiGo collecte les traces chauffeur
DiddiGo demarre une trace DiddiMap au debut de course
DiddiGo envoie les positions via REST batch a la fin du ride
DiddiGo termine puis analyse la trace a la fin du ride
DiddiMap produira distance/duree reelles et insights
un admin validera/rejettera ces insights
les routes/scoring s'amelioreront ensuite
```

Impact frontend actuel :

- Envoyer les positions via `POST /v1/rides/{ride_id}/location-samples`.
- Continuer le WebSocket pour le temps reel/share ride.
- Lire les champs `pricing.actual_distance_km` et
  `pricing.actual_duration_seconds` dans le detail de course terminee.
- Si la finalisation retourne `DIDDIMAP_UNAVAILABLE` ou
  `DIDDIMAP_INVALID_RESPONSE`, afficher une erreur claire au chauffeur/support:
  la course n'a pas pu etre cloturee car l'analyse geographique a echoue.

## 4.4 Partage de course

Creer un lien :

```http
POST /v1/rides/{ride_id}/share-link
```

Reponse :

```json
{
  "ride_id": "ride-id",
  "share_token": "opaque-token",
  "expires_at": "2026-08-06T10:15:00Z",
  "public_path": "/v1/rides/shared/opaque-token"
}
```

Vue publique sans login :

```http
GET /v1/rides/shared/{token}
```

Cette vue doit afficher la position du chauffeur, pas celle du passager.

## 4.5 Urgence

Nouveau endpoint :

```http
POST /v1/rides/{ride_id}/emergency
```

Payload :

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

Le detail course expose aussi :

```json
{
  "emergency": {
    "status": "open",
    "requested_at": "2026-08-05T10:25:00Z"
  }
}
```

## 5. Push notifications

Le backend DiddiGo utilise FCM uniquement, Android et iOS.

```http
POST /v1/devices/register
POST /v1/devices/unregister
```

Sur iOS, l'application doit envoyer un token FCM Firebase Messaging, pas un
token APNs brut. Firebase relaie ensuite vers APNs en interne.

## 5.1 Paiement DiddiPay / Wave

Flux frontend officiel :

```text
1. Le passager choisit cash, wave ou diddipay.
2. L'app appelle DiddiGo: POST /v1/payments/{ride_id}/prepare.
3. DiddiGo relit le montant depuis sa base.
4. DiddiGo appelle DiddiPay cote serveur.
5. L'app execute uniquement le `next_action` retourne.
6. Au retour checkout ou apres attente mobile money, l'app relit GET /v1/payments/{ride_id}.
7. Le paiement est confirme seulement quand DiddiGo retourne status=succeeded.
```

Endpoint :

```http
POST /v1/payments/{ride_id}/prepare
```

Payload :

```json
{
  "method": "wave",
  "customer_email": "client@example.com",
  "customer_phone": "+2250700000000",
  "callback_url": "https://go-staging.diddifree.com/payments/return"
}
```

`callback_url` est une page de retour navigateur. Elle ne confirme pas le
paiement. DiddiGo expose maintenant cette page pour eviter un 404 si l'app
utilise l'URL backend :

```http
GET https://go-staging.diddifree.com/payments/return
```

Pour `wave` et `diddipay`, `customer_email` est obligatoire. DiddiGo appelle
DiddiPay cote backend; le frontend ne doit jamais connaitre `X-Service-Key`.
Le frontend ne transmet jamais le montant, `payer_user_id`, `payee_user_id`,
ni une cle service.

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
    "url": "https://checkout.paystack.com/example"
  }
}
```

Le frontend doit executer `next_action` :

- `redirect` : ouvrir l'URL de checkout.
- `mobile_money_prompt` : afficher l'attente de validation mobile money.
- `display_instructions` : afficher les instructions retournees.
- `await_confirmation` : afficher un etat d'attente.
- `none` : aucune action.

Important : le retour navigateur ne prouve pas le paiement. Apres retour ou
attente, relire :

```http
GET /v1/payments/{ride_id}
GET /v1/rides/{ride_id}
```

Seul `status=succeeded` cote paiement DiddiGo confirme le paiement digital.
Ne jamais faire passer une course en payee parce que le navigateur revient sur
une page `success`.

Si `POST /v1/payments/{ride_id}/prepare` est rejoue pour une transaction deja
creee, DiddiGo renvoie le meme paiement et conserve le `next_action` connu.

Le cash reste disponible via :

```http
POST /v1/payments/{ride_id}/confirm-cash
```

## 5.2 Wallet chauffeur, commission et recharge

Nouveaux endpoints chauffeur :

```http
GET  /v1/drivers/me/wallet
GET  /v1/drivers/me/wallet/ledger?page=1&page_size=20
POST /v1/drivers/me/wallet/topups
GET  /v1/drivers/me/wallet/topups/{topup_id}
```

`GET /v1/drivers/me/wallet` retourne :

```json
{
  "driver_id": "driver-profile-id",
  "balance": -248,
  "currency": "XOF",
  "min_balance": 0,
  "can_go_online": true
}
```

Pour le cash :

```text
le chauffeur encaisse le cash physiquement
DiddiGo debite le wallet chauffeur du montant de la commission plateforme
```

Pour DiddiPay/Wave :

```text
quand le paiement digital est confirme, DiddiGo credite le wallet chauffeur
du montant net chauffeur
```

Recharge chauffeur :

```json
{
  "amount": 5000,
  "method": "wave",
  "customer_email": "driver@example.com",
  "customer_phone": "+2250700000000",
  "callback_url": "https://go-staging.diddifree.com/wallet/return"
}
```

Le frontend execute `next_action` comme pour un paiement course.

Apres retour navigateur, relire :

```http
GET /v1/drivers/me/wallet/topups/{topup_id}
GET /v1/drivers/me/wallet
```

DiddiGo conserve maintenant `next_action`; donc `GET /v1/drivers/me/wallet/topups/{topup_id}`
peut encore retourner l'URL checkout tant que la recharge est en
`requires_action`.

Le solde ne change que quand le backend recoit ou reconcilie un statut
`succeeded` depuis DiddiPay.

DiddiGo expose aussi une page de retour navigateur pour les recharges :

```http
GET https://go-staging.diddifree.com/wallet/return
```

Si `POST /v1/drivers/online` retourne :

```text
DRIVER_BALANCE_TOO_LOW
```

Afficher un message simple et proposer la recharge.

Endpoints admin/support :

```http
GET /v1/admin/drivers/{driver_id}/wallet
GET /v1/admin/drivers/{driver_id}/wallet/ledger
POST /v1/admin/payments/reconcile
POST /v1/admin/payments/rides/{ride_id}/reconcile
POST /v1/admin/payments/topups/{topup_id}/reconcile
```

Ces routes de reconciliation sont des outils admin/support. L'app passager ou
chauffeur ne les appelle pas.

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

## 8. Staging / Portainer

Le correctif recent concerne le deploiement backend, pas les endpoints
frontend. Les URLs API ne changent pas :

```text
API DiddiGo staging: https://go-staging.diddifree.com/v1
Auth staging: https://auth-staging.diddifree.com
WebSocket staging: wss://go-staging.diddifree.com/v1/ws?token=<access_token>
```

Cote Portainer, `DATABASE_URL` et `REDIS_URL` ne sont plus obligatoires si la
stack utilise les services internes `db` et `redis`.

Variables minimales a fournir dans la stack :

```env
JWT_SECRET=<random-32+-characters-secret>
POSTGRES_PASSWORD=<strong-password>
CORS_ORIGINS=https://go-staging.diddifree.com
```

Variables optionnelles selon environnement :

```env
BACKEND_PORT=18000
APP_ENV=production
IDENTITY_BASE_URL=https://auth-staging.diddifree.com
DIDDIMAP_BASE_URL=http://abidjanmaps-backend-staging.diddifree.com
PUSH_ENABLED=true
FCM_PROJECT_ID=<firebase-project-id>
FCM_SERVICE_ACCOUNT_JSON=<firebase-service-account-json-one-line>
DIDDIPAY_BASE_URL=https://pay-api-staging.diddifree.com/payfund/v1
DIDDIPAY_CLIENT_ID=diddigo
DIDDIPAY_SERVICE_KEY=<secret-backend-diddigo>
DIDDIPAY_CALLBACK_SECRET=<secret-callback-diddipay-vers-diddigo>
DIDDIPAY_HTTP_TIMEOUT_SECONDS=15
DIDDIGO_PAYMENT_CALLBACK_URL=https://go-staging.diddifree.com/payments/return
PAYMENT_RECONCILIATION_ENABLED=true
PAYMENT_RECONCILIATION_INTERVAL_SECONDS=300
PAYMENT_RECONCILIATION_BATCH_SIZE=50
```

`POSTGRES_PASSWORD` est obligatoire dans Portainer. Sans cette variable,
Compose refuse de charger la stack.

En staging, `IDENTITY_BASE_URL` et `DIDDIMAP_BASE_URL` ont deja des valeurs par
defaut dans `docker-compose.portainer.yml`. Les surcharger seulement si on vise
un autre environnement.

Ne pas envoyer `DATABASE_URL` ni `REDIS_URL` depuis le frontend. Ce sont des
variables internes backend. Le frontend doit seulement appeler les URLs HTTP et
WebSocket publiques.

Impact frontend :

- Aucun changement de payload pour les courses, places, drivers, devices ou
  WebSocket.
- Si le backend etait bloque au deploiement par `REDIS_URL is required`, il
  doit redeployer avec le dernier commit.
- Pour les tests CORS localhost, le backend accepte deja `localhost` et
  `127.0.0.1` via `CORS_ORIGIN_REGEX`; ajouter les vrais domaines QA dans
  `CORS_ORIGINS`.
