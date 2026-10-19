# DiddiGo - Brief frontend KYC/KYV

Date : 2026-10-19

## Changement principal

Le statut operationnel du chauffeur est maintenant distinct du statut KYC.
Utiliser `kyc.status` pour l'ecran dossier :

- `pending_verification` : dossier en cours de verification ;
- `approved` : dossier approuve ;
- `rejected` : au moins une piece doit etre corrigee.

Ne plus interpreter `driver.status=suspended` comme un refus KYC. Une
suspension est un blocage operationnel distinct qui doit orienter vers le support.

## Lecture du dossier

`GET /v1/drivers/me` est la source DiddiGo du profil chauffeur. La reponse est
maintenant typee dans OpenAPI. Le bloc `kyc.document_reviews` et le bloc
`vehicle.document_reviews` contiennent les decisions par piece.

Exemple :

```json
{
  "document_type": "national_id_back",
  "status": "rejected",
  "reason_code": "unreadable",
  "reason": "Le numero est masque par un reflet.",
  "expected_correction": "Reprendre la photo sans flash.",
  "reviewed_at": "2026-10-19T14:30:00Z"
}
```

Pour chaque piece rejetee, afficher le motif et `expected_correction`. Ne pas
demander au chauffeur de reprendre les pieces deja approuvees.

## Correction et resoumission

- Piece personnelle : `POST /v1/drivers/kyc/resubmit`.
- Piece vehicule : `POST /v1/drivers/vehicles/{vehicle_id}/kyv/resubmit`.
- Informations descriptives du vehicule : `PUT /v1/drivers/me/vehicle`.

Une resoumission remet uniquement les pieces envoyees a `pending`. Le dossier
global repasse a `pending_verification`, puis la projection `/pro/metiers` est
mise a jour de maniere asynchrone.

La carte grise se renvoie avec `registration_document_file_id`. Le `vehicle_id`
et les identifiants des six photos sont disponibles dans `GET /v1/drivers/me`.

## Pieces MVP

KYC obligatoire : permis recto/verso, CNI recto/verso et selfie.

KYV obligatoire : carte grise, assurance, controle technique et six photos
(avant, arriere, gauche, droite, interieur, plaque). L'autorisation de transport
est stockee mais n'est pas bloquante actuellement.

Les purposes DiddiFiles manquants restent un blocage d'integration. Ne pas
inventer de purpose cote application.

## Hors MVP

- controle serveur d'un age minimum de 21 ans ;
- promesse de traitement en 6 h ou 48 h ;
- affichage au chauffeur de l'identite de l'administrateur ayant decide.
