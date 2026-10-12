# DiddiGo - clarifications frontend V2

**Version :** 2026.10.12-v2

**Publié le :** 12 octobre 2026

**Complète :** [`DIDDIGO_FRONTEND_BRIEF_2026-10-12.md`](DIDDIGO_FRONTEND_BRIEF_2026-10-12.md)

**Portée :** comportement réellement disponible et limites connues avant les prochains correctifs backend.

Ce document ne remplace ni l'OpenAPI DiddiGo ni le contrat DiddiFiles. Il explique comment les assembler côté frontend et indique les écarts à ne pas contourner localement.

## 1. Attente avant le départ

Il existe deux attentes différentes.

### Attente pré-course

```text
POST /v1/rides/{ride_id}/arrive
-> statut arrived
-> démarrage automatique de l'attente pré-course
-> 180 secondes gratuites actuellement
-> facturation proportionnelle à la seconde ensuite
```

Le frontend ne doit pas appeler `/waiting/start` après `/arrive`.

- Afficher le chronomètre depuis `waiting_started_at` fourni par `/arrive`.
- Utiliser `free_seconds`, `no_show_after_seconds` et `price_per_minute_xof` retournés par le serveur.
- Ne jamais calculer ni enregistrer le montant côté client.
- Au démarrage, appeler `POST /v1/rides/{ride_id}/start` avec le code à six chiffres, puis relire la course.
- Lorsque `no_show_after_seconds` est atteint, le chauffeur peut appeler `POST /v1/rides/{ride_id}/no-show`.
- Avant le délai, `NO_SHOW_TOO_EARLY` contient `remaining_seconds`.

### Attente pendant la course

`POST /v1/rides/{ride_id}/waiting/start` et `/waiting/stop` concernent uniquement une course déjà `in_progress`. Un appel pendant `arrived` répond normalement `409 WAITING_INVALID_RIDE_STATUS`.

## 2. Envoi des traces GPS

Route REST :

```http
POST /v1/rides/{ride_id}/location-samples
Authorization: Bearer <driver_access_token>
Content-Type: application/json
```

Le corps contient `samples`, entre 1 et 120 éléments selon l'OpenAPI. Seul le chauffeur affecté peut écrire les traces de la course.

### Rejeu après timeout

Le frontend doit générer un UUID `batch_id` avant chaque envoi et le conserver avec le lot. Si la requête expire sans réponse, il rejoue exactement le même corps avec le même `batch_id`.

La réponse contient :

```json
{
  "ride_id": "<uuid>",
  "batch_id": "<uuid stable du client>",
  "accepted_samples": 12,
  "replayed": false
}
```

`replayed=true` signifie que DiddiGo connaissait déjà ce lot et n'a pas créé de doublon. L'absence de `batch_id` reste acceptée pour compatibilité, mais ne permet pas au client de rejouer une requête dont la réponse a été perdue.

Réutiliser un `batch_id` avec un contenu différent répond `409 GPS_BATCH_IDEMPOTENCY_CONFLICT`. Dans ce cas, ne pas remplacer silencieusement le lot local : générer un nouvel identifiant uniquement s'il s'agit réellement d'un nouveau lot.

Le WebSocket `driver.location_push` sert au temps réel. `location-samples` sert à la trace durable de la course ; ces deux mécanismes ne se remplacent pas.

## 3. Capacités chauffeur et passage en ligne

`GET /v1/me/capabilities` et `POST /v1/drivers/online` utilisent désormais la même règle d'éligibilité opérationnelle. Les blocages possibles incluent notamment :

- `DRIVER_NOT_VERIFIED` ;
- véhicule absent ou non validé ;
- partenaire suspendu ;
- `DRIVER_BALANCE_TOO_LOW`.

- utiliser `can_go_online` et `blocking_reasons` pour préparer l'écran ;
- lire `online_requirements.wallet` pour afficher `balance`, `min_balance` et `currency` ;
- continuer à traiter proprement un refus de `/drivers/online`, car l'état peut changer entre la lecture et l'action ;
- sur `DRIVER_BALANCE_TOO_LOW`, proposer la recharge.

Le frontend ne doit pas dupliquer le calcul du solde minimum comme règle de sécurité.

## 4. DiddiComms lié à une course

Le frontend communique avec DiddiComms, jamais avec le resolver interne DiddiGo.

Le comportement DiddiGo prévoit :

- messagerie et appel pendant une course active ;
- appel désactivé après fin ou annulation ;
- messagerie fermée immédiatement après annulation, avec `closes_at=cancelled_at` ;
- messagerie encore autorisée pendant une grâce de 48 heures après une course terminée ;
- `closes_at` indique la fermeture effective.

Le frontend doit toujours respecter la réponse DiddiComms et ne jamais déduire lui-même les permissions depuis le seul statut de course. La lecture de l'historique peut rester disponible quand l'envoi est fermé.

## 5. SOS et résultats par canal

Une réponse réussie de `POST /v1/rides/{ride_id}/emergency` signifie d'abord que l'alerte est enregistrée. Chaque canal possède ensuite son propre résultat :

| Statut | Signification |
|---|---|
| `sent` | Le fournisseur a accepté l'envoi. |
| `failed` | Une tentative a eu lieu, mais a échoué. |
| `skipped` | Le canal n'était pas utilisable ou configuré. |

Le frontend doit confirmer que l'alerte est enregistrée même si un canal est `failed` ou `skipped`. Il ne doit pas afficher les détails techniques de `reason` à l'utilisateur. En staging, WhatsApp peut être `sent` alors que l'e-mail est `skipped` avec `smtp_not_configured`.

## 6. DiddiFiles : parcours obligatoire

Base actuelle : `https://diddifiles.diddifree.com`.

### Étape 1 - Créer une session

```http
POST /v1/files/upload-session
Authorization: Bearer <DiddiFreeID access_token>
Content-Type: application/json
```

Exemple :

```json
{
  "module_owner": "diddigo",
  "purpose": "diddigo_driver_kyc_license",
  "filename": "permis-recto.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 524288
}
```

Conserver `file_id`, `upload_url`, les en-têtes demandés et l'expiration retournée.

### Étape 2 - Envoyer directement le fichier

Faire un `PUT` vers `upload_url` avec exactement le `Content-Type` signé. Ne pas ajouter `Authorization: Bearer` à cette URL de stockage et ne jamais remplacer son hôte.

### Étape 3 - Confirmer

```http
POST /v1/files/{file_id}/confirm
Authorization: Bearer <DiddiFreeID access_token>
```

Envoyer le `file_id` à DiddiGo seulement après confirmation réussie.

### Étape 4 - Lire un fichier privé

```http
GET  /v1/files/{file_id}
POST /v1/files/{file_id}/download-url
```

Les documents KYC/KYV sont privés. Le frontend utilise l'URL temporaire retournée et ne fabrique jamais d'URL MinIO/S3.

### Étape 5 - Photo publique chauffeur

Le purpose `diddigo_driver_profile_photo` est public après confirmation. Son URL stable se résout avec :

```http
GET /v1/files/{file_id}/public-url
```

Ne pas confondre ce purpose avec `profile_avatar`, qui reste privé et générique.

## 7. Matrice DiddiGo vers DiddiFiles

### Purposes utilisables aujourd'hui

| Champ DiddiGo | Purpose DiddiFiles | Visibilité |
|---|---|---|
| `license_document_file_id` | `diddigo_driver_kyc_license` | privée |
| `national_id_document_file_id` | `diddigo_driver_kyc_national_id` | privée |
| `selfie_document_file_id` | `diddigo_driver_kyc_selfie` | privée |
| `profile_photo_file_id` | `diddigo_driver_profile_photo` | publique |
| `registration_document_file_id` | `diddigo_vehicle_registration` | privée |
| `vehicle_front_photo_file_id` | `diddigo_vehicle_front_photo` | privée |
| `vehicle_back_photo_file_id` | `diddigo_vehicle_back_photo` | privée |
| `vehicle_left_photo_file_id` | `diddigo_vehicle_left_photo` | privée |
| `vehicle_right_photo_file_id` | `diddigo_vehicle_right_photo` | privée |
| `vehicle_interior_photo_file_id` | `diddigo_vehicle_interior_photo` | privée |
| `vehicle_plate_photo_file_id` | `diddigo_vehicle_plate_photo` | privée |

### Purposes encore manquants ou ambigus

Les champs suivants existent dans DiddiGo, mais aucun purpose DiddiFiles dédié n'est actuellement publié :

- `license_back_document_file_id` ;
- `national_id_back_document_file_id` ;
- assurance et contrôle technique du véhicule ;
- autorisation de transport ;
- documents KYC partenaire ;
- preuve de propriété de flotte.

Ne pas inventer de chaîne `purpose` et ne pas détourner `generic_private_document` sans décision de contrat. Les écrans peuvent capturer et conserver temporairement l'état local, mais l'envoi final de ces pièces reste bloqué jusqu'à l'ajout des purposes correspondants dans DiddiFiles.

## 8. Erreurs DiddiFiles à traiter

| Code | Action frontend |
|---|---|
| `INVALID_PURPOSE` | Bloquer l'envoi et signaler une incompatibilité de contrat. |
| `INVALID_MIME_TYPE` | Demander un format accepté. |
| `FILE_TOO_LARGE` | Demander un fichier plus petit. |
| `FILE_NOT_FOUND` | Recréer une session si elle a expiré ou si l'objet manque. |
| `FILE_NOT_PUBLIC` | Utiliser `/download-url` pour un fichier privé. |
| `STORAGE_UNAVAILABLE` | Conserver le formulaire et proposer une nouvelle tentative plus tard. |

Le frontend ne valide jamais un KYC ou un KYV. DiddiFiles sécurise le fichier ; DiddiGo conserve le `file_id` et prend la décision métier.

## 9. Points en attente de correctif backend

- typer complètement les réponses `/start` et `/no-show` dans l'OpenAPI ;
- compléter les purposes DiddiFiles manquants avant d'activer les soumissions concernées.
