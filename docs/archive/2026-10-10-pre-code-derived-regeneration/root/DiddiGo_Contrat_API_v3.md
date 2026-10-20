# DiddiGo - Contrat API v3.4

**Destine a :** equipes Frontend / Mobile / Backend DiddiGo
**Base URL staging :** `https://go-staging.diddifree.com/v1`
**Auth staging :** `https://auth-staging.diddifree.com`
**DiddiFiles :** `https://diddifiles.diddifree.com/v1`
**DiddiMap staging :** `http://abidjanmaps-backend-staging.diddifree.com`

Important : le prefixe HTTP reste `/v1`. Le terme `v3.3` designe la version du
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

Regle d'identite partagee : une personne garde une seule identite DiddiFreeID.
DiddiGo active ensuite des capacites metier locales, par exemple le profil
chauffeur. Il ne faut pas creer un compte passager et un compte chauffeur
separes pour la meme personne.

Le token DiddiFreeID ne porte pas le role chauffeur. Le role chauffeur est une
qualification metier DiddiGo via `driver_profiles` + `vehicles`.

Les roles partenaires sont locaux a DiddiGo. DiddiFreeID continue a porter
seulement les roles globaux `user` et `admin`.

La regle complete "identite unique + capacites metier par module" est documentee
dans `docs/architecture/IDENTITY_AND_CAPABILITIES_RULES.md`.

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
| `ride.status` | `requested`, `matched`, `driver_en_route`, `in_progress`, `waiting`, `completed`, `cancelled_by_passenger`, `cancelled_by_driver`, `no_driver_found` |
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
| `score.level` | `new`, `excellent`, `good`, `fair`, `risk` |
| `score.status` | `insufficient_data`, `stable`, `provisional` |

Note produit : on garde les categories vehicule existantes cote backend.
Pour reduire la friction MVP, le frontend passager peut omettre
`vehicle_category`; DiddiGo applique alors `standard`. `comfort_level` devient
le seul choix commercial visible au passager.

---

## 2.1 Capacites utilisateur DiddiGo

### `GET /me/capabilities`

Retourne ce que l'utilisateur authentifie peut faire dans DiddiGo avec son
identite DiddiFreeID actuelle.

Cette route est le point d'entree recommande pour afficher les modes disponibles
dans une app commune ou future app `DiddiFree Pro`.

Regles :

- ne pas deduire le mode chauffeur depuis `role=driver` dans le JWT;
- `passenger` est disponible si l'identite globale est active;
- `driver` depend du profil chauffeur DiddiGo, du KYC, du vehicule actif et du
  KYV;
- `score` dans `/me/capabilities` reste un resume nullable; pour le detail,
  utiliser `/me/scores`.

Requete :

```http
GET /v1/me/capabilities
Authorization: Bearer <access_token>
```

Reponse sans profil chauffeur :

```json
{
  "user_id": "identity-user-id",
  "identity": {
    "role": "user",
    "status": "active"
  },
  "service": "diddigo",
  "consumer": {
    "type": "passenger",
    "enabled": true,
    "status": "active",
    "blocking_reasons": []
  },
  "professional_profiles": [
    {
      "type": "driver",
      "exists": false,
      "status": "not_created",
      "verification_status": "not_created",
      "can_go_online": false,
      "blocking_reasons": ["driver_profile_not_created"],
      "driver_profile_id": null,
      "vehicle": null,
      "score": null
    }
  ],
  "capabilities": [
    {
      "service": "diddigo",
      "type": "passenger",
      "status": "active",
      "enabled": true,
      "blocking_reasons": []
    },
    {
      "service": "diddigo",
      "type": "driver",
      "status": "not_created",
      "enabled": false,
      "blocking_reasons": ["driver_profile_not_created"]
    }
  ]
}
```

Reponse chauffeur actif :

```json
{
  "user_id": "identity-user-id",
  "service": "diddigo",
  "professional_profiles": [
    {
      "type": "driver",
      "exists": true,
      "status": "active",
      "verification_status": "active",
      "can_go_online": true,
      "blocking_reasons": [],
      "driver_profile_id": "driver-profile-id",
      "vehicle": {
        "id": "vehicle-id",
        "status": "active",
        "active": true,
        "category": "standard",
        "comfort_level": "standard",
        "owner_type": "driver",
        "partner_id": null
      },
      "score": null
    }
  ]
}
```

`blocking_reasons` possibles en V1 :

| Reason | Sens frontend |
|---|---|
| `identity_not_active` | Compte global non actif |
| `driver_profile_not_created` | Proposer l'onboarding chauffeur |
| `driver_not_verified` | Afficher KYC en attente ou bloque |
| `no_active_vehicle` | Demander ajout/activation vehicule |
| `vehicle_not_verified` | Afficher KYV vehicule en attente |

---

## 2.2 Scoring DiddiGo

Les scores sont des scores metier locaux a DiddiGo. DiddiFreeID ne les stocke
pas et le JWT ne les porte pas.

En V1 scoring, les scores sont calcules a la demande depuis les donnees DiddiGo
existantes : courses, statuts, annulations, urgences et notes. Ils servent a
l'affichage, au support et aux futures regles metier. Ils ne doivent pas encore
etre utilises seuls pour bloquer un utilisateur.

### `GET /me/scores`

Retourne le score passager et, si le meme utilisateur possede un profil
chauffeur DiddiGo, le score chauffeur.

Requete :

```http
GET /v1/me/scores
Authorization: Bearer <access_token>
```

Reponse :

```json
{
  "user_id": "identity-user-id",
  "service": "diddigo",
  "passenger_score": {
    "subject_type": "passenger",
    "subject_id": "identity-user-id",
    "score_value": 4.72,
    "score_level": "good",
    "score_status": "stable",
    "reason_codes": ["good_ratings", "low_cancellation", "reliable_completion"],
    "last_calculated_at": "2026-09-12T10:00:00Z",
    "sample_size": 18,
    "metrics": {
      "total_rides": 14,
      "completed_rides": 13,
      "cancelled_rides": 1,
      "emergency_reports": 0,
      "rating_count": 4,
      "rating_avg": 4.75
    }
  },
  "driver_score": null
}
```

Si l'utilisateur a un profil chauffeur, `driver_score` suit le meme format avec
`subject_type=driver` et `subject_id=<driver_profile_id>`.

### `GET /rides/{ride_id}/score`

Retourne le score d'une course. Accessible au passager de la course, au
chauffeur assigne ou a un admin.

Requete :

```http
GET /v1/rides/{ride_id}/score
Authorization: Bearer <access_token>
```

Reponse :

```json
{
  "ride_id": "ride-id",
  "subject_type": "trip",
  "score_value": 4.8,
  "score_level": "new",
  "score_status": "stable",
  "reason_codes": ["status_completed", "good_ratings"],
  "last_calculated_at": "2026-09-12T10:00:00Z",
  "sample_size": 2,
  "metrics": {
    "ride_status": "completed",
    "rating_count": 2,
    "rating_avg": 5.0,
    "emergency_status": null,
    "cancellation_reason": null
  }
}
```

Codes utiles :

| HTTP | Code | Cas |
|---|---|---|
| 401 | `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED` | token absent ou invalide |
| 403 | `RIDE_NOT_OWNED_BY_USER` | utilisateur non lie a la course |
| 404 | `RIDE_NOT_FOUND` | course inconnue |

Reason codes possibles en V1 :

```text
no_activity
insufficient_data
good_ratings
low_ratings
high_cancellation
low_cancellation
reliable_completion
low_completion
emergency_reports
status_<ride_status>
no_ratings
emergency_reported
cancel_reason_<reason>
```

## 2.1 Projection chauffeur vers DiddiFreeID

DiddiGo reste la source de verite du statut operationnel chauffeur. La projection
`diddigo/driver` envoyee a DiddiFreeID est asynchrone et persistante : une panne
reseau ou un redemarrage ne bloque pas la requete metier et ne perd pas l'evenement.

Chaque publication contient :

```json
{
  "operational_status": "online",
  "actions": ["go_offline"],
  "projection_version": 42,
  "event_id": "diddigo:driver:<user_id>:42:<uuid>"
}
```

Regles de synchronisation :

- `projection_version` est strictement croissante par chauffeur et persistee en base ;
- un retry reutilise exactement le meme `event_id` et la meme version ;
- un conflit DiddiFreeID `409` est conserve et journalise, jamais rejoue aveuglement ;
- une reconciliation periodique repare les projections absentes ou divergentes ;
- une projection stable est republiee avant expiration de sa fraicheur ;
- l'echec de projection n'annule pas l'action metier DiddiGo deja validee.

Cette integration est strictement service-to-service. Elle utilise un jeton de
service DiddiFreeID avec le scope `capabilities:write` et n'ajoute aucune route
publique DiddiGo.

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

### Acces Backend Backoffice S2S au KYC

Les routes `/v1/drivers/.../kyc` ci-dessus restent utilisables avec un JWT
humain DiddiFreeID `role=admin`. Le Backend Backoffice utilise les routes
internes equivalentes; son secret de client ne doit jamais etre expose au
navigateur.

| Methode | Route interne | Scope requis |
|---|---|---|
| `GET` | `/internal/v1/drivers/kyc` | `diddigo:kyc:read` |
| `GET` | `/internal/v1/drivers/{driver_id}/kyc` | `diddigo:kyc:read` |
| `POST` | `/internal/v1/drivers/{driver_id}/kyc/approve` | `diddigo:kyc:decide` |
| `POST` | `/internal/v1/drivers/{driver_id}/kyc/reject` | `diddigo:kyc:decide` |

Ces routes exigent egalement `sub=service:backoffice`. Un autre service
interne possedant le meme scope reste refuse.

Le manifeste machine-readable des operations disponibles est le fichier
`manifests/manifest.json`. Il suit le contrat `backoffice.v1` et doit etre
importe par Diddi Admin lors du deploiement. Il n'existe volontairement aucun
endpoint HTTP de manifeste dans DiddiGo.

En-tetes communs :

```http
Authorization: Bearer <service_access_token>
X-Client-ID: backoffice-staging-diddigo
X-Request-ID: <uuid-de-correlation>
```

Les deux mutations exigent en plus un en-tete acteur. Le premier est canonique;
le second reste accepte comme alias legacy :

```http
X-Backoffice-Actor: <user_id DiddiFreeID de l'admin humain>
# ou, pendant la migration
X-User-ID: <user_id DiddiFreeID de l'admin humain>
Idempotency-Key: <cle stable de la commande>
```

Le jeton de service doit avoir `aud=diddigo`, `role=service`,
`token_type=service`, `status=active`, et le scope de la route. Au moins un des
deux en-tetes acteur est requis. Lorsqu'ils sont tous les deux
presents, leurs valeurs doivent etre identiques. DiddiGo verifie egalement que
l'identifiant correspond a un shadow user local actif avec
`role=admin`. Une decision rejouee avec la meme cle et le meme contenu retourne
la reponse memorisee; une reutilisation divergente retourne
`409 IDEMPOTENCY_CONFLICT`.

Une decision terminee est journalisee durablement dans DiddiGo avec le client
S2S, le sujet du service, l'admin humain, l'action, le chauffeur cible, le motif,
`X-Request-ID` et `Idempotency-Key`. Cette trace est validee dans la meme
transaction PostgreSQL que la decision KYC. Un rejeu idempotent ne cree pas une
seconde trace d'audit.

### `POST /internal/v1/drivers/provision`

Provisionne l'extension metier chauffeur depuis le Backend Backoffice. Avant
l'appel, le Backoffice doit avoir recherche et valide l'identite cible dans
DiddiFreeID. Le navigateur ne doit jamais appeler directement cette route ni
fournir le secret S2S.

Scope requis : `diddigo:drivers:write`.

En-tetes obligatoires, avec `X-Backoffice-Actor` canonique ou `X-User-ID` legacy :

```http
Authorization: Bearer <service_access_token>
X-Client-ID: backoffice-staging-diddigo
X-Backoffice-Actor: <user_id DiddiFreeID de l'admin humain>
# ou, pendant la migration
X-User-ID: <user_id DiddiFreeID de l'admin humain>
X-Request-ID: <uuid-de-correlation>
Idempotency-Key: <cle stable de la commande>
```

Requete minimale :

```json
{
  "user_id": "identity-user-id",
  "full_name": "Awa Kone",
  "license_number": "CI-123456"
}
```

La requete accepte aussi les memes champs KYC `file_id` et URL legacy que
`POST /v1/drivers/profile`.

Reponse :

```json
{
  "created": true,
  "profile": {
    "id": "driver-profile-id",
    "user_id": "identity-user-id",
    "status": "pending_verification",
    "license_number": "CI-123456",
    "kyc": {}
  }
}
```

Un retry identique retourne le meme resultat sans creer un second profil. Si le
profil existe deja avec exactement les memes informations, la route retourne
`created=false`. Si un profil different existe pour cette identite, elle
retourne `409 DRIVER_PROVISIONING_CONFLICT`.

Le provisionnement termine produit egalement une trace d'audit persistante,
atomique avec le shadow user et le profil chauffeur. La trace conserve notamment
l'acteur humain, le client S2S, la cible, `X-Request-ID` et
`Idempotency-Key`; un rejeu ne la duplique pas.

DiddiGo cree si necessaire un shadow user purement technique pour respecter ses
relations locales. Cela ne cree pas l'identite DiddiFreeID, n'active pas la
capability globale et n'accorde aucune permission de course. Le profil reste
`pending_verification` jusqu'a la validation KYC et aux autres controles metier.

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
| `403` | `SERVICE_ACTOR_FORBIDDEN` | L'acteur humain d'une decision S2S n'est pas un admin actif |
| `403` | `DRIVER_NOT_VERIFIED` | Le chauffeur n'est pas valide pour passer en ligne |
| `403` | `DRIVER_BALANCE_TOO_LOW` | Solde chauffeur insuffisant pour passer en ligne |
| `404` | `DRIVER_PROFILE_NOT_FOUND` | Aucun profil chauffeur pour ce compte ou cet identifiant |
| `409` | `DRIVER_PROFILE_ALREADY_EXISTS` | Un profil chauffeur existe deja pour ce compte |
| `409` | `DRIVER_PROVISIONING_CONFLICT` | Un autre profil chauffeur existe pour l'identite cible |
| `409` | `IDEMPOTENCY_CONFLICT` | La cle S2S designe deja une autre commande |
| `409` | `IDEMPOTENCY_IN_PROGRESS` | La meme commande S2S est encore en cours |
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

### `GET /admin/vehicles/kyv`

Route admin. Liste les vehicules a revoir cote KYV.

Query params :

```text
status=pending_verification | active | suspended | rejected | all
page=1
page_size=20
```

Reponse :

```json
{
  "data": [
    {
      "id": "vehicle-id",
      "driver_id": "driver-profile-id",
      "plate_number": "CE-123-AA",
      "owner_type": "driver",
      "partner_id": null,
      "verification_status": "pending_verification",
      "vehicle_front_photo_file_id": "file-id",
      "vehicle_back_photo_file_id": "file-id",
      "vehicle_left_photo_file_id": "file-id",
      "vehicle_right_photo_file_id": "file-id",
      "vehicle_interior_photo_file_id": "file-id"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1
  }
}
```

Usage backoffice : l'admin liste `pending_verification`, ouvre le dossier
vehicule, verifie les documents et appelle ensuite `approve` ou `reject`.

### `GET /admin/vehicles/{vehicle_id}/kyv`

Route admin. Ouvre le dossier KYV complet d'un vehicule.

Reponse : meme structure qu'un item de `GET /admin/vehicles/kyv`, avec tous les
champs documentaires du vehicule.

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
| `502` | `DIDDIMAP_AUTHENTICATION_FAILED` | authentification interne DiddiGo vers DiddiMap refusee; ce code ne signifie pas que le JWT utilisateur a expire |
| `409` | `DIDDIMAP_BUSINESS_ERROR` | conflit metier DiddiMap non idempotent |
| `422` | `VALIDATION_ERROR` | latitude hors `[-90, 90]` ou longitude hors `[-180, 180]` |

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

Si aucun point GPS n'a ete recu, DiddiGo garde le prix estime et enregistre
`trace_analysis.status=no_samples`. Si DiddiMap retourne
`ignore_for_scoring`, le statut vaut `ignored`. Si l'integration DiddiMap
echoue, la course est tout de meme cloturee avec le prix initial verrouille et
le statut vaut `provider_error`; l'erreur est journalisee via
`ride.actual_pricing.failed`. Ce fallback est donc explicite et observable.

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
partenaire actif si chauffeur affilie
solde chauffeur suffisant si la regle wallet est activee
zone chauffeur compatible quand le modele de zones sera active
```

Matching V2 :

```text
1. DiddiGo classe les chauffeurs eligibles par proximite.
2. DiddiGo ouvre une vague de maximum 5 chauffeurs.
3. Chaque offre expire apres 15 secondes.
4. Le premier chauffeur qui accepte gagne la course.
5. Les autres acceptations recoivent RIDE_ALREADY_MATCHED.
6. Si toute la vague refuse ou expire, DiddiGo ouvre automatiquement la vague suivante.
7. Si aucun chauffeur eligible ne reste, la course passe a no_driver_found.
```

Note zone : le critere "est dans sa zone" est une regle produit retenue, mais
il n'est applique que lorsque les zones chauffeur seront modelees dans DiddiGo.
En v3.3, le matching journalise deja les raisons d'exclusion disponibles et
reste extensible pour ce filtre.

`comfort_level` est maintenant un filtre de matching hierarchique :

```text
course standard -> vehicule standard, comfort ou premium
course comfort  -> vehicule comfort ou premium
course premium  -> vehicule premium uniquement
```

Un vehicule d'un niveau superieur peut servir une demande inferieure, mais pas
l'inverse. Cela evite de faire payer `premium` au passager pour envoyer une
voiture `standard`.

### `GET /rides`

La liste est toujours autorisee avec le role issu du token verifie. Le parametre
optionnel `role=passenger|driver` choisit uniquement les courses du compte
connecte : passager, ou chauffeur associe a son profil DiddiGo. Sans parametre,
un `user` voit ses courses passager et un `admin` voit la liste globale.
`role=admin` exige un vrai token admin ; un utilisateur ordinaire recoit
`403 FORBIDDEN_ROLE`. Une valeur de role inconnue retourne `422 INVALID_ROLE`.

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
  "trace_analysis": {
    "status": "pending",
    "error_code": null,
    "recommendation": null,
    "quality_label": null,
    "quality_score": null,
    "points_count": null,
    "usable_points_count": null
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

Valeurs de `trace_analysis.status` :

| Statut | Sens |
|---|---|
| `pending` | course non terminee ou analyse pas encore lancee |
| `applied` | metriques reelles calculees et conservees pour analytics |
| `ignored` | DiddiMap recommande `ignore_for_scoring` |
| `no_samples` | aucun point GPS chauffeur disponible |
| `provider_error` | erreur DiddiMap; course cloturee au prix verrouille |
| `legacy_not_analyzed` | ancienne course terminee avant le suivi du statut |

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

### `GET /me/emergency-contact`

Retourne le contact d'urgence DiddiGo de l'utilisateur connecte.

Reponse :

```json
{
  "id": "contact-id",
  "user_id": "user-id",
  "contact_name": "Awa Kone",
  "phone": "+2250700000000",
  "email": "awa@example.com",
  "relationship": "famille"
}
```

Erreurs :

- `404 EMERGENCY_CONTACT_NOT_FOUND` si aucun contact n'est configure.

### `PUT /me/emergency-contact`

Cree ou met a jour le contact d'urgence local DiddiGo.

Requete :

```json
{
  "contact_name": "Awa Kone",
  "phone": "+2250700000000",
  "email": "awa@example.com",
  "relationship": "famille"
}
```

Regle :

- `phone` ou `email` est obligatoire.
- `phone` sert au canal WhatsApp si `EMERGENCY_WHATSAPP_WEBHOOK_URL` est configure.
- `email` sert au canal email si SMTP est configure.

Erreurs :

- `422 EMERGENCY_CONTACT_REQUIRED` si aucun telephone/e-mail n'est fourni.

### `DELETE /me/emergency-contact`

Supprime le contact d'urgence DiddiGo de l'utilisateur connecte.

Reponse :

```json
{
  "status": "deleted"
}
```

### `POST /rides/{ride_id}/emergency`

Accessible au passager, au chauffeur assigne, ou admin.

Regle d'audit :

- une course ne peut avoir qu'une urgence ouverte;
- un deuxieme appel ne doit pas ecraser la premiere heure/note;
- DiddiGo retourne `409 EMERGENCY_ALREADY_OPEN` si l'urgence est deja ouverte.

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
  "requested_at": "2026-08-05T10:25:00Z",
  "notifications": [
    {
      "target": "support",
      "channel": "email",
      "recipient": "direction.generale@diddifree.com",
      "status": "sent",
      "reason": null
    },
    {
      "target": "emergency_contact",
      "channel": "whatsapp",
      "recipient": "+2250700000000",
      "status": "skipped",
      "reason": "whatsapp_webhook_not_configured"
    }
  ]
}
```

DiddiGo ecrit aussi un log serveur `ride_emergency` avec `ride_id` et
`actor_user_id`, puis des logs structures `ride.emergency.notification.*`.

Configuration :

- `EMERGENCY_SUPPORT_EMAIL`, defaut `direction.generale@diddifree.com`
- `EMERGENCY_SUPPORT_WHATSAPP`, optionnel
- `EMERGENCY_WHATSAPP_WEBHOOK_URL`, optionnel
- `EMERGENCY_WHATSAPP_API_KEY`, optionnel
- `EMERGENCY_SMTP_HOST`, optionnel
- `EMERGENCY_SMTP_PORT`, defaut `587`
- `EMERGENCY_SMTP_USERNAME`, optionnel
- `EMERGENCY_SMTP_PASSWORD`, optionnel
- `EMERGENCY_EMAIL_FROM`, defaut `alerts@diddifree.com`

Si un provider n'est pas configure, DiddiGo ne fait pas de fallback silencieux :
la notification retourne `status=skipped` avec une raison explicite, et l'urgence
reste bien ouverte.

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
  "customer_phone": "+2250700000000"
}
```

Le client ne peut pas fournir de `callback_url`. DiddiGo choisit la destination
passager configuree par `DIDDIGO_CONSUMER_RETURN_URL`; toute propriete inconnue
dans cette requete est rejetee avec `422`.

DiddiGo ajoute automatiquement un parametre `context` opaque au retour. Ce
contexte expire apres 15 minutes par defaut, est lie a l'utilisateur, la course
et au `payment_intent_id`, et ne peut etre consomme qu'une fois.

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
404 lorsque `DIDDIGO_CONSUMER_RETURN_URL` pointe vers DiddiGo.

Important : cette route ne confirme jamais le paiement. Elle affiche seulement
une page demandant a l'utilisateur de revenir dans l'application. L'application
doit relire `GET /v1/payments/{ride_id}`.

Un contexte absent, falsifie, expire, deja utilise ou destine a l'espace
chauffeur affiche une page de lien invalide. Il ne modifie jamais le paiement.

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
  "can_go_online": false
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

`min_balance` vient de la configuration backend `DRIVER_MIN_BALANCE`.

Regle V1 :

- si `balance < min_balance`, `POST /drivers/online` retourne
  `403 DRIVER_BALANCE_TOO_LOW`;
- la meme regle est reverifiee par le matching pour ne pas proposer de nouvelle
  course a un chauffeur deja en ligne mais passe sous le seuil;
- `DRIVER_MIN_BALANCE=0` bloque un chauffeur negatif;
- une valeur negative autorise un decouvert borne;
- `DRIVER_MAX_ESTIMATED_COMMISSION=0` desactive le plafond global de commission
  estimee;
- si `DRIVER_MAX_ESTIMATED_COMMISSION > 0` et que la commission estimee d'une
  course depasse ce seuil, DiddiGo ne propose pas la course et la passe a
  `no_driver_found`.

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
  "customer_phone": "+2250700000000"
}
```

Le client ne peut pas fournir de `callback_url`. DiddiGo choisit la destination
chauffeur configuree par `DIDDIGO_PRO_RETURN_URL`; toute propriete inconnue dans
cette requete est rejetee avec `422`.

DiddiGo ajoute un `context` opaque, lie au chauffeur, a la recharge et au
`payment_intent_id`. Il expire et ne peut etre consomme qu'une fois. Un contexte
passager ne peut pas etre utilise sur `/wallet/return`.

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

## 13. Resume quotidien interne pour Pilotage

### `GET /internal/pilotage/daily-summary?date=YYYY-MM-DD`

Route canonique conforme au contrat interne `pilotage.v1`. Elle utilise le meme
calcul et les memes controles S2S que la route historique ci-dessous. La reponse
contient `contract_version`, `is_final`, un tableau `metrics` avec les unites,
`calculated_at`, `sources` et les liens profonds Backoffice. Les donnees sont
recalculees a chaque appel. La fenetre de fraicheur attendue cote collecteur est
de 60 secondes.

Metriques :

| Nom | Unite | Definition |
| --- | --- | --- |
| `rides_requested` | `count` | Courses dont `requested_at` appartient a la journee demandee en heure d'Abidjan. |
| `rides_completed` | `count` | Courses terminees dont `completed_at` appartient a cette journee. |
| `completed_fare_total_xof` | `XOF` | Somme du montant facture verrouille des memes courses terminees, frais d'attente inclus, avant remboursement ulterieur. |

`is_final=false` pour la journee courante et `true` pour une journee passee. Une
journee passee reste recalculee lors de chaque appel afin d'inclure une correction
tardive eventuelle.

### `GET /internal/pilotage/finance-summary?date=YYYY-MM-DD`

Retourne uniquement l'agregat `completed_fare_total_xof`, sans donnees
personnelles, avec le meme jeton et le meme scope Pilotage.

### `GET /internal/pilotage/health-summary`

Retourne l'etat agrege `available` ou `degraded`, l'etat PostgreSQL et Redis,
`calculated_at` et une fenetre de fraicheur de 60 secondes. Une indisponibilite
n'est jamais transformee en valeur metier egale a zero.

### `GET /internal/v1/ride-summary?date=YYYY-MM-DD`

Route historique conservee sans changement de forme pendant la migration de
Pilotage.

Cette route serveur-a-serveur requiert un JWT DiddiFreeID signe (JWKS),
`Authorization: Bearer <service_token>` et `X-Client-ID` identique au claim
`client_id`. Les claims doivent inclure `iss=diddifree-id`, `aud=diddigo`,
`sub=service:pilotage`, `role=service`, `token_type=service`, `status=active`
et le scope `diddigo:ride-summary:read`. L'ancien scope `ride-summary:read`
reste temporairement accepte pendant la migration. Un JWT utilisateur ne donne
aucun acces.

La date est interpretee dans `Africa/Abidjan` et les bornes sont inclusives
au debut, exclusives a la fin. Par defaut, seules la date courante et les
31 jours precedents sont admis (`RIDE_SUMMARY_MAX_AGE_DAYS`).

```json
{
  "module": "diddigo",
  "date": "2026-09-19",
  "timezone": "Africa/Abidjan",
  "rides_requested": 12,
  "rides_completed": 8,
  "completed_fare_total_xof": 24000,
  "calculated_at": "2026-09-19T12:00:00Z"
}
```

`rides_requested` compte les courses par `requested_at` quel que soit leur
statut actuel. `rides_completed` compte les courses de statut `completed`
par `completed_at`. Le total additionne uniquement leurs `final_fare` non
nuls en XOF. Les courses terminees sans prix final restent dans le compte,
mais pas dans la somme; une alerte est ecrite dans les logs. Les trois
agregats proviennent d'une seule requete SQL.

| HTTP | Code | Sens |
|---|---|---|
| `401` | `TOKEN_MISSING` | Jeton absent |
| `401` | `SERVICE_CLIENT_ID_MISSING` | En-tete `X-Client-ID` absent |
| `401` | `SERVICE_CLIENT_ID_INVALID` | Client ID different du jeton |
| `401` | `SERVICE_TOKEN_INVALID` | Signature, issuer, audience ou claims invalides |
| `401` | `SERVICE_TOKEN_EXPIRED` | Jeton expire |
| `403` | `SERVICE_SCOPE_INVALID` | Scope insuffisant |
| `403` | `SERVICE_SUBJECT_INVALID` | Service appelant non autorise |
| `403` | `SERVICE_TOKEN_INACTIVE` | Client service inactif |
| `422` | `INVALID_DATE` | Date mal formee ou invalide |
| `422` | `SUMMARY_DATE_IN_FUTURE` | Date future |
| `422` | `SUMMARY_DATE_OUT_OF_RANGE` | Date hors fenetre configuree |
| `500` | `INVALID_RIDE_FARE` | Montant XOF non entier, sans troncature silencieuse |
| `503` | `RIDE_SUMMARY_UNAVAILABLE` | Base de donnees momentanement indisponible |
| `503` | `SERVICE_JWKS_UNAVAILABLE` | Cles JWKS temporairement inaccessibles |

## 14. Attente pendant une course

L'attente manuelle est disponible uniquement pendant une course `in_progress`.
Le chauffeur doit envoyer sa position WebSocket avec `speed_kmh`; DiddiGo
refuse l'activation si cette telemetrie est absente/perimee ou si la vitesse
depasse le seuil configure. Les horodatages et le montant sont calcules par le
serveur. Chaque minute commencee est facturee, avec un minimum d'une minute par
periode d'attente.

### Demarrer l'attente

`POST /v1/rides/{ride_id}/waiting/start`

Reponse `200` :

```json
{
  "ride_id": "uuid",
  "status": "waiting",
  "waiting": {
    "active": true,
    "started_at": "2026-09-21T10:00:00Z",
    "duration_seconds": 0,
    "fee": 0,
    "rate_per_minute": 100
  }
}
```

### Arreter l'attente

`POST /v1/rides/{ride_id}/waiting/stop`

La reponse reprend la meme structure avec `status=in_progress`, `active=false`,
la duree cumulee et le supplement cumule. Une reprise du mouvement au-dessus
du seuil arrete aussi automatiquement l'attente.

Le detail `GET /v1/rides/{ride_id}` expose `waiting` et
`pricing.waiting_fee`. A la fin, `final_fare` vaut le prix estime verrouille
plus le supplement d'attente. Commission plateforme et net chauffeur sont
recalcules sur ce montant final.

Evenements WebSocket envoyes aux abonnes de la course :

```text
ride.status_changed  status=waiting|in_progress
ride.waiting_changed ride_id, status, waiting, at
```

Le message chauffeur `driver.location_push` accepte maintenant `speed_kmh` :

```json
{
  "event": "driver.location_push",
  "ride_id": "uuid",
  "location": {"lat": 5.35, "lng": -4.00},
  "heading": 90,
  "speed_kmh": 0.0
}
```

| HTTP | Code | Sens |
|---|---|---|
| `403` | `RIDE_NOT_OWNED_BY_USER` | Chauffeur non assigne |
| `409` | `WAITING_INVALID_RIDE_STATUS` | Course pas encore demarree |
| `409` | `WAITING_TELEMETRY_REQUIRED` | Vitesse recente absente |
| `409` | `VEHICLE_NOT_STOPPED` | Vitesse superieure au seuil |
| `409` | `WAITING_NOT_ACTIVE` | Arret demande sans attente active |
| `409` | `WAITING_STOP_ENDPOINT_REQUIRED` | Utiliser `/waiting/stop`, pas le PATCH generique |

Configuration backend : `WAITING_PRICE_PER_MINUTE_XOF` (defaut `100`),
`WAITING_STATIONARY_SPEED_THRESHOLD_KMH` (defaut `3`) et
`WAITING_TELEMETRY_TTL_SECONDS` (defaut `30`).

## 15. Hors Scope v3.4

```text
DiddiSend
DiddiScore
dispatch urgence complet
wallet partenaire complet
payout automatique partenaire
contrat physique /v2 ou /v3 dans l'URL
```

## 16. Recherche de logs administrateur (v3.5)

Ces routes sont reservees aux utilisateurs DiddiFreeID ayant le role global
`admin`. Le role n'est jamais accepte depuis un parametre client.

```http
GET /v1/admin/logs/rides/{ride_id}
GET /v1/admin/logs/drivers/{driver_id}
```

Parametres optionnels : `from`, `to` (ISO 8601), `level`, `limit` (1 a 500)
et `cursor`. Sans periode, les dernieres 24 heures sont consultees. Une requete
ne peut pas couvrir plus de 30 jours. Les resultats sont classes du plus recent
au plus ancien.

```json
{
  "items": [
    {
      "timestamp": "2026-09-21T12:00:00Z",
      "level": "INFO",
      "event": "ride.created",
      "message": null,
      "request_id": "req-123",
      "metadata": {"ride_id": "uuid", "status": "requested"}
    }
  ],
  "next_cursor": "1789991999999999999",
  "limit": 100,
  "from": "2026-09-20T12:00:00+00:00",
  "to": "2026-09-21T12:00:00+00:00"
}
```

| HTTP | Code | Sens |
|---|---|---|
| `403` | `FORBIDDEN_ROLE` | L'utilisateur n'est pas administrateur |
| `422` | `INVALID_LOG_TIME_RANGE` | Debut posterieur ou egal a la fin |
| `422` | `LOG_TIME_RANGE_TOO_LARGE` | Periode superieure a 30 jours |
| `422` | `INVALID_LOG_CURSOR` | Curseur de pagination invalide |
| `503` | `LOG_SEARCH_UNAVAILABLE` | Loki absent, en erreur ou mal configure |

La source de verite est Loki. DiddiGo ne masque jamais son indisponibilite par
une reponse vide ou par une recherche de secours en base.
