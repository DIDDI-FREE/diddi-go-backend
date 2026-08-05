# DiddiFiles - Brief de creation du service fichiers

## 1. Contexte

DiddiFree a besoin d'un service transversal pour stocker et servir les fichiers
de tout l'ecosysteme : photos, images, documents, justificatifs, preuves,
pieces KYC, contrats, medias et documents administratifs.

Le cahier des charges des 12 modules ne nomme pas explicitement un module
`DiddiFiles`, mais il contient plusieurs exigences documentaires et media :

- DiddiPay : KYC/AML, audit, conformite.
- DiddiFund : verification d'identite renforcee et pieces de campagne.
- DiddiGo : documents chauffeur, permis, vehicule, KYC transport.
- DiddiSend : photo du colis et preuve de livraison numerique.
- DiddiTransport : lettres de voiture, documents douane, preuves de livraison.
- DiddiShop : images produit et moderation de contenus.
- DiddiNet : photo/description de probleme pour intervention.
- DiddiLegal : documents juridiques, contrats, dossiers, horodatage, retention.
- DiddiHome : galeries photo, baux, quittances, etats des lieux horodates.

Conclusion : le stockage fichier doit etre un service commun, pas une
fonctionnalite cachee dans DiddiFreeID, DiddiGo ou chaque module.

## 2. Objectif du service

Créer un service separe, par exemple :

```text
diddi-files
```

ou :

```text
diddi-media
```

Recommandation : `diddi-files`, car le service doit couvrir autant les images
que les documents sensibles.

## 3. Responsabilites

DiddiFiles doit :

- recevoir les demandes d'upload;
- verifier les JWT DiddiFreeID localement via JWKS;
- generer des URLs temporaires d'upload;
- stocker les fichiers dans un stockage objet;
- enregistrer les metadonnees en base;
- fournir des URLs temporaires de lecture/telechargement;
- gerer les permissions par utilisateur, module et usage;
- journaliser les actions sensibles;
- garder les fichiers prives par defaut;
- permettre aux modules de stocker seulement un `file_id`.

DiddiFiles ne doit pas :

- stocker les fichiers dans PostgreSQL;
- stocker les fichiers dans le filesystem ephemere du conteneur applicatif;
- dependre de DiddiGo ou DiddiFreeID comme module metier;
- rendre les fichiers publics par defaut;
- servir des URLs permanentes pour les fichiers sensibles.

## 4. Architecture recommandee

Flux upload direct objet :

```text
1. Client mobile/web demande une session d'upload a DiddiFiles.
2. DiddiFiles verifie le JWT DiddiFreeID localement via JWKS.
3. DiddiFiles valide module_owner, purpose, type MIME, taille max.
4. DiddiFiles cree une ligne metadata status=pending.
5. DiddiFiles retourne une URL signee temporaire d'upload.
6. Le client envoie le fichier directement vers le stockage objet.
7. Le client appelle DiddiFiles pour confirmer l'upload.
8. DiddiFiles verifie l'objet et passe status=available.
9. Le module metier stocke uniquement le `file_id`.
```

Flux lecture :

```text
1. Client ou module demande un download-url.
2. DiddiFiles verifie droits d'acces.
3. DiddiFiles retourne une URL signee temporaire.
4. Le client telecharge directement depuis le stockage objet.
```

## 5. Stockage

MVP VPS :

```text
MinIO + volume Docker persistant
```

Alternatives cloud compatibles S3 :

```text
Cloudflare R2
AWS S3
Wasabi
Scaleway Object Storage
```

Le service doit utiliser une interface S3-compatible pour pouvoir migrer de
MinIO vers un cloud sans changer l'API.

## 6. Base de donnees

PostgreSQL separe pour les metadonnees.

Schema recommande :

```text
files.files
files.file_access_logs
files.file_events
```

Table minimale `files.files` :

```text
id UUID primary key
owner_user_id UUID nullable
module_owner varchar not null
purpose varchar not null
object_key text not null unique
original_filename text nullable
mime_type varchar not null
size_bytes bigint nullable
checksum_sha256 varchar nullable
visibility varchar not null default 'private'
status varchar not null default 'pending'
storage_provider varchar not null default 'minio'
bucket varchar not null
created_by_user_id UUID nullable
created_at timestamptz not null
updated_at timestamptz not null
confirmed_at timestamptz nullable
deleted_at timestamptz nullable
expires_at timestamptz nullable
metadata jsonb not null default '{}'
```

Statuts :

```text
pending
available
quarantined
deleted
expired
failed
```

Visibilites :

```text
private
module_private
public_read
temporary
```

Par defaut : `private`.

## 7. Authentification et autorisation

DiddiFiles consomme les JWT DiddiFreeID :

- verification locale RS256 avec JWKS;
- issuer obligatoire `diddifree-id`;
- `status=active` obligatoire pour upload utilisateur;
- `role=admin` pour operations admin.

Service-to-service :

- accepter `X-Service-Key` configure par environnement;
- ou accepter un token service `role=service` si DiddiFreeID le fournit;
- ne jamais exposer les endpoints service-to-service au frontend.

Regle de propriete :

- un utilisateur peut creer/lire ses fichiers selon les policies;
- un module peut lire les fichiers dont il est proprietaire;
- un admin peut auditer;
- un fichier sensible ne doit jamais etre public sans decision explicite.

## 8. API MVP

### Health

```http
GET /health
GET /ready
```

### Demander un upload

```http
POST /v1/files/upload-session
Authorization: Bearer <access_token>
```

Requete :

```json
{
  "module_owner": "diddigo",
  "purpose": "driver_kyc_license",
  "filename": "permis.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 524288,
  "checksum_sha256": "optional-client-checksum",
  "owner_user_id": "optional-user-id",
  "metadata": {
    "driver_profile_id": "optional"
  }
}
```

Reponse :

```json
{
  "file_id": "uuid",
  "status": "pending",
  "upload": {
    "method": "PUT",
    "url": "https://signed-upload-url",
    "expires_in_seconds": 900,
    "headers": {
      "Content-Type": "image/jpeg"
    }
  }
}
```

### Confirmer un upload

```http
POST /v1/files/{file_id}/confirm
Authorization: Bearer <access_token>
```

Reponse :

```json
{
  "file_id": "uuid",
  "status": "available"
}
```

### Lire les metadonnees

```http
GET /v1/files/{file_id}
Authorization: Bearer <access_token>
```

### Obtenir une URL temporaire de lecture

```http
POST /v1/files/{file_id}/download-url
Authorization: Bearer <access_token>
```

Reponse :

```json
{
  "file_id": "uuid",
  "download_url": "https://signed-download-url",
  "expires_in_seconds": 300
}
```

### Suppression logique

```http
DELETE /v1/files/{file_id}
Authorization: Bearer <access_token>
```

Reponse :

```json
{
  "file_id": "uuid",
  "status": "deleted"
}
```

## 9. Purposes MVP

Commencer avec une liste stricte :

```text
profile_avatar
diddigo_driver_kyc_license
diddigo_driver_kyc_national_id
diddigo_driver_kyc_selfie
diddigo_vehicle_registration
diddisend_package_photo
diddisend_delivery_proof
diddishop_product_image
diddifund_campaign_document
diddilegal_case_document
diddihome_property_photo
diddihome_contract_document
generic_private_document
```

Un `purpose` inconnu doit repondre `422 INVALID_PURPOSE`.

## 10. Limites et validation

MVP :

```text
Images avatar/produit/preuve: 5 MB max
Documents PDF: 20 MB max
KYC image/document: 10 MB max
Videos: non supportees en MVP
```

MIME autorises MVP :

```text
image/jpeg
image/png
image/webp
application/pdf
```

Le service doit verifier :

- extension coherente avec MIME;
- taille annoncee;
- taille reelle apres upload;
- checksum si fourni;
- objet present dans le bucket apres confirmation.

## 11. Securite

Obligatoire des le MVP :

- fichiers prives par defaut;
- URLs signees courtes;
- pas d'URL permanente pour documents sensibles;
- logs d'acces;
- rate limiting upload-session;
- noms d'objets non devinables;
- jamais de chemin fourni directement par le client;
- CORS strict pour les domaines frontend autorises;
- headers de securite sur telechargement.

A prevoir phase 2 :

- antivirus ClamAV ou service equivalent;
- statut `quarantined`;
- moderation des images publiques;
- watermark eventuel pour documents sensibles;
- retention par type de document;
- chiffrement objet cote serveur;
- lifecycle rules pour expiration.

## 12. Logs et audit

Chaque action sensible doit produire un log structure :

```text
file_upload_session_created
file_upload_confirmed
file_download_url_issued
file_deleted
file_access_denied
file_quarantined
```

Champs minimum :

```text
request_id
file_id
actor_user_id
actor_role
module_owner
purpose
client_ip
user_agent
status
created_at
```

## 13. Portainer / Docker

Le projet doit avoir :

```text
Dockerfile
docker-compose.yml
docker-compose.portainer.yml
.env.example
README.md
DEPLOYMENT.md
alembic migrations
```

Variables :

```env
APP_ENV=production
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db:5432/diddi_files
REDIS_URL=redis://redis:6379/0
IDENTITY_BASE_URL=https://auth.diddifree.com
IDENTITY_ISSUER=diddifree-id
S3_ENDPOINT=http://minio:9000
S3_BUCKET=diddi-files
S3_REGION=local
S3_ACCESS_KEY=<secret>
S3_SECRET_KEY=<secret>
S3_PUBLIC_BASE_URL=
SIGNED_UPLOAD_TTL_SECONDS=900
SIGNED_DOWNLOAD_TTL_SECONDS=300
MAX_UPLOAD_BYTES=20971520
CORS_ORIGINS=https://go.diddifree.com,https://auth.diddifree.com
```

Compose MVP :

- API DiddiFiles;
- PostgreSQL;
- Redis si rate limit/cache;
- MinIO;
- volume persistant MinIO;
- volume persistant PostgreSQL.

Ne pas exposer MinIO publiquement sans proxy/SSL et policies strictes.

## 14. Integration avec les modules

### DiddiFreeID

Stocker :

```text
photo_file_id
```

ou garder temporairement `photo_url`, mais la cible propre est `photo_file_id`.

### DiddiGo

Remplacer progressivement :

```text
license_document_url
national_id_document_url
selfie_document_url
```

par :

```text
license_document_file_id
national_id_document_file_id
selfie_document_file_id
```

Pendant la transition, DiddiGo peut accepter les URLs existantes pour ne pas
bloquer le front.

### DiddiSend

Utiliser DiddiFiles pour :

```text
package_photo_file_id
delivery_proof_file_id
signature_file_id
```

### DiddiShop

Utiliser DiddiFiles pour les images produit avec `visibility=public_read` apres
moderation ou validation explicite.

### DiddiLegal / DiddiHome

Utiliser des fichiers prives, retention longue, audit strict.

## 15. Definition of Done MVP

- Upload session creee et testee.
- Upload direct MinIO fonctionnel.
- Confirmation upload fonctionnelle.
- Download URL signee fonctionnelle.
- Metadata PostgreSQL persistantes.
- JWT DiddiFreeID verifie localement.
- Permissions owner/module implementees.
- Fichiers prives par defaut.
- Tests unitaires des policies.
- Tests integration MinIO.
- Compose local et Portainer fournis.
- README et DEPLOYMENT clairs.

## 16. Decisions produit

Recommandation ferme :

```text
DiddiFiles est un service transversal.
DiddiFreeID ne stocke pas les fichiers.
DiddiGo ne stocke pas les fichiers.
Les modules stockent uniquement des file_id.
Le stockage objet est la source physique.
PostgreSQL stocke uniquement les metadonnees.
```

Nom recommande :

```text
diddi-files
```

Nom alternatif :

```text
diddi-media
```

Je recommande `diddi-files`, car les documents juridiques, KYC et preuves de
livraison sont aussi importants que les images.
