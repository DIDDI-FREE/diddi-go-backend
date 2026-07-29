# DiddiGo — Brief Frontend

**Pour :** équipes mobile (app passager, app chauffeur)
**Backend :** `http://localhost:8000/v1` en local · Swagger : `/docs`
**Contrat de référence :** [`DiddiGo_Contrat_API.md`](DiddiGo_Contrat_API.md)

Ce document dit ce qui est **utilisable dès maintenant**, ce qui **n'existe pas
encore**, et les pièges à connaître avant d'écrire du code client.

---

## 1. En un coup d'œil

| Domaine | État | Remarque |
|---|---|---|
| Inscription / OTP / JWT | ✅ Utilisable | Vrais JWT, refresh inclus |
| Estimation tarifaire | ✅ Utilisable | Fonctionne même sans DiddiMap |
| Création de course | ✅ Utilisable | Déclenche le matching |
| Matching chauffeur | ✅ Utilisable | Offre séquentielle, 15 s par chauffeur |
| Accept / decline chauffeur | ✅ Utilisable | |
| Cycle de vie course | ✅ Utilisable | |
| Onboarding chauffeur | ✅ Utilisable | KYC auto-approuvé (voir §6) |
| Paiement espèces | ✅ Utilisable | |
| Notation | ✅ Utilisable | |
| WebSocket temps réel | ⚠️ Partiel | Le passager doit s'abonner (voir §4) |
| Envoi SMS de l'OTP | ❌ Absent | Code visible dans les logs serveur |
| Admin / back-office | ❌ Absent | Aucun écran admin possible |
| Mobile money / wallet | ❌ Absent | Espèces uniquement |

---

## 2. Démarrer en local

```bash
cp .env.example .env
uv sync
docker compose up -d db redis
uv run alembic upgrade head
uv run uvicorn app_base.main:app --reload
```

**Récupérer un code OTP en dev :** aucun SMS n'est envoyé. Le code à 6 chiffres
est écrit dans les logs du serveur :

```
OTP stub — in dev, code for phone=+2250700000000 is 482913. SMS integration pending.
```

Prévoyez ce détour dans vos scripts de test ; en préprod, l'intégration SMS
changera cela sans modifier l'API.

---

## 3. Endpoints disponibles

Tout est préfixé par `/v1`. Sauf mention contraire, un header
`Authorization: Bearer <access_token>` est obligatoire.

### Auth — *pas de token requis sauf `/me`*

| Méthode | Route | Retour |
|---|---|---|
| `POST` | `/auth/register` | `{user_id, phone, status}` |
| `POST` | `/auth/otp/request` | `{expires_in_seconds, retry_after_seconds}` |
| `POST` | `/auth/otp/verify` | `{access_token, refresh_token, user}` |
| `POST` | `/auth/refresh` | `{access_token, refresh_token}` |
| `GET` | `/auth/me` | profil du porteur du token |

- `access_token` : 15 min · `refresh_token` : 30 jours.
- Le téléphone doit être au format international (`+2250700000000`). Les
  espaces sont tolérés et normalisés ; tout le reste renvoie
  `422 INVALID_PHONE_FORMAT`.
- Un OTP est **à usage unique** et vit 5 minutes. Une seconde demande dans
  les 60 s renvoie `429 OTP_RATE_LIMITED` — désactivez le bouton « renvoyer »
  pendant `retry_after_seconds`.

### Passager

| Méthode | Route | Notes |
|---|---|---|
| `POST` | `/rides/pricing/estimate` | à appeler avant la réservation |
| `POST` | `/rides` | crée la course **et** lance le matching |
| `GET` | `/rides/{id}` | détail, avec le chauffeur une fois assigné |
| `GET` | `/rides` | historique paginé |
| `POST` | `/rides/{id}/cancel` | |
| `POST` | `/rides/{id}/rating` | une seule note par rôle et par course |

### Chauffeur

| Méthode | Route | Notes |
|---|---|---|
| `POST` | `/drivers/profile` | numéro de permis |
| `POST` | `/drivers/vehicle` | plaque, marque, modèle, couleur, catégorie |
| `GET` | `/drivers/me` | profil + véhicule actif |
| `POST` | `/drivers/online` | `{lat, lng}` — entre dans le vivier |
| `POST` | `/drivers/offline` | quitte le vivier |
| `POST` | `/rides/{id}/accept` | accepte l'offre reçue |
| `POST` | `/rides/{id}/decline` | refuse — la course part au suivant |
| `PATCH` | `/rides/{id}/status` | `driver_en_route` → `in_progress` → `completed` |
| `POST` | `/payments/{ride_id}/confirm-cash` | encaissement |

### Paiement

| Méthode | Route |
|---|---|
| `GET` | `/payments/{ride_id}` |
| `POST` | `/payments/{ride_id}/confirm-cash` |

---

## 4. Temps réel — WebSocket

```
wss://<host>/v1/ws?token=<access_token>
```

Un seul socket par session, multiplexé par `event`. Le token passe en query
param (un navigateur ne peut pas poser de header sur un handshake WebSocket).

### ⚠️ Le passager doit s'abonner explicitement

C'est l'écart le plus important par rapport au contrat d'origine. Après avoir
créé une course, envoyez :

```json
{ "event": "ride.subscribe", "ride_id": "c7f2..." }
```

Sans cela **vous ne recevrez aucun événement pour cette course**. Le serveur
répond `{"event":"ack","received_event":"ride.subscribe","ride_id":"..."}`.

### Événements reçus

| Événement | Destinataire | Charge utile |
|---|---|---|
| `ride.status_changed` | passager abonné | `{ride_id, status, at}` |
| `ride.driver_location` | passager abonné | `{ride_id, location:{lat,lng}, heading, at}` |
| `ride.no_driver_found` | passager abonné | `{ride_id}` |
| `ride.new_request` | chauffeur ciblé | `{ride_id, pickup, dropoff_address, estimated_fare, expires_in_seconds}` |

### Événements envoyés

```json
{ "event": "driver.location_push", "ride_id": "c7f2...", "location": {"lat": 5.36, "lng": -4.01}, "heading": 134 }
```

Toutes les 3–5 s pendant une course active. `ride_id` est optionnel : sans lui
la position est enregistrée pour le matching mais n'est diffusée à personne.

### Règles de robustesse

- Un événement inconnu reçoit `{"event":"ignored"}` — **votre client doit faire
  pareil** : de nouveaux types seront ajoutés sans que ce soit une rupture.
- Le serveur **ne rejoue pas** les événements manqués. Après reconnexion
  (backoff 1s→2s→4s→8s, plafond 30s), refaites `GET /rides/{id}` puis
  `ride.subscribe`.
- Codes de fermeture : `4401` = token manquant, invalide ou expiré → renvoyez
  l'utilisateur vers l'écran de connexion.

---

## 5. Les deux parcours, dans l'ordre

### Passager

```
register → otp/request → otp/verify (⇒ token)
   → pricing/estimate            (afficher le prix)
   → POST /rides                 (⇒ ride_id, status: "requested")
   → WS: ride.subscribe {ride_id}
   → attendre ride.status_changed → "matched"
   → GET /rides/{id}             (nom, note, téléphone, véhicule du chauffeur)
   → suivre ride.driver_location sur la carte
   → à "completed" : POST /rides/{id}/rating
```

**`POST /rides` renvoie toujours `status: "requested"`**, même si aucun
chauffeur n'a pu être trouvé. Le verdict arrive par WebSocket
(`ride.no_driver_found`) ou via `GET /rides/{id}`. Ne considérez jamais la
réponse de création comme un succès de matching.

### Chauffeur

```
register (role=driver) → otp/verify
   → POST /drivers/profile   (permis)
   → POST /drivers/vehicle   (véhicule)
   → POST /drivers/online    (position)
   → WS connecté → recevoir ride.new_request
   → POST /rides/{id}/accept  (dans les 15 s)  |  /decline
   → PATCH status: driver_en_route → in_progress → completed
   → POST /payments/{ride_id}/confirm-cash
```

Les trois étapes d'onboarding sont **obligatoires et ordonnées**. Un chauffeur
sans véhicule actif ne peut pas passer en ligne (`409 NO_ACTIVE_VEHICLE`) et ne
recevra jamais d'offre.

---

## 6. Comment fonctionne le matching (ce que l'UI doit refléter)

La course est proposée **à un seul chauffeur à la fois** : le plus proche
disponible dans un rayon de 5 km. Il a **15 secondes** pour répondre. S'il
refuse ou ne répond pas, la course passe au suivant, et ainsi de suite jusqu'à
acceptation ou épuisement des candidats — la course devient alors
`no_driver_found`.

Conséquences côté interface :

- **App chauffeur :** affichez un compte à rebours de `expires_in_seconds`. Une
  fois écoulé, l'offre n'est plus valable — `accept` renverra
  `409 OFFER_EXPIRED`. Ne laissez pas le bouton actif.
- **App passager :** l'attente peut durer plusieurs cycles de 15 s. Prévoyez un
  écran de recherche patient, pas un spinner de 2 secondes.
- Deux chauffeurs ne peuvent pas accepter la même course : le second reçoit
  `409 RIDE_ALREADY_MATCHED`. Traitez ce cas sans plantage.

**Limite actuelle :** l'expiration d'une offre libère bien le créneau, mais la
course n'est réellement proposée au chauffeur suivant qu'au prochain événement
la concernant (un refus, une relance). Un chauffeur qui ignore purement et
simplement une demande peut donc ralentir le passage au suivant. Un worker de
relance est prévu ; en attendant, ne promettez pas de délai garanti dans l'UI.

---

## 7. Gestion des erreurs

Format uniforme sur **toutes** les routes :

```json
{ "error": { "code": "RIDE_NOT_FOUND", "message": "Aucune course trouvée avec cet identifiant.", "details": null } }
```

- `code` : stable, destiné à votre `switch`.
- `message` : déjà en français, affichable tel quel.
- `details` : complément structuré quand il existe.

### Codes à gérer explicitement

**Auth**

| Code | HTTP | Réaction attendue |
|---|---|---|
| `TOKEN_EXPIRED` | 401 | appeler `/auth/refresh`, rejouer la requête **une fois** |
| `TOKEN_INVALID` / `TOKEN_MISSING` | 401 | écran de connexion |
| `REFRESH_TOKEN_INVALID` | 401 | écran de connexion |
| `USER_SUSPENDED` | 403 | message dédié, pas un retry |
| `INVALID_PHONE_FORMAT` | 422 | erreur sur le champ téléphone |
| `PHONE_ALREADY_REGISTERED` | 409 | proposer la connexion |
| `OTP_INVALID` / `OTP_EXPIRED` | 400 / 410 | redemander un code |
| `OTP_RATE_LIMITED` | 429 | attendre `details.retry_after_seconds` |

**Course**

| Code | HTTP | Réaction attendue |
|---|---|---|
| `ACTIVE_RIDE_ALREADY_EXISTS` | 409 | rediriger vers la course en cours |
| `INVALID_STATUS_TRANSITION` | 409 | resynchroniser via `GET /rides/{id}` |
| `RIDE_ALREADY_COMPLETED` / `_CANCELLED` | 409 | rafraîchir l'écran |
| `RIDE_NOT_CANCELLABLE` | 409 | course déjà terminale (`no_driver_found`) |
| `RIDE_NOT_OWNED_BY_USER` | 403 | ne pas afficher |
| `RATING_ALREADY_SUBMITTED` | 409 | masquer le formulaire de note |

**Matching (app chauffeur)**

| Code | HTTP | Réaction attendue |
|---|---|---|
| `OFFER_EXPIRED` | 409 | retirer la demande de l'écran |
| `OFFER_NOT_YOURS` | 403 | idem — elle est partie ailleurs |
| `RIDE_ALREADY_MATCHED` | 409 | idem |
| `DRIVER_PROFILE_NOT_FOUND` | 404 | renvoyer vers l'onboarding |
| `NO_ACTIVE_VEHICLE` | 409 | renvoyer vers l'ajout de véhicule |
| `DRIVER_NOT_VERIFIED` | 403 | écran « compte en cours de validation » |

---

## 8. Ce qui n'existe pas encore

À ne pas maquetter comme fonctionnel :

1. **SMS d'OTP.** Le code sort dans les logs serveur. L'API ne changera pas
   quand le fournisseur SMS sera branché.
2. **Back-office / admin.** Aucune route d'administration : ni validation KYC,
   ni suspension de compte, ni gestion tarifaire. **Tout chauffeur qui soumet un
   permis est approuvé automatiquement** — c'est temporaire et volontaire, pour
   que le parcours soit testable.
3. **Mobile money / wallet.** Espèces uniquement. Le champ `method` existe déjà
   dans les réponses paiement et vaut toujours `"cash"` : lisez-le plutôt que de
   coder « espèces » en dur, l'ajout ne cassera alors rien.
4. **Tarification dynamique.** `surge_multiplier` est toujours `1.0`. Prévoyez
   quand même l'affichage : le produit exige qu'un surge soit montré
   explicitement avant réservation.
5. **Photos / avatars.** Aucun upload de fichier nulle part.
6. **Notifications push.** Uniquement le WebSocket : une app chauffeur en
   arrière-plan ne recevra pas les offres.
7. **Adresses depuis DiddiMap.** Le géocodage existe côté backend mais aucune
   route ne l'expose. L'autocomplétion d'adresse est à votre charge, ou à
   demander.

---

## 9. Détails qui font gagner du temps

- **Montants :** entiers, en XOF (pas de centimes). N'affichez pas de décimales.
- **Dates :** ISO 8601 UTC, suffixe `Z`. Convertissez à l'affichage.
- **Distances :** kilomètres (2 décimales). **Durées :** secondes.
- **Pagination :** `?page=1&page_size=20` (max 100), réponse
  `{data, pagination:{page,page_size,total_items,total_pages}}`.
- **Liste vs détail :** `GET /rides` renvoie une vue allégée **sans** le
  chauffeur ni le véhicule. Ces informations n'existent que sur
  `GET /rides/{id}`.
- **`driver` vaut `null`** tant que la course est `requested` ou
  `no_driver_found`. Testez-le avant de déréférencer.
- **Statuts :** codez en dur les 8 valeurs, mais **ignorez proprement** un
  statut inconnu reçu par WebSocket — `payment_pending` est explicitement
  réservé pour plus tard.
- **Estimation ≠ prix final.** `estimated_fare` à la réservation,
  `final_fare` (`null` avant la fin) une fois la course terminée.

---

## 10. Questions ouvertes pour le produit

À trancher avant que les écrans correspondants soient figés :

1. **Attente passager :** au bout de combien de temps sans chauffeur abandonne-t-on ?
2. **Annulation :** y a-t-il des frais après un certain délai ? Rien n'est
   implémenté côté backend aujourd'hui.
3. **Autocomplétion d'adresse :** exposons-nous le géocodage DiddiMap, ou le
   front utilise-t-il un autre fournisseur ?
4. **Courses programmées :** `scheduled_at` est accepté et stocké, mais aucune
   planification n'existe — la course part au matching immédiatement. À
   masquer dans l'UI tant que ce n'est pas traité.
5. **Reconnexion chauffeur :** une offre en cours doit-elle survivre à une
   coupure réseau de 10 s côté chauffeur ?
